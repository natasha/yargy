# coding: utf-8
from __future__ import unicode_literals

from yargy.utils import (
    Record,
    assert_equals
)
from .normalizer import (
    InflectNormalizer,
    NormalFormNormalizer
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


class FactAttribute(FactAttributeBase):
    __attributes__ = ['fact', 'name', 'default']

    def __init__(self, fact, name, default):
        self.fact = fact
        self.name = name
        self.default = default

    def inflected(self, grammemes=None):
        return InflectedFactAttribute(self, grammemes)

    def normalized(self):
        return NormalizedFactAttribute(self)


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
