# coding: utf-8
from __future__ import unicode_literals

from yargy.utils import Record
from yargy.visitor import TransformatorsComposition


class Tree(Record):
    __attributes__ = ['root']

    def __init__(self, root):
        self.root = root

    def walk(self, types=None):
        items = dfs_tree(self.root)
        if types:
            items = (_ for _ in items if isinstance(_, types))
        return items

    def transform(self, *transformators):
        return TransformatorsComposition(transformators)(self)

    @property
    def normalized(self):
        from .transformators import PropogateEmptyTransformator
        return self.transform(PropogateEmptyTransformator)

    @property
    def relations(self):
        from .transformators import RelationsTransformator
        return self.transform(RelationsTransformator)

    def constrain(self, relations):
        from .transformators import ApplyRelationsTransformator
        transform = ApplyRelationsTransformator(relations)
        return transform(self)

    def interpret(self):
        from .transformators import (
            KeepInterpretationNodesTransformator,
            InterpretationTransformator
        )
        return self.transform(
            KeepInterpretationNodesTransformator,
            InterpretationTransformator
        )

    @property
    def as_dot(self):
        from .transformators import DotTreeTransformator
        return self.transform(DotTreeTransformator)


def bfs_tree(root):
    queue = [root]
    while queue:
        item = queue.pop(0)
        yield item
        queue.extend(item.children)


def dfs_tree(root):
    queue = [root]
    while queue:
        item = queue.pop()
        yield item
        queue.extend(reversed(item.children))


class Node(Record):
    __attributes__ = ['rule', 'production', 'children']

    def __init__(self, rule, production, children):
        self.rule = rule
        self.production = production
        self.children = children

    @property
    def main(self):
        return self.children[self.production.main].main

    @property
    def interpretator(self):
        return self.rule.interpretator

    @property
    def relation(self):
        return self.rule.relation

    @property
    def label(self):
        return self.rule.label


class Leaf(Node):
    __attributes__ = ['predicate', 'token']

    children = []
    interpretator = None
    relation = None

    def __init__(self, predicate, token):
        self.predicate = predicate
        self.token = token

    @property
    def main(self):
        return self.token

    @property
    def label(self):
        return self.token.value
