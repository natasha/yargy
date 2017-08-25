# coding: utf-8
from __future__ import unicode_literals

from inspect import isclass

from yargy.utils import (
    Record,
    assert_type,
    assert_subclass,
    flatten
)
from yargy.token import (
    Token,
    NormalizedToken
)

from .attribute import (
    FactAttributeBase,
    MorphFactAttribute
)
from .normalizer import (
    Normalizer,
    RawNormalizer
)
from .fact import is_fact, Fact


class AttributeWrapper(Record):
    __attributes__ = ['value', 'attribute']

    def __init__(self, value, attribute):
        self.value = value
        self.attribute = attribute


def is_wrapper(item):
    return isinstance(item, AttributeWrapper)


class Chain(Record):
    __attributes__ = ['items']

    def __init__(self, items):
        self.items = items

    def flatten(self):
        items = list(flatten(self.items, Chain))
        return Chain(items)


class RuleInterpretator(Record):
    pass


class FactRuleInterpretator(RuleInterpretator):
    __attributes__ = ['fact']

    def __init__(self, fact):
        assert_subclass(fact, Fact)
        self.fact = fact

    @property
    def label(self):
        return self.fact.__name__

    def __call__(self, items):
        fact = self.fact()
        for item in items:
            if is_wrapper(item) and issubclass(self.fact, item.attribute.fact):
                fact.set(
                    item.attribute.name,
                    item.value
                )
            elif is_fact(item) and isinstance(item, self.fact):
                fact.merge(item)
        return fact


class AttributeInterpretator(RuleInterpretator):
    __attributes__ = ['attribute', 'normalizer']

    def __init__(self, attribute, normalizer):
        assert_type(attribute, FactAttributeBase)
        self.attribute = attribute
        assert_type(normalizer, Normalizer)
        self.normalizer = normalizer

    @property
    def label(self):
        return self.attribute.label


class AttributeRuleInterpretator(AttributeInterpretator):
    def normalize(self, item):
        if is_wrapper(item):
            item = item.value
        if isinstance(item, Token) and not isinstance(item, NormalizedToken):
            return NormalizedToken(self.normalizer, item)
        else:
            return item

    def __call__(self, items):
        items = Chain([self.normalize(_) for _ in items])
        items = items.flatten()
        return AttributeWrapper(items, self.attribute)


class TokenInterpretator(AttributeInterpretator):
    def __call__(self, tokens):
        tokens = Chain([
            NormalizedToken(self.normalizer, _)
            for _ in tokens
        ])
        return AttributeWrapper(tokens, self.attribute)


class NormalizerInterpretator(RuleInterpretator):
    __attributes__ = ['normalizer']

    def __init__(self, normalizer):
        assert_type(normalizer, Normalizer)
        self.normalizer = normalizer

    def __call__(self, tokens):
        return Chain([
            NormalizedToken(self.normalizer, _)
            for _ in tokens
        ])


def prepare_attribute_interpretator(item, interpretator):
    if isinstance(item, MorphFactAttribute):
        normalizer = item.normalizer
        attribute = item.attribute
    else:
        normalizer = RawNormalizer()
        attribute = item
    return interpretator(attribute, normalizer)


def prepare_token_interpretator(item):
    if isinstance(item, FactAttributeBase):
        return prepare_attribute_interpretator(
            item,
            TokenInterpretator
        )
    elif isinstance(item, Normalizer):
        return NormalizerInterpretator(item)
    else:
        raise TypeError(type(item))


def prepare_rule_interpretator(item):
    if isinstance(item, RuleInterpretator):
        return item
    elif isclass(item) and issubclass(item, Fact):
        return FactRuleInterpretator(item)
    elif isinstance(item, FactAttributeBase):
        return prepare_attribute_interpretator(
            item,
            AttributeRuleInterpretator
        )
    else:
        raise TypeError(type(item))
