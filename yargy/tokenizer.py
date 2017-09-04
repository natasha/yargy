# coding: utf-8
from __future__ import unicode_literals

import re

from .utils import Record, assert_type
from .compat import string_type
from .token import Token
from .morph import Form, MORPH


class TokenRule(Record):
    __attributes__ = ['pattern', 'grammemes']

    pattern = None
    grammemes = set()

    def construct(self, value):
        return value

    def normalize(self, value):
        return value

    def forms(self, value):
        yield Form(self.normalize(value), self.grammemes)

    def __call__(self, value, span):
        value = self.construct(value)
        forms = list(self.forms(value))
        return Token(value, span, forms)


class RussianRule(TokenRule):
    # TODO Why does it differ from LatinRule pattern?
    pattern = r'[а-яё]+'

    def __init__(self, morph=MORPH):
        self.morph = morph

    def forms(self, value):
        return self.morph.parse(value)


class LatinRule(TokenRule):
    pattern = r'[a-z]+'
    grammemes = {'LATN'}

    def normalize(self, value):
        return value.lower()


class StrInt(int):
    def __init__(self, string):
        assert_type(string, string_type)
        int.__init__(int(string))  # int(..) for pypy
        self.raw = string

    def __str__(self):
        return self.raw

    def __repr__(self):
        return self.raw


class IntRule(TokenRule):
    pattern = r'\d+'
    construct = StrInt
    grammemes = {'NUMBER', 'INT'}


class QuoteRule(TokenRule):
    # TODO Are ʼʻ” generic? Need to include ˈ and ´
    pattern = r'["\'«»„“ʼʻ”]'

    def forms(self, value):
        grammemes = {'QUOTE', }
        if value in {'«', '„'}:
            grammemes |= {'L-QUOTE'}  # left quote
        elif value in {'»', '“'}:
            grammemes |= {'R-QUOTE'}  # right quote
        else:
            grammemes |= {'G-QUOTE'}  # generic quote like <">

        yield Form(value, grammemes)


class PunctuationRule(TokenRule):
    pattern = r'[-\\/!#$%&()\[\]\*\+,\.:;<=>?@^_`{|}~№…]'
    grammemes = {'PUNCT'}


class EOLRule(TokenRule):
    pattern = r'[\n\r]+'
    grammemes = {'END-OF-LINE'}

    def normalize(self, value):
        return '\n'


class OtherRule(TokenRule):
    pattern = r'\S'
    grammemes = {'OTHER'}


class EmailRule(TokenRule):
    pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    grammemes = {'EMAIL'}


class PhoneRule(TokenRule):
    # found at https://toster.ru/answer?answer_id=852265#answers_list_answer
    pattern = r'(\+)?([-\s_()]?\d[-\s_()]?){10,14}'
    grammemes = {'PHONE'}


DEFAULT_RULES = [
    RussianRule(),
    LatinRule(),
    IntRule(),
    QuoteRule(),
    PunctuationRule(),
    EOLRule(),
    OtherRule(),
    # EmailRule(),
    # PhoneRule()
]


class Tokenizer(object):
    def __init__(self, rules=DEFAULT_RULES):
        for rule in rules:
            assert_type(rule, TokenRule)
        self.rules = rules
        self.regexp, self.mapping = self.compile(rules)

    def add_rules(self, *rules):
        self.__init__(self.rules + rules)

    def compile(self, rules):
        mapping = {}
        patterns = []
        for rule in rules:
            name = 'rule_{id}'.format(id=id(rule))
            pattern = r'(?P<{name}>{pattern})'.format(
                name=name,
                pattern=rule.pattern
            )
            mapping[name] = rule
            patterns.append(pattern)

        pattern = '|'.join(patterns)
        regexp = re.compile(pattern, re.UNICODE | re.IGNORECASE)
        return regexp, mapping

    def __call__(self, text):
        for match in re.finditer(self.regexp, text):
            name = match.lastgroup
            value = match.group(0)
            span = match.span()
            rule = self.mapping[name]
            token = rule(value, span)
            yield token
