# coding: utf-8
from __future__ import unicode_literals

from yargy.visitor import Visitor
from yargy.utils import assert_type
from yargy.dot import (
    style,
    DotTransformator,
    BLUE,
    GREEN
)

from .constructors import (
    Tree,
    Node,
    InterpretationNode,
    Leaf
)


class TreeTransformator(Visitor):
    def __call__(self, tree):
        root = self.visit(tree.root)
        return Tree(root)

    def visit_Node(self, item):
        return Node(
            item.rule,
            [self.visit(_) for _ in item.children]
        )

    def visit_InterpretationNode(self, item):
        return InterpretationNode(
            item.rule,
            [self.visit(_) for _ in item.children]
        )

    def visit_Leaf(self, item):
        return item


class DotTreeTransformator(DotTransformator, TreeTransformator):
    def visit_Node(self, item):
        return style(label=item.label, fillcolor=BLUE)

    def visit_InterpretationNode(self, item):
        return style(label=item.label, fillcolor=GREEN)

    def visit_Leaf(self, item):
        return style(label=item.label)


class PropogateEmptyTransformator(TreeTransformator):
    def visit_children(self, item):
        return list(filter(
            None,
            [self.visit(_) for _ in item.children]
        ))

    def visit_Node(self, item):
        children = self.visit_children(item)
        if children:
            return Node(item.rule, children)

    def visit_InterpretationNode(self, item):
        children = self.visit_children(item)
        if children:
            return InterpretationNode(item.rule, children)


class KeepInterpretationNodesTransformator(TreeTransformator):
    def __call__(self, tree):
        assert_type(tree.root, InterpretationNode)
        return super(KeepInterpretationNodesTransformator, self).__call__(tree)

    def flatten(self, item):
        for child in item.children:
            if not isinstance(child, (InterpretationNode, Leaf)):
                for item in self.flatten(child):
                    yield item
            else:
                yield child

    def visit_InterpretationNode(self, item):
        children = [self.visit(_) for _ in self.flatten(item)]
        return InterpretationNode(item.rule, children)


class ReplaceTokenFormsTransformator(TreeTransformator):
    def __init__(self, mapping):
        self.mapping = {
            id(_.token): _.forms
            for _ in mapping
        }

    def visit_Leaf(self, item):
        predicate, token = item
        forms = self.mapping.get(id(token))
        if forms:
            token = token.replace(forms=forms)
        return Leaf(predicate, token)


class InterpretationTransformator(TreeTransformator):
    def __call__(self, tree):
        return self.visit(tree.root)

    def visit_InterpretationNode(self, item):
        args = [self.visit(_) for _ in item.children]
        return item.interpretator(args)

    def visit_Leaf(self, item):
        return item.token
