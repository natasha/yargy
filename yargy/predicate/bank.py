# coding: utf-8
from __future__ import unicode_literals

from functools import wraps

from yargy.compat import (
    string_type, long
)
from .constructors import (
    Predicate,
    ParameterPredicate
)


__all__ = [
    'eq',
    'caseless',
    'in_',
    'in_caseless',
    'gte',
    'lte',
    'length_eq',
    'normalized',
    'dictionary',
    'gram',
    'custom',
    'true',
    'is_lower',
    'is_upper',
    'is_title',
    'is_capitalized',
    'is_single'
]


def type_required(type):
    def handler(method):
        @wraps(method)
        def wrapper(self, token):
            if not isinstance(token.value, type):
                return False
            else:
                return method(self, token)
        return wrapper
    return handler


def tokenize(string):
    from yargy.tokenizer import Tokenizer

    tokenizer = Tokenizer()
    return list(tokenizer(string))


class eq(ParameterPredicate):
    """a == b

    >>> predicate = eq(1)
    >>> token, = tokenize('1')
    >>> predicate(token)
    True

    """

    def __call__(self, token):
        return token.value == self.value

    @property
    def label(self):
        return repr(self.value)


class caseless(ParameterPredicate):
    """a.lower() == b.lower()


    >>> predicate = caseless('рано')
    >>> token, = tokenize('РАНО')
    >>> predicate(token)
    True

    """

    def __init__(self, value):
        super(caseless, self).__init__(value.lower())

    @type_required(string_type)
    def __call__(self, token):
        return token.value.lower() == self.value


class in_(ParameterPredicate):
    """a in b


    >>> predicate = in_({'S', 'M', 'L'})
    >>> a, b = tokenize('S 1')
    >>> predicate(a)
    True
    >>> predicate(b)
    False

    """

    def __call__(self, token):
        return token.value in self.value

    @property
    def label(self):
        return 'in_(...)'


class in_caseless(ParameterPredicate):
    """a.lower() in b

    >>> predicate = in_caseless({'S', 'M', 'L'})
    >>> a, b = tokenize('S m')
    >>> predicate(a)
    True
    >>> predicate(b)
    True

    """

    def __init__(self, value):
        value = {_.lower() for _ in value}
        super(in_caseless, self).__init__(value)

    @type_required(string_type)
    def __call__(self, token):
        return token.value.lower() in self.value

    @property
    def label(self):
        return 'in_caseless(...)'


class gte(ParameterPredicate):
    """a >= b

    >>> predicate = gte(4)
    >>> a, b, c = tokenize('3 5 C')
    >>> predicate(a)
    False
    >>> predicate(b)
    True
    >>> predicate(c)
    False

    """

    @type_required((int, float, long))
    def __call__(self, token):
        return token.value >= self.value


class lte(ParameterPredicate):
    """a <= b

    >>> predicate = lte(4)
    >>> a, b, c = tokenize('3 5 C')
    >>> predicate(a)
    True
    >>> predicate(b)
    False
    >>> predicate(c)
    False

    """
    @type_required((int, float, long))
    def __call__(self, token):
        return token.value <= self.value


class length_eq(ParameterPredicate):
    """len(a) == b

    >>> predicate = length_eq(3)
    >>> a, b = tokenize('XXX 123')
    >>> predicate(a)
    True
    >>> predicate(b)
    False

    """

    @type_required(string_type)
    def __call__(self, token):
        return len(token.value) == self.value


class normalized(ParameterPredicate):
    """Нормальная форма слова == value

    >>> a = normalized('сталь')
    >>> b = normalized('стать')
    >>> token, = tokenize('стали')
    >>> a(token)
    True
    >>> b(token)
    True

    """

    @type_required(string_type)
    def __call__(self, token):
        return any(
            _.normalized == self.value
            for _ in token.forms
        )


class dictionary(ParameterPredicate):
    """Нормальная форма слова in value

    >>> predicate = dictionary({'учитель', 'врач'})
    >>> a, b = tokenize('учителя врачи')
    >>> predicate(a)
    True
    >>> predicate(b)
    True

    """

    @type_required(string_type)
    def __call__(self, token):
        return any(
            _.normalized in self.value
            for _ in token.forms
        )

    @property
    def label(self):
        return 'dictionary(...)'


class gram(ParameterPredicate):
    """value есть среди граммем слова

    >>> a = gram('NOUN')
    >>> b = gram('VERB')
    >>> token, = tokenize('стали')
    >>> a(token)
    True
    >>> b(token)
    True

    """

    def __call__(self, token):
        return any(
            self.value in _.grammemes
            for _ in token.forms
        )


class custom(Predicate):
    """function в качестве предиката

    >>> from math import log
    >>> predicate = custom(lambda x: int(log(x, 10)) == 2, types=(int, long))
    >>> a, b = tokenize('12 123')
    >>> predicate(a)
    False
    >>> predicate(b)
    True

    """

    __attributes__ = ['function', 'types']

    def __init__(self, function, types=None):
        self.function = function
        self.types = types

    def __call__(self, token):
        value = token.value
        if self.types and not isinstance(value, self.types):
            return False
        return self.function(value)

    @property
    def label(self):
        return 'custom({name})'.format(
            name=self.function.__name__
        )


class true(Predicate):
    """Всегда возвращает True

    >>> predicate = true()
    >>> predicate(False)
    True

    """

    def __call__(self, token):
        return True


class is_lower(Predicate):
    """str.islower

    >>> predicate = is_lower()
    >>> a, b = tokenize('xxx Xxx')
    >>> predicate(a)
    True
    >>> predicate(b)
    False

    """

    @type_required(string_type)
    def __call__(self, token):
        return token.value.islower()


class is_upper(Predicate):
    """str.isupper

    >>> predicate = is_upper()
    >>> a, b = tokenize('XXX xxx')
    >>> predicate(a)
    True
    >>> predicate(b)
    False

    """

    @type_required(string_type)
    def __call__(self, token):
        return token.value.isupper()


class is_title(Predicate):
    """str.istitle

    >>> predicate = is_title()
    >>> a, b = tokenize('XXX Xxx')
    >>> predicate(a)
    False
    >>> predicate(b)
    True

    """

    @type_required(string_type)
    def __call__(self, token):
        return token.value.istitle()


class is_capitalized(Predicate):
    """Слово написано с большой буквы

    >>> predicate = is_capitalized()
    >>> a, b, c = tokenize('Xxx XXX xxX')
    >>> predicate(a)
    True
    >>> predicate(b)
    True
    >>> predicate(c)
    False

    """

    @type_required(string_type)
    def __call__(self, token):
        return token.value[0].isupper()


class is_single(Predicate):
    """Слово в единственном числе

    >>> predicate = is_single()
    >>> token, = tokenize('слово')
    >>> predicate(token)
    True

    """

    def single(self, form):
        number = form.number
        return number.single or number.only_single

    @type_required(string_type)
    def __call__(self, token):
        return any(
            self.single(_)
            for _ in token.forms
        )
