# coding: utf-8
from __future__ import unicode_literals

from collections import defaultdict

from .compat import str, string_type
from .utils import (
    Record,
    assert_type,
    assert_not_empty,
)
from .token import Multitoken
from .morph import MORPH


class Key(Record):
    __attributes__ = ['terms']

    def __init__(self, terms):
        assert_type(terms, list)
        assert_not_empty(terms)
        self.terms = terms

    def __str__(self):
        return ' '.join(str(_) for _ in self.terms)


def maybe_lower(value):
    if isinstance(value, string_type):
        return value.lower()
    return value


class CaselessKey(Key):
    def __init__(self, terms):
        super(CaselessKey, self).__init__(terms)
        self.normalized = [maybe_lower(_) for _ in terms]


def maybe_normalize(term, morph):
    if isinstance(term, string_type):
        forms = morph.parse(term)
        return {_.normalized for _ in forms}
    return term


class MorphKey(Key):
    def __init__(self, terms, morph=MORPH):
        super(MorphKey, self).__init__(terms)
        self.normalized = [maybe_normalize(_, morph) for _ in terms]


class State(Record):
    __attributes__ = ['key', 'dot', 'start', 'stop', 'tokens']

    def __init__(self, key, dot, start, stop, tokens):
        self.key = key
        self.dot = dot
        self.start = start
        self.stop = stop
        self.tokens = tokens

    @property
    def completed(self):
        return self.dot >= len(self.key.terms)


class Column(object):
    __attributes__ = ['index', 'token', 'states']

    def __init__(self, index, token):
        self.index = index
        self.token = token
        self.states = []

    def __iter__(self):
        return iter(self.states)

    def add(self, key):
        state = State(
            key,
            dot=1,
            start=self.index,
            stop=self.index,
            tokens=[self.token]
        )
        self.states.append(state)

    def move(self, state):
        state = State(
            state.key,
            dot=state.dot + 1,
            start=state.start,
            stop=self.index,
            tokens=state.tokens + [self.token]
        )
        self.states.append(state)


class Chart(object):
    def __init__(self, tokens):
        self.columns = []
        for index, token in enumerate(tokens):
            column = Column(index, token)
            self.columns.append(column)

    @property
    def matches(self):
        for column in self.columns:
            for state in column:
                if state.completed:
                    yield state

    def __iter__(self):
        return iter(self.columns)

    def __getitem__(self, index):
        return self.columns[index]


class Pipeline(object):
    Key = Key
    grammemes = set()
    keys = []

    def __init__(self):
        assert_type(self.grammemes, set)
        assert_not_empty(self.grammemes)
        assert_type(self.keys, list)
        assert_not_empty(self.keys)
        self.keys = [self.prepare_key(_) for _ in self.keys]
        self.build_index()

    def prepare_key(self, item):
        if isinstance(item, self.Key):
            return item
        else:
            assert_type(item, (string_type, list))
            if isinstance(item, string_type):
                item = item.split()
            return self.Key(item)

    def build_index(self):
        self.index = defaultdict(list)
        for key in self.keys:
            term = key.terms[0]
            self.index[term].append(key)

    def chart(self, tokens):
        chart = Chart(tokens)
        for column in chart:
            self.predict(column)
            if column.index > 0:
                previous_column = chart[column.index - 1]
                self.scan(previous_column, column)
        return chart

    def predict(self, column):
        term = column.token.value
        if term in self.index:
            for key in self.index[term]:
                column.add(key)

    def scan(self, previous_column, column):
        term = column.token.value
        for state in previous_column:
            if not state.completed:
                next_term = state.key.terms[state.dot]
                if next_term == term:
                    column.move(state)

    def resolve(self, chart):
        matches = {}
        for state in chart.matches:
            start = state.start
            if start not in matches:
                matches[start] = state
            else:
                existing = matches[start]
                if existing.stop < state.stop:
                    matches[start] = state

        match = None
        tokens = []
        for column in chart:
            index = column.index
            token = column.token
            if not match and index in matches:
                match = matches[index]
            if match:
                tokens.append(token)
                if index == match.stop:
                    normalized = str(match.key)
                    yield Multitoken(tokens, self.grammemes, normalized)
                    match = None
                    tokens = []
            else:
                yield token

    def __call__(self, tokens):
        chart = self.chart(tokens)
        return self.resolve(chart)


class CaselessPipeline(Pipeline):
    Key = CaselessKey

    def build_index(self):
        self.index = defaultdict(list)
        for key in self.keys:
            term = key.normalized[0]
            self.index[term].append(key)

    def predict(self, column):
        term = maybe_lower(column.token.value)
        if term in self.index:
            for key in self.index[term]:
                column.add(key)

    def scan(self, previous_column, column):
        term = maybe_lower(column.token.value)
        for state in previous_column:
            if not state.completed:
                next_term = state.key.normalized[state.dot]
                if next_term == term:
                    column.move(state)


class MorphPipeline(Pipeline):
    Key = MorphKey
    morph = MORPH

    def prepare_key(self, item):
        if isinstance(item, MorphKey):
            return item
        else:
            assert_type(item, (string_type, list))
            if isinstance(item, string_type):
                item = item.split()
            return MorphKey(item, self.morph)

    def build_index(self):
        self.index = defaultdict(list)
        for key in self.keys:
            for term in key.normalized[0]:
                self.index[term].append(key)

    def predict(self, column):
        terms = {_.normalized for _ in column.token.forms}
        for term in terms:
            if term in self.index:
                for key in self.index[term]:
                    column.add(key)

    def scan(self, previous_column, column):
        terms = {_.normalized for _ in column.token.forms}
        for state in previous_column:
            if not state.completed:
                next_term = state.key.normalized[state.dot]
                if next_term & terms:
                    column.move(state)
