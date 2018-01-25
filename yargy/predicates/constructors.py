# coding: utf-8
from __future__ import unicode_literals

from yargy.utils import Record, assert_type


class Predicate(Record):
    children = []

    def __call__(self, token):
        # return True of False
        raise NotImplementedError

    def optional(self):
        from yargy.api import rule
        return rule(self).optional()

    def repeatable(self):
        from yargy.api import rule
        return rule(self).repeatable()

    def interpretation(self, attribute):
        from yargy.api import rule
        from yargy.interpretation import prepare_token_interpretator
        interpretator = prepare_token_interpretator(attribute)
        return rule(self).interpretation(interpretator)

    def match(self, relation):
        from yargy.api import rule
        return rule(self).match(relation)

    def activate(self, _):
        return self

    def constrain(self, token):
        return token

    @property
    def label(self):
        return repr(self)


def is_predicate(item):
    return isinstance(item, Predicate)


class PredicateScheme(Predicate):
    def activate(self, tokenizer):
        # return Predicate not a scheme
        raise NotImplementedError


class PredicatesComposition(Predicate):
    __attributes__ = ['predicates']

    operator = None
    name = None

    def __init__(self, predicates):
        predicates = list(predicates)
        for predicate in predicates:
            assert_type(predicate, Predicate)
        self.predicates = predicates

    def __call__(self, token):
        return self.operator(_(token) for _ in self.predicates)

    def activate(self, tokenizer):
        return self.__class__(
            _.activate(tokenizer)
            for _ in self.predicates
        )

    @property
    def label(self):
        return '{name}({predicates})'.format(
            name=self.name,
            predicates=', '.join(_.label for _ in self.predicates)
        )


class AndPredicate(PredicatesComposition):
    operator = all
    name = 'and_'


class OrPredicate(PredicatesComposition):
    operator = any
    name = 'or_'


class NotPredicate(Predicate):
    __attributes__ = ['predicate']

    def __init__(self, predicate):
        assert_type(predicate, Predicate)
        self.predicate = predicate

    def __call__(self, token):
        return not self.predicate(token)

    def activate(self, tokenizer):
        return NotPredicate(self.predicate.activate(tokenizer))

    @property
    def label(self):
        return 'not_({predicate})'.format(
            predicate=self.predicate.label
        )


class ParameterPredicate(Predicate):
    __attributes__ = ['value']

    def __init__(self, value):
        self.value = value


class ParameterPredicateScheme(ParameterPredicate, PredicateScheme):
    pass
