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
