from copy import copy
from collections import deque

from yargy import FactParser


class Combinator(object):

    def __init__(self, grammars, cache_size=50000):
        self.grammars = grammars
        self.parser = FactParser(cache_size=cache_size)

    def extract(self, text):
        tokens = deque(self.parser.tokenizer.transform(text))
        for grammar in self.grammars:
            for grammar_type, rule in grammar.__members__.items():
                for match in self.parser.extract(copy(tokens), rule.value):
                    yield (grammar, grammar_type, match)
