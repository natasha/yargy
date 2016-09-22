from copy import copy
from collections import deque

from yargy import FactParser


class Combinator(object):

    def __init__(self, grammars, parser=None, cache_size=50000):
        self.grammars = grammars
        self.parser = parser or FactParser(cache_size=cache_size)

    def extract(self, text):
        tokens = deque(self.parser.tokenizer.transform(text))
        for grammar in self.grammars:
            for grammar_type, rule in grammar.__members__.items():
                for match in self.parser.extract(copy(tokens), rule.value):
                    yield (grammar, grammar_type, match)

    def resolve_matches(self, matches):
        matches = sorted(matches, key=lambda m: len(m[2]), reverse=True)
        index = {}
        for match in matches:
            *_, tokens = match
            head, tail = tokens[0], tokens[-1]
            x, y = head[2][0], tail[2][1]
            length = len(tokens)
            for (m_x, m_y, m_len) in index.keys():
                if (x >= m_x and y <= m_y):
                    if (m_len > length):
                        break
            else:
                index[(x, y, length)] = match
        return index.values()
