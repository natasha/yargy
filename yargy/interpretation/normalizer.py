# coding: utf-8
from __future__ import unicode_literals

from yargy.utils import Record


class Normalizer(Record):
    def __call__(self, token):
        raise NotImplementedError


class NormalFormNormalizer(Normalizer):
    def __call__(self, token):
        form = token.forms[0]
        return form.normalized


class InflectNormalizer(Normalizer):
    __attributes__ = ['grammemes']

    def __init__(self, grammemes=None):
        self.grammemes = grammemes

    def __call__(self, token):
        form = token.forms[0]
        try:
            return form.inflect(self.grammemes)
        except ValueError:
            return form.normalized


class ValueNormalizer(Record):
    def __call__(self, Value):
        raise NotImplementedError


class ConstNormalizer(ValueNormalizer):
    __attributes__ = ['value']

    def __init__(self, value):
        self.value = value

    def __call__(self, _):
        return self.value


class FunctionNormalizer(ValueNormalizer):
    __attributes__ = ['function']

    def __init__(self, function):
        self.function = function

    def __call__(self, value):
        return self.function(value)
