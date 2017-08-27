# coding: utf-8
from __future__ import unicode_literals

from yargy.visitor import Visitor
from yargy.dot import (
    style,
    DotTransformator,
    BLUE,
    ORANGE,
    RED,
    PURPLE,
    GREEN
)

from .constructors import (
    is_rule,
    Production,
    Rule,
    OrRule,
    ExtendedRule,
    OptionalRule,
    RepeatableRule,
    RepeatableOptionalRule,
    NamedRule,
    InterpretationRule,
    ForwardRule,
    EmptyRule
)


class RuleTransformator(Visitor):
    def __init__(self):
        self.entered = {}
        self.visited = {}

    def __call__(self, root):
        forwards = [
            _ for _ in root.walk(types=ForwardRule)
            if _.defined
        ]
        for item in forwards:
            item.define(self.visit(item.rule))
        return self.visit(root)

    def visit(self, item):
        item_id = id(item)
        if item_id in self.visited:
            return self.visited[item_id]
        else:
            self.entered[item_id] = item
            item = self.resolve_method(item)(item)
            self.visited[item_id] = item
            return item

    def visit_term(self, item):
        if is_rule(item):
            return self.visit(item)
        else:
            return item

    def visit_Production(self, item):
        return Production([self.visit_term(_) for _ in item.terms])

    def visit_Rule(self, item):
        return Rule([self.visit(_) for _ in item.productions])

    def visit_OrRule(self, item):
        return OrRule([self.visit(_) for _ in item.rules])

    def visit_OptionalRule(self, item):
        return OptionalRule(self.visit(item.rule))

    def visit_RepeatableRule(self, item):
        return RepeatableRule(self.visit(item.rule))

    def visit_RepeatableOptionalRule(self, item):
        return RepeatableOptionalRule(self.visit(item.rule))

    def visit_NamedRule(self, item):
        return NamedRule(self.visit(item.rule), item.name)

    def visit_InterpretationRule(self, item):
        return InterpretationRule(self.visit(item.rule), item.interpretator)

    def visit_ForwardRule(self, item):
        return item

    def visit_EmptyRule(self, item):
        return item


class SquashExtendedTransformator(RuleTransformator):
    def visit_RepeatableRule(self, item):
        child = item.rule
        if isinstance(child, (OptionalRule, RepeatableOptionalRule)):
            return self.visit(RepeatableOptionalRule(child.rule))
        elif isinstance(child, RepeatableRule):
            return self.visit(RepeatableRule(child.rule))
        else:
            return RepeatableRule(self.visit(child))

    def visit_OptionalRule(self, item):
        child = item.rule
        if isinstance(child, (RepeatableRule, RepeatableOptionalRule)):
            return self.visit(RepeatableOptionalRule(child.rule))
        elif isinstance(child, OptionalRule):
            return self.visit(OptionalRule(child.rule))
        else:
            return OptionalRule(self.visit(child))

    def visit_RepeatableOptionalRule(self, item):
        child = item.rule
        if isinstance(child, (RepeatableRule, OptionalRule, RepeatableOptionalRule)):
            return self.visit(RepeatableOptionalRule(child.rule))
        else:
            return RepeatableOptionalRule(self.visit(child))


class ReplaceOrTransformator(RuleTransformator):
    def visit_OrRule(self, item):
        return Rule([Production([self.visit(_)]) for _ in item.rules])


class FlattenTransformator(RuleTransformator):
    def visit_term(self, item):
        if type(item) is Rule:
            productions = item.productions
            if len(productions) == 1:
                terms = productions[0].terms
                if len(terms) == 1:
                    term = terms[0]
                    return self.visit_term(term)
        return super(FlattenTransformator, self).visit_term(item)

    def visit_Production(self, item):
        terms = item.terms
        if len(terms) == 1:
            term = terms[0]
            if type(term) is Rule:
                productions = term.productions
                if len(productions) == 1:
                    production = productions[0]
                    return self.visit(production)
        return super(FlattenTransformator, self).visit_Production(item)


class ExpandExtendedTransformator(RuleTransformator):
    def visit_RepeatableRule(self, item):
        from yargy.api import forward, or_, rule

        child = self.visit(item.rule)
        temp = forward()
        return temp.define(
            or_(
                child,
                rule(child, temp)
            )
        )

    def visit_OptionalRule(self, item):
        from yargy.api import or_, empty

        child = self.visit(item.rule)
        return or_(child, empty())

    def visit_RepeatableOptionalRule(self, item):
        from yargy.api import forward, or_, rule, empty

        child = self.visit(item.rule)
        temp = forward()
        return temp.define(
            or_(
                child,
                rule(child, temp),
                empty(),
            )
        )


class DotRuleTransformator(DotTransformator, RuleTransformator):
    def visit_PredicateBase(self, item):
        return style(label=item.label)

    def visit_Production(self, item):
        return style(label='Production', fillcolor=BLUE)

    def visit_Rule(self, item):
        return style(label='Rule', fillcolor=BLUE)

    def visit_OrRule(self, item):
        return style(label='Or', fillcolor=BLUE)

    def visit_OptionalRule(self, item):
        return style(label='Optional', fillcolor=ORANGE)

    def visit_RepeatableRule(self, item):
        return style(label='Repeatable', fillcolor=ORANGE)

    def visit_RepeatableOptionalRule(self, item):
        return style(label='RepeatableOptional', fillcolor=ORANGE)

    def visit_NamedRule(self, item):
        return style(label=item.name, fillcolor=RED)

    def visit_InterpretationRule(self, item):
        return style(label=item.interpretator.label, fillcolor=GREEN)

    def visit_ForwardRule(self, item):
        return style(label='Forward', fillcolor=PURPLE)

    def visit_EmptyRule(self, item):
        return style(label='Empty')
