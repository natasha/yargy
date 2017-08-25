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
        from .transformators import (
            PropogateEmptyTransformator,
            KeepInterpretationNodesTransformator,
        )
        return self.transform(
            PropogateEmptyTransformator,
            KeepInterpretationNodesTransformator
        )

    def interpret(self):
        from .transformators import InterpretationTransformator
        return self.normalized.transform(
            InterpretationTransformator
        )

    def replace_token_forms(self, mapping):
        from .transformators import ReplaceTokenFormsTransformator
        return ReplaceTokenFormsTransformator(mapping)(self)

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
    __attributes__ = ['rule', 'children']

    def __init__(self, rule, children):
        self.rule = rule
        self.children = children

    @property
    def label(self):
        return self.rule.label


class Leaf(Node):
    __attributes__ = ['predicate', 'token']

    children = []

    def __init__(self, predicate, token):
        self.predicate = predicate
        self.token = token

    @property
    def label(self):
        return self.token.value


class InterpretationNode(Node):
    @property
    def interpretator(self):
        return self.rule.interpretator
