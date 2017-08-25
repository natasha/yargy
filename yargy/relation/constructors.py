# coding: utf-8
from __future__ import unicode_literals

from yargy.utils import (
    Record,
    assert_type
)


class Relation(Record):
    def __init__(self):
        self.sides = []

    @property
    def defined(self):
        return len(self.sides) == 2

    def register(self, predicate):
        if self.defined:
            raise ValueError('used > 2 times')
        self.sides.append(predicate)
        if self.defined and id(self.first) == id(self.second):
            raise ValueError('first == second')

    @property
    def first(self):
        return self.sides[0]

    @property
    def second(self):
        return self.sides[1]

    def side(self, predicate):
        for index, side in enumerate(self.sides):
            if id(side) == id(predicate):
                return index

    def other(self, side):
        return (side + 1) % 2

    def __call__(self, token, other):
        raise NotImplementedError

    @property
    def label(self):
        return repr(self)


def is_relation(item):
    return isinstance(item, Relation)


class RelationsComposition(Relation):
    __attributes__ = ['relations']

    operator = None
    name = None

    def __init__(self, relations):
        super(RelationsComposition, self).__init__()
        relations = list(relations)
        for relation in relations:
            assert_type(relation, Relation)
        self.relations = relations

    def __call__(self, form, other):
        return self.operator(_(form, other) for _ in self.relations)

    @property
    def label(self):
        return '{name}({relations})'.format(
            name=self.name,
            relations=', '.join(_.label for _ in self.relations)
        )


class AndRelation(RelationsComposition):
    operator = all
    name = 'and_'


class OrRelation(RelationsComposition):
    operator = any
    name = 'or_'


class NotRelation(Relation):
    __attributes__ = ['relation']

    def __init__(self, relation):
        super(NotRelation, self).__init__()
        assert_type(relation, Relation)
        self.relation = relation

    def __call__(self, form, other):
        return not self.relation(form, other)

    @property
    def label(self):
        return 'not_({relation})'.format(
            relation=self.relation.label
        )
