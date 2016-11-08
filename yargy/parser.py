# coding: utf-8
from __future__ import unicode_literals


from yargy.tokenizer import Token, Tokenizer
from yargy.labels import LABELS_LOOKUP_MAP


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

    def __init__(self, name, rules):
        self.name = name
        self.rules = rules
        self.rules.append({'terminal': True})
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

        :return: list with matched tokens or None if (at current step) stack doesn't contains matches
        :rtype: list or None
        '''
        rule = self.rules[self.index]

        repeatable = rule.get('repeatable', False)
        optional = rule.get('optional', False)
        terminal = rule.get('terminal', False)
        skip = rule.get('skip', False)

        if not all(self.match(token, rule)) and not terminal:
            if optional or (repeatable and self.stack.have_matches_by_rule_index(self.index)):
                self.index += 1
            else:
                self.reset()
            if not recheck:
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

    def reduce(self):
        '''
        Reduce method returns grammar stack if
        current grammar index equals to last (terminal) rule
        '''
        if self.rules[self.index] == self.rules[-1]:
            match = self.stack.flatten()
            self.reset()
            return match

    def reset(self):
        self.stack = Stack()
        self.index = 0

    def match(self, token, rule):
        labels = rule.get('labels', [])
        stack = self.stack.flatten()
        for (name, value) in labels:
            yield LABELS_LOOKUP_MAP[name](token, value, stack)

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
                self.grammars.append(Grammar(name, rule.value))
        self.parser = Parser(self.grammars, *args, **kwargs)

    def extract(self, text):
        for (rule, match) in self.parser.extract(text):
            yield self.classes[rule.name], match
