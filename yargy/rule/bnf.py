# coding: utf-8
from __future__ import unicode_literals

from yargy.utils import Record
from yargy.compat import str

from .transformators import RuleTransformator
from .constructors import (
    bfs_rule,
    ExtendedRule,
    NamedRule,
    InterpretationRule,
    ForwardRule,
    EmptyRule
)


class BNF(Record):
    __attributes__ = ['rules']

    def generate_names(self, items):
        count = 0
        for item in items:
            if item.name is None:
                item.name = 'R%d' % count
                count += 1
            yield item

    def __init__(self, rules):
        self.rules = list(self.generate_names(rules))

    @property
    def start(self):
        return self.rules[0]

    @property
    def source(self):
        for rule in self.rules:
            yield str(rule)

    def _repr_pretty_(self, printer, cycle):
        for line in self.source:
            printer.text(line)
            printer.break_()


class Production(Record):
    __attributes__ = ['terms']

    def __init__(self, terms):
        self.terms = list(terms)

    @property
    def children(self):
        return self.terms

    def __str__(self):
        if self.terms:
            return ' '.join(_.label for _ in self.terms)
        else:
            return 'e'


class FutureProduction(Record):
    __attributes__ = ['id']

    def __init__(self, id):
        self.id = id


class Rule(Record):
    __attributes__ = ['productions', 'name', 'optional', 'repeatable', 'interpretator']

    def __init__(self, productions, name=None, optional=False, repeatable=False, interpretator=None):
        self.productions = productions
        self.name = name
        self.optional = optional
        self.repeatable = repeatable
        self.interpretator = interpretator

    @property
    def children(self):
        return self.productions

    def replace(self, name=None, optional=None, repeatable=None, interpretator=None):
        if name is None:
            name = self.name
        if optional is None:
            optional = self.optional
        if repeatable is None:
            repeatable = self.repeatable
        if interpretator is None:
            interpretator = self.interpretator
        return Rule(
            self.productions,
            name=name,
            optional=optional,
            repeatable=repeatable,
            interpretator=interpretator
        )

    def define(self, visited):
        item = self.productions
        if isinstance(item, FutureProduction):
            item = visited[item.id]
            self.productions = item.productions
            if self.name is None:
                self.name = item.name
            if self.optional is None:
                self.optional = item.optional
            if self.repeatable is None:
                self.repeatable = item.repeatable
            if self.interpretator is None:
                self.interpretator = item.interpretator

    @property
    def label(self):
        if self.interpretator:
            return self.interpretator.label
        else:
            return self.name

    def walk(self, types=None):
        items = bfs_rule(self)
        if types:
            items = (_ for _ in items if isinstance(_, types))
        return items

    def __str__(self):
        productions = ' | '.join(str(_) for _ in self.productions)
        if self.optional and self.repeatable:
            productions += ' *'
        elif self.optional:
            productions += ' ?'
        elif self.repeatable:
            productions += ' +'
        return '{name} -> {productions}'.format(
            name=self.label,
            productions=productions
        )


def is_rule(item):
    return isinstance(item, Rule)


class BNFTransformator(RuleTransformator):
    def __call__(self, root):
        if not root.defined:
            raise ValueError('rule is not defined')

        forwards = root.walk(types=ForwardRule)
        for item in forwards:
            self.visit(item.rule)
        root = self.visit(root)

        for item in root.walk(types=Rule):
            item.define(self.visited)

        return BNF(root.walk(types=Rule))

    def visit_Production(self, item):
        return Production([self.visit_term(_) for _ in item.terms])

    def visit_Rule(self, item):
        return Rule([self.visit(_) for _ in item.productions])

    def visit_OrRule(self, item):
        return Rule([Production([self.visit(_)]) for _ in item.rules])

    def visit_ExtendedRule(self, item):
        child = item.rule
        item = self.visit(child)
        if (isinstance(child, (ExtendedRule, NamedRule, InterpretationRule, EmptyRule))
            or (isinstance(child, ForwardRule)
                and isinstance(child.rule, (ExtendedRule, NamedRule, InterpretationRule, EmptyRule)))):
            item = Rule([Production([item])])
        return item

    def visit_OptionalRule(self, item):
        item = self.visit_ExtendedRule(item)
        return item.replace(optional=True)

    def visit_RepeatableRule(self, item):
        item = self.visit_ExtendedRule(item)
        return item.replace(repeatable=True)

    def visit_RepeatableOptionalRule(self, item):
        item = self.visit_ExtendedRule(item)
        return item.replace(optional=True, repeatable=True)

    def visit_NamedRule(self, item):
        child = item.rule
        name = item.name
        item = self.visit(child)
        if (isinstance(child, (NamedRule, EmptyRule))
            or (isinstance(child, ForwardRule)
                and isinstance(child, (NamedRule, EmptyRule)))):
            item = Rule([Production([item])])
        return item.replace(name=name)

    def visit_InterpretationRule(self, item):
        child = item.rule
        interpretator = item.interpretator
        item = self.visit(child)
        if (isinstance(child, (NamedRule, InterpretationRule, EmptyRule))
            or (isinstance(child, ForwardRule)
                and isinstance(child, (NamedRule, InterpretationRule, EmptyRule)))):
            item = Rule([Production([item])])
        return item.replace(interpretator=interpretator)

    def visit_ForwardRule(self, item):
        child = item.rule
        item = Rule(
            FutureProduction(id(child)),
            name=None,
            optional=None,
            repeatable=None
        )
        if isinstance(child, ForwardRule):
            item = Rule([Production([item])])
        return item

    def visit_EmptyRule(self, item):
        return Rule([Production([])])
