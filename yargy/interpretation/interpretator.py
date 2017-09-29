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
    MorphFactAttribute,
    CustomFactAttribute
)
from .normalizer import Normalizer
from .fact import is_fact, Fact


class Wrapper(Record):
    __attributes__ = ['value', 'attribute']

    def __init__(self, value, attribute):
        self.value = value
        self.attribute = attribute


def is_wrapper(item):
    return isinstance(item, Wrapper)


class Chain(Record):
    __attributes__ = ['items', 'normalizer']

    def __init__(self, items, normalizer=None):
        self.items = items
        self.normalizer = normalizer

    def __iter__(self):
        return iter(self.items)

    def flatten(self):
        items = list(flatten(self.items, Chain))
        return Chain(items, self.normalizer)


def is_chain(item):
    return isinstance(item, Chain)


class InterpretatorBase(Record):
    pass


class FactInterpretator(InterpretatorBase):
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


class NormalizerInterpretator(InterpretatorBase):
    __attributes__ = ['normalizer']

    def __init__(self, normalizer):
        assert_type(normalizer, Normalizer)
        self.normalizer = normalizer

    def __call__(self, tokens):
        return Chain([
            NormalizedToken(self.normalizer, _)
            for _ in tokens
        ])


class AttributeInterpretator(InterpretatorBase):
    __attributes__ = ['attribute']

    def __init__(self, attribute):
        assert_type(attribute, FactAttributeBase)
        self.attribute = attribute

    @property
    def label(self):
        return self.attribute.label

    def normalize(self, item):
        if is_wrapper(item):
            item = item.value
        return item

    def __call__(self, items):
        items = Chain([self.normalize(_) for _ in items])
        items = items.flatten()
        return Wrapper(items, self.attribute)


class MorphAttributeInterpretator(AttributeInterpretator):
    __attributes__ = ['attribute', 'normalizer']

    def __init__(self, attribute, normalizer):
        super(MorphAttributeInterpretator, self).__init__(attribute)
        assert_type(normalizer, Normalizer)
        self.normalizer = normalizer

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
        return Wrapper(items, self.attribute)


class CustomAttributeInterpretator(AttributeInterpretator):
    __attributes__ = ['attribute', 'normalizer']

    def __init__(self, attribute, normalizer):
        super(CustomAttributeInterpretator, self).__init__(attribute)
        self.normalizer = normalizer

    def __call__(self, items):
        items = Chain(
            [self.normalize(_) for _ in items],
            self.normalizer
        )
        items = items.flatten()
        return Wrapper(items, self.attribute)


def prepare_attribute_interpretator(item):
    if isinstance(item, MorphFactAttribute):
        return MorphAttributeInterpretator(
            item.attribute,
            item.normalizer
        )
    elif isinstance(item, CustomFactAttribute):
        return CustomAttributeInterpretator(
            item.attribute,
            item.normalizer
        )
    else:
        return AttributeInterpretator(item)


def prepare_token_interpretator(item):
    if isinstance(item, FactAttributeBase):
        return prepare_attribute_interpretator(item)
    elif isinstance(item, Normalizer):
        return NormalizerInterpretator(item)
    else:
        raise TypeError(type(item))


def prepare_rule_interpretator(item):
    if isinstance(item, InterpretatorBase):
        return item
    elif isinstance(item, FactAttributeBase):
        return prepare_attribute_interpretator(item)
    elif isclass(item) and issubclass(item, Fact):
        return FactInterpretator(item)
    else:
        raise TypeError(type(item))
