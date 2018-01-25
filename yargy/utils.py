# coding: utf-8
from __future__ import unicode_literals


def assert_type(item, types):
    if not isinstance(item, types):
        if not isinstance(types, tuple):
            types = [types]
        raise TypeError('expected {types}, got {type}'.format(
            types=' or '.join(_.__name__ for _ in types),
            type=type(item).__name__
        ))


def assert_subclass(item, Class):
    if not issubclass(item, Class):
        raise TypeError('expected {expected}, got {got}'.format(
            expected=Class.__name__,
            got=item.__name__
        ))


def assert_equals(item, value):
    if item != value:
        raise ValueError('expected {value!r}, got {item!r}'.format(
            item=item,
            value=value
        ))


def assert_not_empty(item):
    if len(item) == 0:
        raise ValueError('expected not empty')


class Record(object):
    __attributes__ = []

    def __eq__(self, other):
        return (
            type(self) == type(other)
            and all(
                (getattr(self, _) == getattr(other, _))
                for _ in self.__attributes__
            )
        )

    def __ne__(self, other):
        return not self == other

    def __iter__(self):
        return (getattr(self, _) for _ in self.__attributes__)

    def __hash__(self):
        return hash(tuple(self))

    def __repr__(self):
        name = self.__class__.__name__
        args = ', '.join(
            repr(getattr(self, _))
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
                        printer.breakable()
                    value = getattr(self, key)
                    printer.pretty(value)


class KVRecord(Record):
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


def flatten(items, list=list):
    for item in items:
        if isinstance(item, list):
            for item in flatten(item):
                yield item
        else:
            yield item
