# coding: utf-8
from __future__ import unicode_literals
from copy import copy

from yargy.tokenizer import Token, Tokenizer


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

class Grammar(object):

    '''
    Grammar contains stack and list of rules.
    When GLR-parser iterates over tokens it calls
    `shift` & `reduce` methods on each grammar which checks
    current grammar stack & provided token on current rule
    when stack contents matches all rules - grammar returns stack,
    which contains actual text match
    '''

    def __init__(self, name, rules, changes_token_structure=False):
        self.name = name
        self.rules = rules + [
            {
                'terminal': True,
            },
        ]
        self.changes_token_structure = changes_token_structure
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

        repeatable = rule.get('repeatable', False)
        optional = rule.get('optional', False)
        terminal = rule.get('terminal', False)
        skip = rule.get('skip', False)

        if self.changes_token_structure:
            # need to clone tokens, because labels modifies
            # its forms or other attributes
            token = copy(token)

        if not all(self.match(token, rule)) and not terminal:
            last_index = self.index
            if optional or (repeatable and self.stack.have_matches_by_rule_index(self.index)):
                self.index += 1
            else:
                self.reset()
            if not recheck and (self.index != last_index):
                self.shift(token, recheck=True) # recheck current token on next rule
        else:
            # token matches current rule
            if not terminal:
                # append token to stack if it's not a terminal rule and current rule
                # doesn't have 'skip' option
                if not skip:
                    self.stack.append((self.index, token))
                if not repeatable:
                    if len(self.rules) >= (self.index + 1):
                        self.index += 1

    def reduce(self, end_of_stream=False):
        '''
        Reduce method returns grammar stack if
        current grammar index equals to last (terminal) rule
        '''
        if not self.stack:
            return None

        current_rule = self.rules[self.index]
        terminal_rule = self.rules[-1]

        if current_rule == terminal_rule:
            match = self.stack.flatten()
            self.reset()
            return match

        if end_of_stream:
            is_repeatable_and_have_matches = (
                current_rule.get('repeatable', False)
                and
                self.stack.have_matches_by_rule_index(self.index)
            )
            is_optional = current_rule.get('optional', False)
            next_rule_is_terminal = (self.rules[self.index + 1] == terminal_rule)
            if (is_repeatable_and_have_matches or is_optional) and next_rule_is_terminal:
                match = self.stack.flatten()
                self.reset()
                return match


    def reset(self):
        self.stack = Stack()
        self.index = 0

    def match(self, token, rule):
        stack = self.stack.flatten()
        for label in rule.get('labels', []):
            yield label(token, stack)

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

    def extract(self, text):
        stream = self.tokenizer.transform(text)
        for pipeline in self.pipelines:
            stream = pipeline(stream)
        for token in stream:
            for grammar in self.grammars:
                grammar.shift(token)
                match = grammar.reduce()
                if match:
                    yield (grammar, match)
        for grammar in self.grammars:
            match = grammar.reduce(end_of_stream=True)
            if match:
                yield (grammar, match)

class Combinator(object):

    '''
    Combinator merges multiple grammars (in multiple enums) into one parser
    '''

    def __init__(self, classes, *args, **kwargs):
        self.classes = {}
        self.grammars = []
        for _class in classes:
            _class_name = _class.__name__
            for rule in _class.__members__.values():
                name = "{0}__{1}".format(_class_name, rule.name)
                self.classes[name] = rule
                if not isinstance(rule.value, Grammar):
                    grammar = Grammar(name, rule.value)
                else:
                    grammar = rule.value
                self.grammars.append(grammar)
        self.parser = Parser(self.grammars, *args, **kwargs)

    def extract(self, text):
        for (rule, match) in self.parser.extract(text):
            yield self.classes[rule.name], match

    def resolve_matches(self, matches):
        matches = sorted(matches, key=lambda m: len(m[1]), reverse=True)
        index = {}
        for match in matches:
            tokens = match[-1]
            head, tail = tokens[0], tokens[-1]
            x, y = head.position[0], tail.position[1]
            length = 0 + (y - x)
            for (m_x, m_y, m_len) in index.keys():
                if (x >= m_x and y <= m_y):
                    if (m_len > length):
                        break
            else:
                index[(x, y, length)] = match
        return index.values()
