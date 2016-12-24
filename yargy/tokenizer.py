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

from pymorphy2 import MorphAnalyzer
from pymorphy2.shapes import is_roman_number

from yargy.utils import frange

russian_token_regex = r'(?P<russian>[а-яё][а-яё\-]*)'
latin_token_regex = r'(?P<latin>[a-z][a-z\-\']*)'
int_separated_token_regex = r'(?P<int_separated>[1-9]\d*(\s\d{3})+)'
int_range_token_regex = r'(?P<int_range>[+-]?\d+\s*?[\-\—]\s*?\d+)'
int_token_regex = r'(?P<int>[+-]?\d+)'
float_range_token_regex = r'(?P<float_range>[+-]?[\d]+[\.\,][\d]+\s*?[\-\—]\s*?[\d]+[\.\,][\d]+)'
float_token_regex = r'(?P<float>[+-]?[\d]+[\.\,][\d]+)'
quote_token_regex = r'(?P<quote>[\"\'\«\»\„\“])'
punctuation_token_regex = string.punctuation.join(['(?P<punct>[', r']+)'])
email_token_regex = r'(?P<email>[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)'
phone_number_token_regex = r'(?P<phone>(\+)?([-\s_()]?\d[-\s_()]?){10,14})' # found at https://toster.ru/answer?answer_id=852265#answers_list_answer
complete_token_regex = r'|'.join((
    phone_number_token_regex,
    email_token_regex,
    float_range_token_regex,
    float_token_regex,
    int_separated_token_regex,
    int_range_token_regex,
    int_token_regex,
    russian_token_regex,
    latin_token_regex,
    quote_token_regex,
    punctuation_token_regex,
))

token_regex = re.compile(complete_token_regex, re.UNICODE | re.IGNORECASE)

class Token(object):

    __slots__ = (
        'value',
        'position',
        'forms',
    )

    def __init__(self, value, position, forms):
        self.value = value
        self.position = position
        self.forms = forms

    def __eq__(self, other):
        if not isinstance(other, Token):
            return False
        else:
            return (
                (self.value == other.value) &
                (self.position == other.position) &
                (self.forms == other.forms)
            )

    def __repr__(self):
        return '{0.__class__.__name__}({0.value!r}, {0.position!r}, {0.forms!r})'.format(self)

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
            transform_method = getattr(self, 'transform_{}'.format(group), None)
            if transform_method:
                yield transform_method(value, position)
            else:
                raise NotImplementedError('Unknown token type: {}'.format(group))

    def transform_russian(self, value, position):
        '''
        Transforms russian word into token
        :returns: Token with word morphology info
        :rtype: Token instance
        '''
        return Token(value, position, self.cache(value))

    def transform_latin(self, value, position):
        '''
        Transforms latin word into token, note that no morph info is added to token
        :returns: Token with 'LATN' or 'ROMN' grammeme
        :rtype: Token instance
        '''
        grammemes = {
            'LATN',
        }
        normal_form = value.lower()
        is_number = is_roman_number(value)
        if is_number:
            grammemes = {
                'ROMN',
            }
            normal_form = value
        return Token(value, position, [
            {
                'grammemes': grammemes,
                'normal_form': normal_form,
            }
        ])

    def transform_quote(self, value, position):
        '''
        Transforms different types of quotes to tokens, sets different grammemes
        to its, based on type of quote (e.g. '«' - gets L-QUOTE grammeme)
        :returns: Token with 'QUOTE' grammeme and (optional) L/R-QUOTE grammeme
        '''
        grammemes = {'QUOTE', }
        if value in {'«', '„'}:
            grammemes |= {'L-QUOTE'}
        elif value in {'»', '“'}:
            grammemes |= {'R-QUOTE'}
        return Token(value, position, [
            {
                'grammemes': grammemes,
                'normal_form': value
            }
        ])

    def transform_int(self, value, position):
        '''
        Transforms integer to token
        :returns: Token with 'NUMBER' and 'INT' grammemes
        :rtype: Token instance
        '''
        return Token(int(value), position, [
            {'grammemes': {'NUMBER', 'INT'}, 'normal_form': value}
        ])

    def transform_int_range(self, value, position):
        '''
        Transforms integer range (two numbers separated by dash or minus) to token with 'RANGE' grammeme
        :returns: Token with 'RANGE' and 'INT-RANGE' grammemes
        :rtype: Token instance
        '''
        if value[0] == '-':
            value = value[1:]
        values = map(int, re.split(r'[\-\—]', value))
        return Token(range(*values), position, [
            {'grammemes': {'RANGE', 'INT-RANGE'}, 'normal_form': value}
        ])

    def transform_int_separated(self, value, position):
        '''
        Transforms integer separated by spaces (like 1 000 000) to token with 'INT' grammeme
        :returns: Token with 'NUMBER' and 'INT' gramemes
        :rtype: Token instance
        '''
        value = int(re.sub('\s', '', value))
        return Token(value, position, [
            {'grammemes': {'NUMBER', 'INT', 'INT-SEPARATED'}, 'normal_form': value}
        ])

    def transform_float(self, value, position):
        '''
        Transforms float (with '.' or ',' as delimiter) to token with 'FLOAT' grammeme
        :returns: Token with 'NUMBER' and 'FLOAT' grammeme
        :rtype: Token instance
        '''
        value = float(value.replace(',', '.'))
        return Token(value, position, [
            {'grammemes': {'NUMBER', 'FLOAT'}, 'normal_form': value}
        ])

    def transform_float_range(self, value, position):
        '''
        Transforms floats separated by dash or minus to token with special type - float range
        Because python built-in `range` type doesnt supports float ranges we use custom type
        for that purposes, which can be found at `yargy.utils.frange` function
        :returns: Token with 'RANGE' and 'FLOAT-RANGE' gremmemes
        :rtype: Token instance
        '''
        values = map(float, (x.replace(',', '.') for x in re.split(r'[\-\—]', value)))
        range_value = frange(*values, step=self.frange_step)
        return Token(range_value, position, [
            {
                'grammemes': {'RANGE', 'FLOAT-RANGE'},
                'normal_form': value,
            },
        ])

    def transform_punct(self, value, position):
        '''
        Transforms punctuation characters to token with 'PUNCT' grammeme
        :returns: Token with 'PUNCT' grammeme
        :rtype: Token instance
        '''
        return Token(value, position, [
            {
                'grammemes': {'PUNCT', },
                'normal_form': value
            }
        ])

    def transform_email(self, value, position):
        '''
        Transforms email address to token with 'EMAIL' grammeme
        :returns: Token with 'EMAIL' grammeme
        :rtype: Token instance
        '''
        return Token(value, position, [
            {
                'grammemes': {'EMAIL', },
                'normal_form': value,
            }
        ])

    def transform_phone(self, value, position):
        '''
        Transforms phone number to token with 'PHONE' gremmeme
        :returns: Token with 'PHONE' grammeme
        :rtype: Token instance
        '''
        value = value.strip()
        return Token(value, position,
            {
                'grammemes': {'PHONE', },
                'normal_form': value,
            }
        )
