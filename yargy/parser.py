from collections import deque
from yargy.transformer import TEXT_TRANSFORMER
from yargy.labels import LABELS_LOOKUP_MAP


class Stack(list):

    def has_matches_by_rule_index(self, rule_index):
        return any((rule == rule_index for (rule, _) in self))

    def flatten(self):
        return [value for (_, value) in self]

class FactParser(object):

    def __init__(self, rules):
        self.rules = rules
        self.text_transformer = TEXT_TRANSFORMER

    def parse(self, text):
        tokens = self.text_transformer.transform(text)
        return self.extract(deque(tokens), self.rules)

    def extract(self, tokens, rules):
        """
        Actually, only God knows what going there
        Stack = [(rule_index, match), ...]
        """
        stack = Stack()
        rule_index = 0
        while tokens:
            token = tokens.popleft()
            rule_type, rule_options = rules[rule_index]
            rule_labels = rule_options.get("labels", [])
            rule_repeat = rule_options.get("repeat", False)
            rule_optional = rule_options.get("optional", False)
            if rule_type == "$":
                if stack:
                    yield stack.flatten()
                stack = Stack()
                rule_index = 0
            elif token[0] == rule_type:
                if all(self.check_labels(token, rule_labels, stack)):
                    stack.append((rule_index, token))
                    if not rule_repeat:
                        rule_index += 1
                else:
                    if rule_repeat and stack.has_matches_by_rule_index(rule_index):
                        tokens.appendleft(token)
                        rule_index += 1
                    else:
                        stack = Stack()
                        rule_index = 0
            else:
                if rule_repeat and stack.has_matches_by_rule_index(rule_index):
                    tokens.appendleft(token)
                    rule_index += 1
                else:
                    stack = Stack()
                    rule_index = 0
        else:
            if stack and rule_index == len(rules) - 1:
                yield stack.flatten()

    def check_labels(self, token, labels, stack):
        for (name, value) in labels:
            yield LABELS_LOOKUP_MAP[name](token, value, stack)
