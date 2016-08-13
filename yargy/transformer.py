# coding: utf-8
import re
import functools

from pymorphy2 import MorphAnalyzer

russian_token_regex = r'(?P<russian>[а-яё\-]+)'
latin_token_regex = r'(?P<latin>[a-z\-\']+)'
int_token_regex = r'(?P<int>[+-]?[0-9]+)'
float_token_regex = r'(?P<float>[+-]?[\d]+\.[\d]+)'
quote_token_regex = r'(?P<quote>[\"\'«»])'
complete_token_regex = r'|'.join((
    float_token_regex,
    int_token_regex,
    russian_token_regex,
    latin_token_regex,
    quote_token_regex,
))

token_regex = re.compile(complete_token_regex, re.UNICODE | re.IGNORECASE)

class TokenTransformer(object):

    def __init__(self):
        self.morph = MorphAnalyzer()

    @functools.lru_cache(maxsize=50000)
    def get_word_options(self, word):
        options = {
            "grammemes": set(),
            "forms": set(),
        }
        for form in self.morph.parse(word):
            options["grammemes"] = options["grammemes"] | set(form.tag.grammemes)
            options["forms"] = options["forms"] | {form.normal_form}
        return options

    def transform(self, text):
        for match in re.finditer(token_regex, text):
            group = match.lastgroup
            value = match.group(0)
            position = match.span()
            if group == "russian":
                token = ("word", value, position, self.get_word_options(value))
            elif group == "latin":
                token = ("word", value, position, {"grammemes": set(), "forms": set()})
            elif group == "quote":
                token = ("quote", value, position, None)
            elif group == "float":
                token = ("float", float(value), position, None)
            elif group == "int":
                token = ("int", int(value), position, None)
            else:
                raise NotImplementedError
            yield token

TEXT_TRANSFORMER = TokenTransformer()
