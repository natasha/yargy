# coding: utf-8
from __future__ import unicode_literals

from .utils import assert_type
from .predicate import (
    is_predicate,
    PredicateBase,
    AndPredicate,
    OrPredicate,
    NotPredicate,
)
from .predicates import eq
from .relation import (
    is_relation,
    Relation,
    AndRelation,
    OrRelation,
    NotRelation
)
from .rule import (
    is_rule,
    Production,
    Rule,
    OrRule,
    EmptyRule,
    ForwardRule,
)
from .interpretation import (
    fact,
    AttributeScheme,
    NormalFormNormalizer,
    InflectNormalizer
)


__all__ = [
    'rule',
    'empty',
    'forward',

    'and_',
    'or_',
    'not_',

    'fact',
    'attribute',
    'normalizer',
    'inflector'
]


def prepare_production_item(item):
    if not isinstance(item, (PredicateBase, Rule)):
        return eq(item)
    else:
        return item


def rule(*items):
    production = Production([prepare_production_item(_) for _ in items])
    return Rule([production])


empty = EmptyRule
forward = ForwardRule


def and_(*items):
    if all(is_predicate(_) for _ in items):
        return AndPredicate(items)
    elif all(is_relation(_) for _ in items):
        return AndRelation(items)
    else:
        raise TypeError('mixed types')


def or_(*items):
    if all(is_predicate(_) for _ in items):
        return OrPredicate(items)
    elif all(is_relation(_) for _ in items):
        return OrRelation(items)
    elif all(is_rule(_) for _ in items):
        return OrRule(items)
    else:
        raise TypeError('mixed types')


def not_(item):
    assert_type(item, (PredicateBase, Relation))
    if is_predicate(item):
        return NotPredicate(item)
    elif is_relation(item):
        return NotRelation(item)


attribute = AttributeScheme
normalizer = NormalFormNormalizer
inflector = InflectNormalizer
