# coding: utf-8
import re
import enum
import string
import datetime
import functools
import collections

from yargy.utils import frange
from pymorphy2 import MorphAnalyzer

russian_token_regex = r'(?P<russian>[а-яё][а-яё\-]*)'
latin_token_regex = r'(?P<latin>[a-z][a-z\-\']*)'
time_token_regex = r'(?P<time>\d{2}:\d{2})'
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
    time_token_regex,
    int_separated_token_regexp,
    int_range_token_regexp,
    int_token_regex,
    russian_token_regex,
    latin_token_regex,
    quote_token_regex,
    punctuation_token_regex,
))

token_regex = re.compile(complete_token_regex, re.UNICODE | re.IGNORECASE)

class Token(enum.Enum):
    Word = 0
    Number = 1
    Range = 2
    Punct = 3
    Quote = 4
    Datetime = 5

    Term = 6

TokenClass = collections.namedtuple('Token', ['type', 'value', 'position', 'forms'])

class Tokenizer(object):

    def __init__(self, pattern=token_regex, morph_analyzer=None, cache_size=0, frange_step=0.1):
        self.pattern = pattern
        self.morph = morph_analyzer or MorphAnalyzer()
        self.cache = functools.lru_cache(maxsize=cache_size)(self.get_word_forms)
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
                yield TokenClass(Token.Word, value, position, self.cache(value))
            elif group == 'latin':
                yield TokenClass(Token.Word, value, position, [{'grammemes': {'LATN'}, 'normal_form': value.lower()}])
            elif group == 'quote':
                yield TokenClass(Token.Quote, value, position, None)
            elif group == 'float':
                yield TokenClass(Token.Number, float(value.replace(',', '.')), position, None)
            elif group == 'int':
                yield TokenClass(Token.Number, int(value), position, None)
            elif group == 'int_range':
                if value[0] == '-':
                    value = value[1:]
                values = map(int, re.split(r'[\-\—]', value))
                yield TokenClass(Token.Range, range(*values), position, None)
            elif group == 'float_range':
                values = map(float, re.split(r'[\-\—]', value))
                yield TokenClass(Token.Range, frange(*values, step=self.frange_step), position, None)
            elif group == 'punct':
                yield TokenClass(Token.Punct, value, position, None)
            elif group == 'int_separated':
                value = int(re.sub('\s', '', value))
                yield TokenClass(Token.Number, value, position, None)
            elif group == 'time':
                hours, minutes = map(int, value.split(':'))
                if 0 <= hours <= 23 and 0 <= minutes <= 59:
                    yield TokenClass(Token.Datetime, datetime.time(hours, minutes), position, None)
                else:
                    index = value.index(':')
                    start = (position[0], position[0] + index)
                    middle = (position[0] + index, position[0] + index + 1)
                    finish = (position[1] - index, position[1])
                    yield TokenClass(Token.Number, hours, start, None)
                    yield TokenClass(Token.Punct, ':', middle, None)
                    yield TokenClass(Token.Number, minutes, finish, None)
            else:
                raise NotImplementedError
