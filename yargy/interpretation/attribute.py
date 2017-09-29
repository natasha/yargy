# coding: utf-8
from __future__ import unicode_literals

from yargy.utils import (
    Record,
    assert_equals
)
from .normalizer import (
    InflectNormalizer,
    NormalFormNormalizer,
    ConstNormalizer,
    FunctionNormalizer
)


class AttributeSchemeBase(Record):
    __attributes__ = ['name']


class AttributeScheme(AttributeSchemeBase):
    __attributes__ = ['name', 'default']

    def __init__(self, name, default=None):
        self.name = name
        self.default = default

    def repeatable(self):
        return RepeatableAttributeScheme(self)

    def construct(self, fact):
        return FactAttribute(fact, self.name, self.default)


class RepeatableAttributeScheme(AttributeSchemeBase):
    def __init__(self, attribute):
        assert_equals(attribute.default, None)
        self.name = attribute.name

    def construct(self, fact):
        return RepeatableFactAttribute(fact, self.name)


class FactAttributeBase(Record):
    __attributes__ = ['fact', 'name']

    def __init__(self, fact, name):
        self.fact = fact
        self.name = name

    @property
    def label(self):
        return '{fact}.{name}'.format(
            fact=self.fact.__name__,
            name=self.name
        )


def prepare_normalized(attribute, item):
    if item is not None:
        if callable(item):
            return FunctionFactAttribute(attribute, item)
        else:
            return ConstFactAttribute(attribute, item)
    else:
        return NormalizedFactAttribute(attribute)


class FactAttribute(FactAttributeBase):
    __attributes__ = ['fact', 'name', 'default']

    def __init__(self, fact, name, default):
        self.fact = fact
        self.name = name
        self.default = default

    def inflected(self, grammemes=None):
        return InflectedFactAttribute(self, grammemes)

    def normalized(self, item=None):
        return prepare_normalized(self, item)


class RepeatableFactAttribute(FactAttributeBase):
    pass


class MorphFactAttribute(FactAttributeBase):
    pass


class InflectedFactAttribute(MorphFactAttribute):
    __attributes__ = ['attribute', 'grammemes']

    def __init__(self, attribute, grammemes):
        self.attribute = attribute
        self.grammemes = grammemes

    @property
    def normalizer(self):
        return InflectNormalizer(self.grammemes)


class NormalizedFactAttribute(MorphFactAttribute):
    __attributes__ = ['attribute']

    def __init__(self, attribute):
        self.attribute = attribute

    @property
    def normalizer(self):
        return NormalFormNormalizer()


class CustomFactAttribute(FactAttributeBase):
    pass


class ConstFactAttribute(CustomFactAttribute):
    __attributes__ = ['attribute', 'value']

    def __init__(self, attribute, value):
        self.attribute = attribute
        self.value = value

    @property
    def normalizer(self):
        return ConstNormalizer(self.value)


class FunctionFactAttribute(CustomFactAttribute):
    __attributes__ = ['attribute', 'function']

    def __init__(self, attribute, function):
        self.attribute = attribute
        self.function = function

    @property
    def normalizer(self):
        return FunctionNormalizer(self.function)
