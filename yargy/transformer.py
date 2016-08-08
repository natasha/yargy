# coding: utf-8
import re

from plyplus import Grammar, STransformer
from pymorphy2 import MorphAnalyzer


class TokenTransformer(STransformer):

    def __init__(self):
        self.morph = MorphAnalyzer()

    def word(self, node):
        node.value = node.tail[0]
        node.grammemes = set()
        node.forms = set()
        for form in self.morph.parse(node.value):
            node.grammemes = node.grammemes | set(form.tag.grammemes)
            node.forms = node.forms | {form.normal_form}
        return node

    def int(self, node):
        node.value = int(node.tail[0])
        return node

    def float(self, node):
        node.value = float(node.tail[0])
        return node

TEXT_GRAMMAR = Grammar(r"""
    start: (word | float | int | dot | comma | quote)?* ;
    word: '[\w]+' | '[\w\-]*[\w]+' | '[\w]*[\'][\w]+' ;
    int: '[+-]?[\d]+' ; 
    float: '[+-]?[\d]+[\.][\d]+' ; 
    dot: '\.' ; 
    comma: ',' ; 
    quote: '[\"\'«»`]' ; 
    SPACES: '[ \n\r\t]+' (%ignore) ;
""")
TEXT_CLEANING_REGEX = re.compile(r'[^\w\d\s\-\n\.\"\'«»`,]', flags=re.M | re.U | re.I)
TEXT_TRANSFORMER = TokenTransformer()
