# coding: utf-8
import re
import functools

from pymorphy2 import MorphAnalyzer

russian_token_regex = r'(?P<russian>[а-яё\-]+)'
latin_token_regex = r'(?P<latin>[a-z\-\']+)'
int_range_token_regexp = r'(?P<int_range>[+-]?[0-9]+\s*?\-\s*?[0-9]+)'
int_token_regex = r'(?P<int>[+-]?[0-9]+)'
float_range_token_regex = r'(?P<float_range>[+-]?[\d]+[\.\,][\d]+\s*?\-\s*?[\d]+[\.\,][\d]+)'
float_token_regex = r'(?P<float>[+-]?[\d]+[\.\,][\d]+)'
quote_token_regex = r'(?P<quote>[\"\'«»])'
punctuation_token_regex = r'(?P<punct>[\.\-—,;:]+)'
complete_token_regex = r'|'.join((
    float_range_token_regex,
    float_token_regex,
    int_range_token_regexp,
    int_token_regex,
    punctuation_token_regex,
    russian_token_regex,
    latin_token_regex,
    quote_token_regex,
))

token_regex = re.compile(complete_token_regex, re.UNICODE | re.IGNORECASE)

class Tokenizer(object):

    def __init__(self, cache_size):
        self.morph = MorphAnalyzer()
        self.cache = functools.lru_cache(maxsize=cache_size)(self.get_word_attributes)

    def get_word_attributes(self, word):
        attributes = {
            "grammemes": set(),
            "forms": set(),
        }
        for form in self.morph.parse(word):
            attributes["grammemes"] = attributes["grammemes"] | set(form.tag.grammemes)
            attributes["forms"] = attributes["forms"] | {form.normal_form}
        return attributes

    def transform(self, text):
        for match in re.finditer(token_regex, text):
            group = match.lastgroup
            value = match.group(0)
            position = match.span()
            if group == "russian":
                token = ("word", value, position, self.cache(value))
            elif group == "latin":
                token = ("word", value, position, {"grammemes": set(['LATN']), "forms": set()})
            elif group == "quote":
                token = ("quote", value, position, None)
            elif group == "float":
                token = ("float", float(value.replace(",", ".")), position, None)
            elif group == "int":
                token = ("int", int(value), position, None)
            elif group == "int_range":
                values = map(int, value.split("-"))
                token = ("range", range(*values), position, None)
            elif group == "float_range":
                values = map(float, value.split("-"))
                token = ("range", range(*values), position, None)
            elif group == "punct":
                token = ("punct", value, position, None)
            else:
                raise NotImplementedError
            yield token
