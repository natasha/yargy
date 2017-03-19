# coding: utf-8
from __future__ import unicode_literals

from copy import deepcopy, copy
from threading import Lock
from intervaltree import IntervalTree

from yargy.tokenizer import Token, Tokenizer
from yargy.pipeline import PipelineStatus
from yargy.normalization import NormalizationType
from yargy.utils import get_tokens_position


def create_or_copy_grammar(grammar, name=None):
    if isinstance(grammar, list):
        grammar = Grammar(name, deepcopy(grammar))
    elif isinstance(grammar, (Operation, Grammar)):
        grammar = deepcopy(grammar)
    else:
        raise ValueError('Not supported grammar type: {}'.format(grammar))
    return grammar


def build_grammars_from_multiple_classes(classes):
    for _class in classes:
        _class_name = _class.__name__
        for rule in _class.__members__.values():
            name = '{0}__{1}'.format(_class_name, rule.name)
            yield rule, name, create_or_copy_grammar(rule.value, name)


class Stack(list):

    '''
    Special list for grammar, which holds matches with rule index
    (by which token was captured)
    '''

    def have_matches_by_rule_index(self, rule_index):
        '''
        Checks that stack contains matches by rule index
        '''
        return any(
            (rule == rule_index for (rule, _) in reversed(self))
        )

    def flatten(self):
        '''
        Returns matched tokens without rule indexes
        '''
        return [value for (_, value) in self]


class Operation(object):

    def __init__(self, *grammars):
        self.grammars = [
            create_or_copy_grammar(grammar) 
            for grammar in grammars
        ]

    def reset(self):
        for grammar in self.grammars:
            if grammar.stack:
                grammar.reset()

    def shift(self, token):
        for grammar in self.grammars:
            grammar.shift(token)

    def reduce(self, end_of_stream=False):
        for grammar in self.grammars:
            if grammar.stack:
                match = grammar.reduce(end_of_stream=end_of_stream)
                if match:
                    self.reset()
                    return match

    @property
    def stack(self):
        return any(
            grammar.stack for grammar in self.grammars
        )


class OR(Operation):

    pass


class Grammar(object):

    '''
    Grammar contains stack and list of rules.
    When GLR-parser iterates over tokens it calls
    `shift` & `reduce` methods on each grammar which checks
    current grammar stack & provided token on current rule
    when stack contents matches all rules - grammar returns stack,
    which contains actual text match
    '''

    def __init__(self, name, rules):
        self.name = name
        self.rules = rules + [
            {
                'terminal': True,
            },
        ]
        self.reset()

    def shift(self, token, recheck=False):
        '''
        Parser <- [grammar_1, grammar_2]
                   |
                   V
                shift(token_1)
        Grammar_1 -> []
        Grammar_2 -> [token_1]
                   |
                   V
                shift(token_2)
        Grammar_1 -> []
        Grammar_2 -> [token_1, token_2]
                   |
                   V
                reduce()
        Grammar_1 -> []
        Grammar_2 -> [] <-> returns stack [token_1, token_2]
        '''
        rule = self.rules[self.index]

        # need to clone tokens, because labels can modify
        # its forms or other attributes
        token = copy(token)

        if isinstance(rule, (Operation, Grammar)):
            rule.shift(token)
            if not rule.stack:
                rule.reset()
                self.reset()
        else:
            repeatable = rule.get('repeatable', False)
            optional = rule.get('optional', False)
            terminal = rule.get('terminal', False)
            skip = rule.get('skip', False)

            if not all(self.match(token, rule)) and not terminal:
                last_index = self.index
                recheck = False
                if optional or (repeatable and self.stack.have_matches_by_rule_index(self.index)):
                    self.index += 1
                else:
                    recheck = True
                    self.reset()
                if (self.index != last_index) and (not recheck or (optional or repeatable)):
                    # recheck current token on next rule
                    self.shift(token, recheck=recheck)
                else:
                    self.reset()
            else:
                # token matches current rule
                if not terminal:
                    # append token to stack if it's not a terminal rule and current rule
                    # doesn't have 'skip' option
                    if not skip:
                        # add additional fields to tokens, like normalization
                        # and interpretation rules
                        token.normalization_type = rule.get(
                            'normalization', NormalizationType.Normalized)
                        token.interpretation = rule.get('interpretation', None)
                        # finally append match to stack
                        self.stack.append((self.index, token))
                    if not repeatable:
                        self.index += 1

    def reduce(self, end_of_stream=False):
        '''
        Reduce method returns grammar stack if
        current grammar index equals to last (terminal) rule
        '''
        current_rule = self.rules[self.index]
        terminal_rule = self.rules[-1]

        is_grammar_object = isinstance(current_rule, (Operation, Grammar))

        if is_grammar_object:
            match = current_rule.reduce(end_of_stream=end_of_stream)
            if match:
                self.index += 1
                for token in match.flatten():
                    self.stack.append((self.index, token))

        if (current_rule == terminal_rule) and self.stack:
            match = self.stack
            self.reset()
            return match

        if end_of_stream and not is_grammar_object:
            is_repeatable_and_have_matches = (
                current_rule.get('repeatable', False)
                and
                self.stack.have_matches_by_rule_index(self.index)
            )
            is_optional = current_rule.get('optional', False)
            next_rule_is_terminal = (
                self.rules[self.index + 1] == terminal_rule)
            if (is_repeatable_and_have_matches or is_optional) and next_rule_is_terminal:
                match = self.stack
                self.reset()
                return match

    def reset(self):
        self.stack = Stack()
        self.index = 0

    def match(self, token, rule):
        stack = self.stack.flatten()
        for label in rule.get('labels', []):
            yield label(token, stack)

    def __copy__(self):
        return Grammar(self.name, self.rules[:-1])

    def __repr__(self):
        return 'Grammar(name=\'{name}\', stack={stack})'.format(
            name=self.name,
            stack=self.stack,
        )


