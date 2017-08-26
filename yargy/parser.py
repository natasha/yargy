# coding: utf-8
from __future__ import unicode_literals

from threading import Lock
from collections import defaultdict

from intervaltree import IntervalTree

from yargy.compat import str
from .utils import Record
from .token import get_tokens_span
from .tree import (
    Node,
    InterpretationNode,
    Leaf,
    Tree
)
from .tokenizer import Tokenizer
from .predicate import is_relation_predicate
from .relation import Graph as Relations
from .rule.bnf import is_rule


class Chart(object):
    def __init__(self, tokens):
        self.tokens = list(tokens)

        self.columns = [Column(0, None)]
        for index, token in enumerate(self.tokens, 1):
            self.columns.append(Column(index, token))

    def matches(self, rule):
        for column in self.columns:
            for state in column:
                if state.completed and id(state.rule) == id(rule):
                    yield state

    def __iter__(self):
        return iter(self.columns)

    def __getitem__(self, index):
        return self.columns[index]

    def __len__(self):
        return len(self.columns)

    def __repr__(self):
        return 'Chart({columns!r}, ...)'.format(
            columns=self.columns
        )

    @property
    def source(self):
        for column in self.columns:
            for line in column.source:
                yield line
            yield ''

    def _repr_pretty_(self, printer, cycle):
        for line in self.source:
            printer.text(line)
            printer.break_()


class Column(object):
    def __init__(self, index, token):
        self.index = index
        self.token = token
        self.states = []
        self.hashes = set()
        self.states_index = defaultdict(list)

    def __iter__(self):
        return iter(self.states)

    def append(self, state):
        value = hash(state)
        if value not in self.hashes:
            self.hashes.add(value)
            self.states.append(state)
            self.update_index(state)

    def update_index(self, state):
        if not state.completed:
            next_term = state.next_term
            if is_rule(next_term):
                self.states_index[id(next_term)].append(state)

    def __repr__(self):
        return 'Column({index!r}, {token!r}, ...)'.format(
            index=self.index,
            token=self.token
        )

    @property
    def source(self):
        yield '{index!r} {token!r}'.format(
            index=self.index,
            token=self.token
        )
        yield '----------------'
        for state in self.states:
            yield str(state)

    def _repr_pretty_(self, printer, cycle):
        for line in self.source:
            printer.text(line)
            printer.break_()


class State(object):
    def __init__(self, rule, production, dot_index,
                 start_column, stop_column, children,
                 relations):
        self.rule = rule
        self.production = production
        self.dot_index = dot_index
        self.start_column = start_column
        self.stop_column = stop_column
        self.children = children
        self.relations = relations

    def __hash__(self):
        return hash((
            id(self.rule), id(self.production), self.dot_index,
            self.start_column.index, self.stop_column.index
        ))

    @property
    def completed(self):
        return self.dot_index >= len(self.production.terms)

    @property
    def next_term(self):
        return self.production.terms[self.dot_index]

    def __str__(self):
        terms = self.production.terms
        production = ' '.join(
            [_.label for _ in terms[:self.dot_index]]
            + ['$']
            + [_.label for _ in terms[self.dot_index:]]
        )
        return '[{start}:{stop}] {name} -> {production}'.format(
            start=self.start_column.index,
            stop=self.stop_column.index,
            name=self.rule.label,
            production=production,
        )


class Match(Record):
    __attributes__ = ['tokens', 'span']

    def __init__(self, rule, tree):
        self.rule = rule
        self.tree = tree
        self.tokens = [_.token for _ in tree.walk(types=Leaf)]
        self.span = get_tokens_span(self.tokens)

    @property
    def fact(self):
        fact = self.tree.interpret()
        return fact.normalized


def prepare_node(rule, children):
    if rule.interpretator:
        return InterpretationNode(rule, children)
    else:
        return Node(rule, children)


class Parser(object):
    def __init__(self, rule, tokenizer=None, pipelines=None):
        self.rule = rule.normalized.as_bnf.start
        self.tokenizer = tokenizer or Tokenizer()
        self.pipelines = pipelines or []
        self.lock = Lock()

    def chart(self, text):
        with self.lock:
            stream = self.tokenizer(text)

            for pipeline in self.pipelines:
                stream = pipeline(stream)

            chart = Chart(stream)
            for column in chart:
                self.predict(column, self.rule)
                for state in column:
                    if state.completed:
                        self.complete(column, state)
                    else:
                        next_term = state.next_term
                        if is_rule(next_term):
                            self.predict(column, next_term)
                        elif column.index + 1 < len(chart):
                            next_column = chart[column.index + 1]
                            self.scan(next_column, next_term, state)
            return chart

    def extract(self, text):
        chart = self.chart(text)
        for state in chart.matches(self.rule):
            root = prepare_node(self.rule, state.children)
            tree = Tree(root).replace_token_forms(state.relations.nodes)
            yield Match(self.rule, tree)

    def resolve(self, matches):
        matches = sorted(matches, key=lambda _: len(_.tokens), reverse=True)
        tree = IntervalTree()
        for match in matches:
            start, stop = match.span
            if not tree[start:stop]:
                tree[start:stop] = match
                yield match

    def findall(self, text):
        matches = self.extract(text)
        return self.resolve(matches)

    def match(self, text):
        # NOTE Not an optimal implementation. Assume `match` is used
        # not very often
        for match in self.extract(text):
            if match.span == (0, len(text)):
                yield match

    def predict(self, column, rule):
        for production in rule.productions:
            state = State(
                rule, production,
                dot_index=0,
                start_column=column,
                stop_column=column,
                children=[],
                relations=Relations()
            )
            column.append(state)

    def scan(self, column, predicate, state):
        token = column.token
        if predicate(token):
            relations = state.relations
            if is_relation_predicate(predicate):
                relations = relations.copy().add(token, predicate)
                if not relations:
                    return
            node = Leaf(predicate, token)
            state = State(
                state.rule, state.production,
                dot_index=state.dot_index + 1,
                start_column=state.start_column,
                stop_column=column,
                children=state.children + [node],
                relations=relations
            )
            column.append(state)

    def complete(self, column, completed):
        node = prepare_node(completed.rule, completed.children)
        states = completed.start_column.states_index[id(completed.rule)]
        for state in states:
            relations = state.relations.copy().merge(completed.relations)
            if relations:
                state = State(
                    state.rule, state.production,
                    dot_index=state.dot_index + 1,
                    start_column=state.start_column,
                    stop_column=column,
                    children=state.children + [node],
                    relations=relations
                )
                column.append(state)
