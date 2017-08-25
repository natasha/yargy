# coding: utf-8
from __future__ import unicode_literals

from .compat import str
from .utils import Record
from .morph import Form


class Token(Record):
    __attributes__ = ['value', 'span', 'forms']

    def __init__(self, value, span, forms):
        self.value = value
        self.span = span
        self.forms = forms

    def replace(self, forms=None):
        if forms is None:
            forms = self.forms
        return Token(self.value, self.span, forms)


def format_tokens(tokens):
    previous = None
    for token in tokens:
        if previous:
            _, stop = previous.span
            start, _ = token.span
            if start - stop > 0:
                yield ' '
        previous = token
        yield str(token.value)


def join_tokens(tokens):
    return ''.join(format_tokens(tokens))


def get_tokens_span(tokens):
    head, tail = tokens[0], tokens[-1]
    return head.span[0], tail.span[1]


class Multitoken(Token):
    def __init__(self, tokens, grammemes, normalized=None):
        self.tokens = tokens
        value = join_tokens(tokens)
        span = get_tokens_span(tokens)
        forms = list(self.forms(tokens, normalized, grammemes))
        super(Multitoken, self).__init__(value, span, forms)

    @staticmethod
    def forms(tokens, normalized, grammemes):
        if len(tokens) == 1:
            token = tokens[0]
            if normalized is None:
                for form in token.forms:
                    yield Form(form.normalized, form.grammemes | grammemes)
            else:
                forms = [
                    _ for _ in token.forms
                    if _.normalized == normalized
                ]
                if forms:
                    for form in forms:
                        yield Form(normalized, form.grammemes | grammemes)
                else:
                    yield Form(normalized, grammemes)
        else:
            yield Form(normalized, grammemes)


class NormalizedToken(Token):
    __attributes__ = ['normalizer', 'token']

    def __init__(self, normalizer, token):
        self.normalizer = normalizer
        self.token = token

    @property
    def value(self):
        return self.normalizer(self.token)

    @property
    def span(self):
        return self.token.span

    @property
    def forms(self):
        return self.token.forms
