# coding: utf-8
from __future__ import unicode_literals

from yargy.utils import Record


class Node(Record):
    __attributes__ = ['predicate', 'token', 'forms']

    def __init__(self, predicate, token, forms):
        self.predicate = predicate
        self.token = token
        self.forms = forms

    def copy(self):
        return Node(
            self.predicate,
            self.token,
            self.forms[:]
        )


class Edge(Record):
    __attributes__ = ['relation', 'first', 'second']

    def __init__(self, relation, first=None, second=None):
        self.relation = relation
        self.nodes = [first, second]

    @property
    def first(self):
        return self.nodes[0]

    @property
    def second(self):
        return self.nodes[1]

    @property
    def defined(self):
        return self.first and self.second

    def copy(self, nodes):
        first = self.first
        if first:
            first = nodes[id(first)]
        second = self.second
        if second:
            second = nodes[id(second)]
        return Edge(
            self.relation,
            first, second
        )

    def eval(self):
        if self.defined:
            first_forms = []
            second_forms = []
            # TODO just todo
            for second_form in self.second.forms:
                for first_form in self.first.forms:
                    if self.relation(first_form, second_form):
                        if first_form not in first_forms:
                            first_forms.append(first_form)
                        if second_form not in second_forms:
                            second_forms.append(second_form)
            self.first.forms = first_forms
            self.second.forms = second_forms

    def add(self, node):
        side = self.relation.side(node.predicate)
        # TODO Store list of tokens. Not just the left one
        if not self.nodes[side]:
            self.nodes[side] = node
            self.eval()

    def merge(self, edge):
        # TODO Store list of tokens
        if not self.defined:
            for index, node in enumerate(edge.nodes):
                if not self.nodes[index]:
                    self.nodes[index] = node
            self.eval()


class Graph(Record):
    __attributes__ = ['nodes', 'edges']

    def __init__(self, nodes=None, edges=None):
        self.nodes = []
        self.edges = []
        self.nodes_index = {}
        self.edges_index = {}
        if nodes:
            for node in nodes:
                self.add_node(node)
        if edges:
            for edge in edges:
                self.add_edge(edge)

    def copy(self):
        nodes = {
            id(_): _.copy()
            for _ in self.nodes
        }
        edges = [_.copy(nodes) for _ in self.edges]
        return Graph(nodes.values(), edges)

    def add_node(self, node):
        self.nodes.append(node)
        self.nodes_index[id(node.token)] = node

    def node(self, predicate, token):
        node = self.nodes_index.get(id(token))
        if not node:
            node = Node(predicate, token, token.forms)
            self.add_node(node)
        return node

    def add_edge(self, edge):
        self.edges.append(edge)
        self.edges_index[id(edge.relation)] = edge

    def edge(self, relation):
        edge = self.edges_index.get(id(relation))
        if not edge:
            edge = Edge(relation)
            self.add_edge(edge)
        return edge

    def add(self, token, item):
        node = self.node(item.predicate, token)
        for relation in item.relations:
            edge = self.edge(relation)
            edge.add(node)
        # TODO Need to propogate changes
        if node.forms:
            return self

    def merge(self, other):
        other = other.copy()
        nodes = other.nodes
        for node in nodes:
            self.add_node(node)
        for edge in other.edges:
            self.edge(edge.relation).merge(edge)
        # TODO Need to propogate changes
        if all(_.forms for _ in nodes):
            return self
