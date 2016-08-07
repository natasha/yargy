from collections import deque
from yargy.transformer import (TEXT_GRAMMAR,
                               TEXT_CLEANING_REGEX,
                               TEXT_TRANSFORMER)
from yargy.labels import LABELS_LOOKUP_MAP

class FactParser(object):

    def __init__(self, rules):
        self.rules = rules
        self.text_grammar = TEXT_GRAMMAR
        self.text_cleaning_regex = TEXT_CLEANING_REGEX
        self.text_transformer = TEXT_TRANSFORMER

    def parse(self, text):
        text = self.text_cleaning_regex.sub(" ", text)
        ast = self.text_grammar.parse(text)
        tokens = self.text_transformer.transform(ast)
        return self.extract(deque(tokens.tail), self.rules)

    def extract(self, tokens, rules):
        stack = []
        rule_index = 0
        while len(tokens):
            token = tokens.popleft()
            rule_type, rule_options = rules[rule_index]
            rule_labels = rule_options.get("labels", [])
            rule_repeat = rule_options.get("repeat", [])
            if rule_type == "$":
                yield stack
                stack = []
                rule_index = 0
            elif token.head == rule_type:
                if all(self.check_labels(token, rule_labels, stack)):
                    stack.append(token)
                    if not rule_repeat:
                        rule_index += 1
                else:
                    if rule_repeat:
                        tokens.appendleft(token)
                        rule_index += 1
                    else:
                        stack = []
                        rule_index = 0
            else:
                if rule_repeat:
                    tokens.appendleft(token)
                    rule_index += 1
                else:
                    stack = []
                    rule_index = 0
        else:
            if stack and rule_index == len(rules) - 1:
                yield stack

    def check_labels(self, token, labels, stack):
        for label in labels:
            for name, value in label.items():
                yield LABELS_LOOKUP_MAP[name](token, value, stack)
