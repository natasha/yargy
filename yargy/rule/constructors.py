# coding: utf-8
from __future__ import unicode_literals

from yargy.compat import string_type
from yargy.utils import Record, assert_type
from yargy.visitor import TransformatorsComposition
from yargy.predicate import is_predicate, PredicateBase


class Production(Record):
    __attributes__ = ['terms']

    def __init__(self, terms):
        terms = list(terms)
        for term in terms:
            assert_type(term, (PredicateBase, Rule))
        self.terms = terms

    @property
    def defined(self):
        return all(
            isinstance(_, PredicateBase) or _.defined
            for _ in self.terms
        )

    @property
    def children(self):
        return self.terms


class Rule(Record):
    __attributes__ = ['productions']

    def __init__(self, productions):
        productions = list(productions)
        for production in productions:
            assert_type(production, Production)
        self.productions = productions

    @property
    def children(self):
        return self.productions

    def optional(self):
        return OptionalRule(self)

    def repeatable(self):
        return RepeatableRule(self)

    def named(self, name):
        return NamedRule(self, name)

    def interpretation(self, item):
        from yargy.interpretation import prepare_rule_interpretator
        interpretator = prepare_rule_interpretator(item)
        return InterpretationRule(self, interpretator)

    def transform(self, *transformators):
        return TransformatorsComposition(transformators)(self)

    @property
    def normalized(self):
        from .transformators import (
            SquashExtendedTransformator,
            ReplaceOrTransformator,
            FlattenTransformator,
            ExpandExtendedTransformator,
        )
        return self.transform(
            SquashExtendedTransformator,
            ExpandExtendedTransformator,
            ReplaceOrTransformator,
            FlattenTransformator
        )

    @property
    def as_dot(self):
        from .transformators import DotRuleTransformator
        return self.transform(DotRuleTransformator)

    @property
    def as_bnf(self):
        from .bnf import BNFTransformator
        return self.transform(BNFTransformator)

    @property
    def defined(self):
        return all(_.defined for _ in self.productions)

    def walk(self, types=None):
        items = bfs_rule(self)
        if types:
            items = (_ for _ in items if isinstance(_, types))
        return items

    def __or__(self, other):
        return OrRule([self, other])


def is_rule(item):
    return isinstance(item, Rule)


def bfs_rule(rule):
    queue = [rule]
    visited = {id(rule)}
    while queue:
        item = queue.pop(0)
        yield item
        for child in item.children:
            if id(child) not in visited:
                visited.add(id(child))
                queue.append(child)


class OrRule(Rule):
    __attributes__ = ['rules']

    def __init__(self, rules):
        rules = list(rules)
        for rule in rules:
            assert_type(rule, Rule)
        self.rules = rules

    @property
    def defined(self):
        return all(_.defined for _ in self.rules)

    @property
    def children(self):
        return self.rules


class WrapperRule(Rule):
    __attributes__ = ['rule']

    def __init__(self, rule):
        assert_type(rule, Rule)
        self.rule = rule

    def define(self, *args):
        return self.rule.define(*args)

    @property
    def defined(self):
        return self.rule.defined

    @property
    def children(self):
        yield self.rule


class ExtendedRule(WrapperRule):
    pass


class OptionalRule(ExtendedRule):
    pass


class RepeatableRule(ExtendedRule):
    pass


class RepeatableOptionalRule(RepeatableRule, OptionalRule):
    pass


class NamedRule(WrapperRule):
    __attributes__ = ['rule', 'name']

    def __init__(self, rule, name):
        super(NamedRule, self).__init__(rule)
        assert_type(name, string_type)
        self.name = name


class InterpretationRule(WrapperRule):
    __attributes__ = ['rule', 'interpretator']

    def __init__(self, rule, interpretator):
        from yargy.interpretation import InterpretatorBase
        super(InterpretationRule, self).__init__(rule)
        assert_type(interpretator, InterpretatorBase)
        self.interpretator = interpretator


class ForwardRule(WrapperRule):
    def __init__(self):
        self.rule = None

    def define(self, item, *items):
        if not items and is_rule(item):
            self.rule = item
        else:
            self.rule = rule(item, *items)
        return self

    @property
    def defined(self):
        return self.rule is not None

    @property
    def children(self):
        if self.defined:
            yield self.rule

    def __eq__(self, other):
        return id(self) == id(other)

    def __repr__(self):
        if self.defined:
            # sorry, need to prevent resursion
            return 'ForwardRule(...)'
        else:
            return 'ForwardRule()'


class EmptyRule(Rule):
    __attributes__ = []

    defined = True
    children = []

    def __init__(self):
        pass
