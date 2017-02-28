# coding: utf-8
from __future__ import unicode_literals

# TODO: using raw python version due to jellyfish#issues/55
from jellyfish._jellyfish import damerau_levenshtein_distance

from yargy.normalization import get_normalized_text


class InterpretationObject(object):

    '''
    Base class for object interpretation
    '''

    Attributes = None

    SIMILARITY_THRESHOLD = 3

    def __init__(self, **kwargs):
        for key in self.Attributes.__members__.keys():
            # set default values for object attributes
            self.__dict__[key.lower()] = None
        for key, value in kwargs.items():
            self.__dict__[key] = value

    @property
    def normalized(self):
        return get_normalized_text(
            self.spans[0],
        ).lower()

    def difference(self, other):
        return damerau_levenshtein_distance(
            self.normalized,
            other.normalized,
        )

    def __repr__(self):
        return '{cls}({attrs})'.format(
            cls=self.__class__.__name__,
            attrs=self.__dict__,
        )

    def __iter__(self):
        for k, v in self.__dict__.items():
            yield k, v

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            self_name = self.normalized
            other_name = other.normalized
            if len(self_name) > len(other_name):
                a, b = self_name, other_name
            else:
                a, b = other_name, self_name
            if b in a:
                return True
            if self.difference(other) <= self.SIMILARITY_THRESHOLD:
                return True
        return False

class InterpretationEngine(object):

    '''
    This class creates objects from text spans
    '''

    def __init__(self, object_class):
        self.object_class = object_class

    def extract(self, matches):
        for _, tokens in matches:
            fields = {}
            for token in tokens:
                if token.interpretation:
                    field = token.interpretation['attribute']
                    if not field in self.object_class.Attributes:
                        continue
                    name = field.name.lower()
                    if fields.get(name, None):
                        value = fields[name]
                        if isinstance(value, list):
                            value.append(token)
                        else:
                            fields[name] = [value, token]
                    else:
                        fields[name] = token
            if fields:
                fields['spans'] = [
                    tokens
                ]
                yield self.object_class(**fields)
