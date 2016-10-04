from collections import deque
from yargy.tokenizer import Token, Tokenizer
from yargy.labels import LABELS_LOOKUP_MAP


class Stack(list):

    def have_matches_by_rule_index(self, rule_index):
        return any((rule == rule_index for (rule, _) in self))

    def flatten(self):
        return [value for (_, value) in self]

class FactParser(object):

    def __init__(self, tokenizer=None, cache_size=0, pipelines=[]):
        self.pipelines = pipelines
        self.tokenizer = tokenizer or Tokenizer(cache_size=cache_size)

    def parse(self, text, rules, out=None):
        tokens = deque(self.tokenizer.transform(text))
        return self.extract(tokens, rules, out)

    def extract(self, tokens, rules, out=None):
        """
        Actually, only God knows what going there
        Stack = [(rule_index, match), ...]
        Token = (type, value, (position_start, position_end), attributes)
        """
        stack = Stack()
        rule_index = 0
        while tokens:
            rule_type, rule_options = rules[rule_index]
            rule_labels = rule_options.get("labels", [])
            rule_repeat = rule_options.get("repeat", False)
            rule_optional = rule_options.get("optional", False)
            if rule_type == Token.Term:
                if stack:
                    yield stack.flatten()
                stack = Stack()
                rule_index = 0
                continue
            else:
                for pipeline in self.pipelines:
                    match, token = pipeline.get_match(tokens)
                    if match:
                        break
                else:
                    token = tokens.popleft()
                if token[0] == rule_type:
                    if all(self.check_labels(token, rule_labels, stack.flatten())):
                        stack.append((rule_index, token))
                        if not rule_repeat or not tokens:
                            rule_index += 1
                        continue
                if (rule_repeat and stack.have_matches_by_rule_index(rule_index)) or rule_optional:
                    tokens.appendleft(token)
                    rule_index += 1
                else:
                    if rule_index > 0:
                        tokens.appendleft(token)
                    if (stack or token) and not (out is None):
                        if not rule_index > 0:
                            out.append(token)
                        for token in stack.flatten():
                            out.append(token)
                    stack = Stack()
                    rule_index = 0
        else:
            if stack and rule_index == len(rules) - 1:
                yield stack.flatten()

    def check_labels(self, token, labels, stack):
        for (name, value) in labels:
            yield LABELS_LOOKUP_MAP[name](token, value, stack)