class Parser(object):

    '''
    Yet another GLR-parser.
    '''

    def __init__(self, grammars, tokenizer=None, pipelines=None, cache_size=0):
        self.grammars = grammars
        self.tokenizer = tokenizer or Tokenizer(cache_size=cache_size)
        self.pipelines = pipelines or []
        self.lock = Lock()

    def extract(self, text, return_flatten_stack=True):
        with self.lock:
            stream = self.tokenizer.transform(text)
            
            for pipeline in self.pipelines:
                stream = pipeline(stream)

            for token in stream:
                for grammar in self.grammars:
                    grammar.shift(token)
                    match = grammar.reduce()
                    if match:
                        if return_flatten_stack:
                            match = match.flatten()
                        yield (grammar, match)
            for grammar in self.grammars:
                match = grammar.reduce(end_of_stream=True)
                if match:
                    if return_flatten_stack:
                        match = match.flatten()
                    yield (grammar, match)
                grammar.reset()


class Combinator(object):

    '''
    Combinator merges multiple grammars (in multiple enums) into one parser
    '''

    def __init__(self, classes, *args, **kwargs):
        self.classes = {}
        self.grammars = []
        for rule, name, grammar in build_grammars_from_multiple_classes(classes):
            self.classes[name] = rule
            self.grammars.append(grammar)
        self.parser = Parser(self.grammars, *args, **kwargs)

    def extract(self, text):
        for (rule, match) in self.parser.extract(text):
            yield self.classes[rule.name], match

    def resolve_matches(self, matches, strict=True):
        # sort matches by tokens count in decreasing order
        matches = sorted(matches, key=lambda m: len(m[1]), reverse=True)
        tree = IntervalTree()
        for (grammar, match) in matches:
            start, stop = get_tokens_position(match)
            exists = tree[start:stop]
            if exists and not strict:
                for interval in exists:
                    exists_grammar, _ = interval.data
                    exists_contains_current_grammar = (
                        interval.begin < start and interval.end > stop)
                    exists_grammar_with_same_type = isinstance(
                        exists_grammar, grammar.__class__)
                    if not exists_grammar_with_same_type and exists_contains_current_grammar:
                        exists = False
            if not exists:
                tree[start:stop] = (grammar, match)
                yield (grammar, match)
