from collections import deque
from yargy.transformer import TEXT_TRANSFORMER
from yargy.labels import LABELS_LOOKUP_MAP

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
        """
        stack = []
        rule_index = 0
        while tokens:
            token = tokens.popleft()
            rule_type, rule_options = rules[rule_index]
            rule_labels = rule_options.get("labels", [])
            rule_repeat = rule_options.get("repeat", False)
            rule_optional = rule_options.get("optional", False)
            if rule_type == "$":
                if stack:
                    yield stack
                stack = []
                rule_index = 0
            elif token[0] == rule_type:
                if all(self.check_labels(token, rule_labels, stack)):
                    stack.append(token)
                    if (not rule_repeat) or rule_optional:
                        rule_index += 1
                else:
                    if rule_repeat or rule_optional:
                        tokens.appendleft(token)
                        rule_index += 1
                    else:
                        stack = []
                        rule_index = 0
            else:
                if rule_repeat or rule_optional:
                    tokens.appendleft(token)
                    rule_index += 1
                else:
                    stack = []
                    rule_index = 0
        else:
            if stack and rule_index == len(rules) - 1:
                yield stack

    def check_labels(self, token, labels, stack):
        for (name, value) in labels:
            yield LABELS_LOOKUP_MAP[name](token, value, stack)
