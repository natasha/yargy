# coding: utf-8
from __future__ import unicode_literals

from yargy.utils import assert_type

from .base import PredicateBase


class Predicate(PredicateBase):
    def match(self, *items):
        from .relation import RelationPredicate
        return RelationPredicate(self, items)


def is_predicate(item):
    return isinstance(item, Predicate)


class PredicatesComposition(Predicate):
    __attributes__ = ['predicates']

    operator = None
    name = None

    def __init__(self, predicates):
        predicates = list(predicates)
        for predicate in predicates:
            assert_type(predicate, Predicate)
        self.predicates = predicates

    def __call__(self, token):
        return self.operator(_(token) for _ in self.predicates)

    @property
    def label(self):
        return '{name}({predicates})'.format(
            name=self.name,
            predicates=', '.join(_.label for _ in self.predicates)
        )


class AndPredicate(PredicatesComposition):
    operator = all
    name = 'and_'


class OrPredicate(PredicatesComposition):
    operator = any
    name = 'or_'


class NotPredicate(Predicate):
    __attributes__ = ['predicate']

    def __init__(self, predicate):
        assert_type(predicate, Predicate)
        self.predicate = predicate

    def __call__(self, token):
        return not self.predicate(token)

    @property
    def label(self):
        return 'not_({predicate})'.format(
            predicate=self.predicate.label
        )


class ParameterPredicate(Predicate):
    __attributes__ = ['value']

    def __init__(self, value):
        self.value = value
