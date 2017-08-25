# coding: utf-8
from __future__ import unicode_literals

from subprocess import Popen, PIPE

from yargy.compat import str
from .utils import Record
from .visitor import Visitor


BLUE = '#aec7e8'
ORANGE = '#ffbb78'
GREEN = '#dbdb8d'
RED = '#ff9896'
PURPLE = '#f7b6d2'
SILVER = '#eeeeee'
GRAY = 'gray'


def dot2svg(source):
    process = Popen(
        ['dot', '-T', 'svg'],
        stdin=PIPE, stdout=PIPE, stderr=PIPE
    )
    output, error = process.communicate(source.encode('utf8'))
    if process.returncode != 0:
        raise ValueError(error)
    return output.decode('utf8')


class style(Record):
    __attributes__ = ['attributes']

    def __init__(self, **attributes):
        self.attributes = attributes

    def quote(self, value):
        value = str(value)
        replace = {
            '"': r'\"',
            '\n': r'\n',
            '\r': r'\r'
        }
        for a, b in replace.items():
            value = value.replace(a, b)
        return '"' + value + '"'

    def __str__(self):
        return ', '.join(
            '{key}={value}'.format(
                key=key,
                value=self.quote(value)
            )
            for key, value in self.attributes.items()
        )


class Node(Record):
    __attributes__ = ['id', 'style']

    def __init__(self, id, style):
        self.id = id
        self.style = style


class Edge(Record):
    __attributes__ = ['source', 'target']

    def __init__(self, source, target):
        self.source = source
        self.target = target


class Graph(Record):
    __attributes__ = ['nodes', 'edges']

    graph_style = style(
        margin=0,
        nodesep=0,
        ranksep=0
    )
    node_style = style(
        shape='box',
        fontname='sans',
        fontsize=10,
        height=0,
        width=0,
        color='none',
        style='filled',
        fillcolor=SILVER
    )
    edge_style = style(
        arrowsize=0.3,
        color=GRAY
    )

    def __init__(self):
        self.nodes = []
        self.edges = []

    def add_node(self, *args):
        node = Node(*args)
        self.nodes.append(node)

    def add_edge(self, *args):
        edge = Edge(*args)
        self.edges.append(edge)

    @property
    def source(self):
        yield 'digraph {id} {{'.format(id=id(self))
        yield 'graph [{graph_style}];'.format(graph_style=str(self.graph_style))
        yield 'node [{node_style}];'.format(node_style=str(self.node_style))
        yield 'edge [{edge_style}];'.format(edge_style=str(self.edge_style))
        for node in self.nodes:
            yield '{id} [{style}];'.format(
                id=node.id,
                style=str(node.style)
            )
        for edge in self.edges:
            yield '{source} -> {target};'.format(
                source=edge.source,
                target=edge.target
            )
        yield '}'

    def _repr_svg_(self):
        return dot2svg('\n'.join(self.source))


class DotTransformator(Visitor):
    def __call__(self, root):
        graph = Graph()
        for item in root.walk():
            style = self.visit(item)
            graph.add_node(id(item), style)
            for child in item.children:
                graph.add_edge(id(item), id(child))
        return graph
