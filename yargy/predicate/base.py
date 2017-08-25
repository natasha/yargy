

from yargy.utils import Record


class PredicateBase(Record):
    children = []

    def __call__(self, token):
        raise NotImplementedError
        # return True of False

    def optional(self):
        from yargy.api import rule
        return rule(self).optional()

    def repeatable(self):
        from yargy.api import rule
        return rule(self).repeatable()

    def interpretation(self, attribute):
        from yargy.api import rule
        from yargy.interpretation import prepare_token_interpretator
        interpretator = prepare_token_interpretator(attribute)
        return rule(self).interpretation(interpretator)

    @property
    def label(self):
        return repr(self)
