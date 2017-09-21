# coding: utf-8
from __future__ import unicode_literals

from pymorphy2 import MorphAnalyzer as PymorphyAnalyzer

from .compat import lru_cache
from .utils import Record


class Gender(Record):
    __attributes__ = ['male', 'female', 'neutral', 'bi', 'general']

    def __init__(self, grammemes):
        self.male = 'masc' in grammemes
        self.female = 'femn' in grammemes
        self.neutral = 'neut' in grammemes
        self.bi = 'Ms-f' in grammemes or 'ms-f' in grammemes
        self.general = 'GNdr' in grammemes


class Number(Record):
    __attributes__ = ['single', 'plural', 'only_single', 'only_plural']

    def __init__(self, grammemes):
        self.single = 'sing' in grammemes
        self.plural = 'plur' in grammemes
        self.only_single = 'Sgtm' in grammemes
        self.only_plural = 'Pltm' in grammemes


class Case(Record):
    __attributes__ = ['mask', 'fixed']

    def __init__(self, grammemes):
        self.mask = [
            (_ in grammemes)
            for _ in ['nomn', 'gent', 'datv', 'accs', 'ablt', 'loct', 'voct']
        ]
        self.fixed = 'Fixd' in grammemes


class Form(Record):
    __attributes__ = ['normalized', 'grammemes']

    def __init__(self, normalized, grammemes, raw=None):
        self.normalized = normalized
        self.grammemes = grammemes
        self.raw = raw

    @property
    def gender(self):
        return Gender(self.grammemes)

    @property
    def number(self):
        return Number(self.grammemes)

    @property
    def case(self):
        return Case(self.grammemes)

    def inflect(self, grammemes=None):
        if self.raw:
            if grammemes is None:
                grammemes = {'nomn', 'sing'}
            form = self.raw.inflect(grammemes)
            if form:
                return form.word
        raise ValueError


def prepare_form(record):
    normalized = record.normal_form
    grammemes = set(record.tag.grammemes)
    return Form(normalized, grammemes, raw=record)


class MorphAnalyzer(object):
    def __init__(self):
        self.analyzer = PymorphyAnalyzer()

    def parse(self, word):
        records = self.analyzer.parse(word)
        return [prepare_form(_) for _ in records]


DEFAULT_SIZE = 100000


class CachedMorphAnalyzer(MorphAnalyzer):
    def __init__(self, size=DEFAULT_SIZE):
        super(CachedMorphAnalyzer, self).__init__()
        self.parse = lru_cache(size)(self.parse)


MORPH = CachedMorphAnalyzer()
