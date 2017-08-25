# coding: utf-8
from __future__ import unicode_literals

from yargy.utils import assert_type, assert_not_empty
from yargy.relation import Relation

from .base import PredicateBase
from .constructors import Predicate


class RelationPredicate(PredicateBase):
    __attributes__ = ['predicate', 'relations']

    def __init__(self, predicate, relations):
        assert_type(predicate, Predicate)
        relations = list(relations)
        assert_not_empty(relations)
        for relation in relations:
            assert_type(relation, Relation)
            relation.register(predicate)
        self.predicate = predicate
        self.relations = relations

    def __call__(self, token):
        return self.predicate(token)

    @property
    def label(self):
        return self.predicate.label


def is_relation_predicate(predicate):
    return isinstance(predicate, RelationPredicate)
