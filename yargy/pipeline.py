from itertools import product

from yargy.tokenizer import Token


class BasePipeline(object):

    '''
    Pipelines allows to combine rule-based named-entity recognition
    with dictionary-based recognition. For example, OpenCorpora doesn't have
    enough geo-related words, so we can use GeoNames and/or Wikipedia data for
    that purposes.
    '''

    def __init__(self, tokens, dictionary):
        self.tokens = tokens
        self.dictionary = dictionary

    def matches_prefix(self, stack, token):
        raise NotImplementedError

    def matches_complete_sequence(self, stack):
        raise NotImplementedError

    def join_stack(self, stack):
        raise NotImplementedError

    def get_match(self):
        raise NotImplementedError

    def create_new_token(self, stack):
        raise NotImplementedError

class DictionaryMatchPipeline(BasePipeline):

    def join_stack(self, tokens):
        words = [set() for _ in tokens]
        for (index, token) in enumerate(tokens):
            (_, value, _, forms) = token
            for form in (forms or []):
                normal_form = form['normal_form']
                words[index] |= {normal_form,}
            else:
                words[index] |= {str(value).lower(),}
        return product(*words)

    def matches_prefix(self, stack, token):
        words = self.join_stack([*stack, token])
        for form in words:
            string = ' '.join(form)
            for word in self.dictionary:
                if word.startswith(string):
                    return True
        return False

    def matches_complete_word(self, stack):
        words = self.join_stack(stack)
        for form in words:
            string = ' '.join(form)
            if string in self.dictionary:
                return True, string
        return False, None

    def get_match(self):
        stack = []
        while self.tokens:
            token = self.tokens.popleft()
            match = self.matches_prefix(stack, token)
            if match:
                stack.append(token)
            else:
                self.tokens.appendleft(token)
                break
        completed, match = self.matches_complete_word(stack)
        if not completed:
            for token in reversed(stack):
                self.tokens.appendleft(token)
        else:
            stack = self.create_new_token(stack, match)
        return completed, stack

    def create_new_token(self, stack, match):
        ((_, _, (start_position, _), *_), *_, (_, _, (_, end_position), *_)) = stack
        return (Token.Word, match, (start_position, end_position), {
            'grammemes': self.dictionary.get(match),
        })
