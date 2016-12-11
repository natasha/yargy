# coding: utf-8
from __future__ import unicode_literals

try:
    from functools import lru_cache
except ImportError:
    from backports.functools_lru_cache import lru_cache

try:
    range = xrange
except NameError:
    range = range

import re
import string
import collections

from yargy.utils import frange
from pymorphy2 import MorphAnalyzer

russian_token_regex = r'(?P<russian>[а-яё][а-яё\-]*)'
latin_token_regex = r'(?P<latin>[a-z][a-z\-\']*)'
int_separated_token_regexp = r'(?P<int_separated>[1-9]\d*(\s\d{3})+)'
int_range_token_regexp = r'(?P<int_range>[+-]?\d+\s*?[\-\—]\s*?\d+)'
int_token_regex = r'(?P<int>[+-]?\d+)'
float_range_token_regex = r'(?P<float_range>[+-]?[\d]+[\.\,][\d]+\s*?[\-\—]\s*?[\d]+[\.\,][\d]+)'
float_token_regex = r'(?P<float>[+-]?[\d]+[\.\,][\d]+)'
quote_token_regex = r'(?P<quote>[\"\'\«\»])'
punctuation_token_regex = string.punctuation.join(['(?P<punct>[', r']+)'])
complete_token_regex = r'|'.join((
    float_range_token_regex,
    float_token_regex,
    int_separated_token_regexp,
    int_range_token_regexp,
    int_token_regex,
    russian_token_regex,
    latin_token_regex,
    quote_token_regex,
    punctuation_token_regex,
))

token_regex = re.compile(complete_token_regex, re.UNICODE | re.IGNORECASE)

Token = collections.namedtuple('Token', ['value', 'position', 'forms'])

class Tokenizer(object):

    def __init__(self, pattern=token_regex, morph_analyzer=None, cache_size=0, frange_step=0.1):
        self.pattern = pattern
        self.morph = morph_analyzer or MorphAnalyzer()
        self.cache = lru_cache(maxsize=cache_size)(self.get_word_forms)
        self.frange_step = frange_step

    def get_word_forms(self, word):
        forms = []
        for form in self.morph.parse(word):
            token = {}
            token['grammemes'] = set(form.tag.grammemes)
            token['normal_form'] = form.normal_form
            forms.append(token)
        return forms

    def transform(self, text):
        for match in re.finditer(self.pattern, text):
            group = match.lastgroup
            value = match.group(0)
            position = match.span()
            if group == 'russian':
                yield Token(value, position, self.cache(value))
            elif group == 'latin':
                yield Token(value, position, [
                    {
                        'grammemes': {'LATN'},
                        'normal_form': value.lower(),
                    }
                ])
            elif group == 'quote':
                grammemes = {'QUOTE', }
                if value in {'«', }:
                    grammemes |= {'L-QUOTE'}
                elif value in {'»', }:
                    grammemes |= {'R-QUOTE'}
                yield Token(value, position, [
                    {
                        'grammemes': grammemes,
                        'normal_form': value
                    }
                ])
            elif group == 'float':
                yield Token(float(value.replace(',', '.')), position, [
                    {'grammemes': {'NUMBER', 'FLOAT'}, 'normal_form': value}
                ])
            elif group == 'int':
                yield Token(int(value), position, [
                    {'grammemes': {'NUMBER', 'INT'}, 'normal_form': value}
                ])
            elif group == 'int_range':
                if value[0] == '-':
                    value = value[1:]
                values = map(int, re.split(r'[\-\—]', value))
                yield Token(range(*values), position, [
                    {'grammemes': {'RANGE', 'INT-RANGE'}, 'normal_form': value}
                ])
            elif group == 'float_range':
                values = map(float, (x.replace(',', '.') for x in re.split(r'[\-\—]', value)))
                yield Token(frange(*values, step=self.frange_step), position, [
                    {'grammemes': {'RANGE', 'FLOAT-RANGE'}, 'normal_form': value}
                ])
            elif group == 'punct':
                yield Token(value, position, [
                    {
                        'grammemes': {'PUNCT', },
                        'normal_form': value
                    }
                ])
            elif group == 'int_separated':
                value = int(re.sub('\s', '', value))
                yield Token(value, position, [
                    {'grammemes': {'NUMBER', 'INT-SEPARATED'}, 'normal_form': value}
                ])
            else:
                raise NotImplementedError(group)
