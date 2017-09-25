# coding: utf-8
from __future__ import unicode_literals

from collections import OrderedDict

from yargy.utils import (
    Record,
    assert_type
)
from yargy.token import join_tokens
from .attribute import (
    AttributeSchemeBase,
    RepeatableFactAttribute
)


def same_as(item, other):
    if is_fact(item) and is_fact(other):
        return item.same_as(other)
    else:
        return item == other


def normalize(item):
    from .interpretator import is_chain

    if is_chain(item):
        items = item.items
        normalizer = item.normalizer
        if len(items) == 1:
            item = items[0]
            if is_fact(item):
                value = item.normalized
            else:
                value = item.value
        else:
            if any(is_fact(_) for _ in items):
                value = [
                    (_.normalized if is_fact(_) else _.value)
                    for _ in items
                ]
            else:
                value = join_tokens(items)
        if normalizer:
            value = normalizer(value)
        return value
    else:
        # NOTE is_fact?
        return item


def serialize(item):
    if is_fact(item):
        return item.as_json
    return item


def spans(item):
    from .interpretator import is_chain
    from yargy.token import get_tokens_span

    if is_chain(item):
        chunks = []
        chunk = []
        for item in item.items:
            if is_fact(item):
                for span in item.spans:
                    yield span
                if chunk:
                    chunks.append(chunk)
            else:
                chunk.append(item)
        if chunk:
            chunks.append(chunk)
        for chunk in chunks:
            yield get_tokens_span(chunk)
    elif is_fact(item):
        for span in item.spans:
            yield span


class Fact(Record):
    __attributes__ = []

    def __init__(self, **kwargs):
        self.raw = None
        self.__repeatable = set()
        for key in self.__attributes__:
            attribute = getattr(self, key)
            if isinstance(attribute, RepeatableFactAttribute):
                self.__repeatable.add(key)
                value = []
            else:
                value = attribute.default
            setattr(self, key, value)

        self.__modified = set()
        for key, value in kwargs.items():
            if key not in self.__attributes__:
                raise TypeError(key)
            if key in self.__repeatable:
                assert_type(value, list)
            setattr(self, key, value)
            self.__modified.add(key)

    def set(self, key, value):
        if key in self.__repeatable:
            getattr(self, key).append(value)
        else:
            setattr(self, key, value)
        self.__modified.add(key)

    def merge(self, fact):
        for key in fact.__modified:
            value = getattr(fact, key)
            self.set(key, value)

    @property
    def normalized(self):
        fact = self.__class__()
        for key in self.__attributes__:
            value = getattr(self, key)
            if key in self.__repeatable:
                value = [normalize(_) for _ in value]
            else:
                value = normalize(value)
            setattr(fact, key, value)
        fact.raw = self
        return fact

    def same_as(self, other):
        return (
            type(self) == type(other)
            and all(
                same_as(
                    getattr(self, _),
                    getattr(other, _)
                )
                for _ in self.__attributes__
            )
        )

    @property
    def as_json(self):
        data = OrderedDict()
        for key in self.__attributes__:
            value = getattr(self, key)
            if key in self.__repeatable:
                value = [serialize(_) for _ in value]
            else:
                value = serialize(value)
            data[key] = value
        return data

    @property
    def spans(self):
        for key in self.__attributes__:
            value = getattr(self, key)
            if key in self.__repeatable:
                for item in value:
                    for span in spans(item):
                        yield span
            else:
                for span in spans(value):
                    yield span

    def __repr__(self):
        name = self.__class__.__name__
        args = ', '.join(
            '{key}={value!r}'.format(
                key=_,
                value=getattr(self, _)
            )
            for _ in self.__attributes__
        )
        return '{name}({args})'.format(
            name=name,
            args=args
        )

    def _repr_pretty_(self, printer, cycle):
        name = self.__class__.__name__
        if cycle:
            printer.text('{name}(...)'.format(name=name))
        else:
            with printer.group(len(name) + 1, '{name}('.format(name=name), ')'):
                for index, key in enumerate(self.__attributes__):
                    if index > 0:
                        printer.text(',')
                        printer.break_()
                    with printer.group(len(key) + 1, key + '='):
                        value = getattr(self, key)
                        printer.pretty(value)


def prepare_attribute(item):
    if isinstance(item, AttributeSchemeBase):
        return item
    else:
        from yargy.api import attribute
        return attribute(item)


def fact(name, attributes):
    cls = type(
        str(name),
        (Fact,),
        dict(__attributes__=[])
    )
    for item in attributes:
        attribute = prepare_attribute(item)
        key = attribute.name
        cls.__attributes__.append(key)
        attribute = attribute.construct(cls)
        setattr(cls, str(key), attribute)
    return cls


def is_fact(item):
    return isinstance(item, Fact)
