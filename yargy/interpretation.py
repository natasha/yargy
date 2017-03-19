# coding: utf-8
from __future__ import unicode_literals

# TODO: using raw python version due to jellyfish#issues/55
from jellyfish._jellyfish import damerau_levenshtein_distance, levenshtein_distance

from yargy.compat import str
from yargy.normalization import get_normalized_text


def choice_best_span(a, b):

    if not a and not b:
        return None
    if not a and b:
        return b
    if not b and a:
        return a

    if isinstance(a, list) and isinstance(b, list):
        if len(a) >= len(b):
            return a
        else:
            return b

    if isinstance(a, list) or isinstance(b, list):
        if isinstance(a, list):
            return a
        else:
            return b

    if len(a.value) == 1:
        return b
    if len(b.value) == 1:
        return a

    if len(a.value) > len(b.value):
        return a
    else:
        return b

    if len(a.forms) > len(b.forms):
        return b
    else:
        return a


class InterpretationObject(object):

    '''
    Base class for object interpretation
    '''

    Attributes = None

    SIMILARITY_THRESHOLD = 2

    def __init__(self, **kwargs):
        for key in self.Attributes.__members__.keys():
            # set default values for object attributes
            self.__dict__[key.lower()] = None
        for key, value in kwargs.items():
            self.__dict__[key] = value

    @property
    def abbr(self):
        abbr = set()
        for span in self.spans:
            if len(span) > 1:
                abbr |= {
                    ''.join(str(x.value)[0].lower() for x in span),
                }
            else:
                abbr |= {
                    str(span[0].value).lower(),
                }
        return abbr

    @property
    def normalized(self):
        return get_normalized_text(
            self.spans[0],
        ).lower()

    def difference(self, another):
        return damerau_levenshtein_distance(
            self.normalized,
            another.normalized,
        )

    def __repr__(self):
        return '{cls}({attrs})'.format(
            cls=self.__class__.__name__,
            attrs=self.__dict__,
        )

    def __iter__(self):
        for k, v in self.__dict__.items():
            yield k, v

    def __eq__(self, another):
        if isinstance(another, self.__class__):
            a, b = self.normalized, another.normalized
            if b > a:
                a, b = b, a
            if b in a or a.startswith(b):
                return True
            if self.abbr & another.abbr:
                return True
            if self.difference(another) <= self.SIMILARITY_THRESHOLD:
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
                    attribute = token.interpretation['attribute']
                    if isinstance(attribute, list):
                        required_attribute = None
                        for field in attribute:
                            if field in self.object_class.Attributes:
                                required_attribute = field
                        if not required_attribute:
                            continue
                        attribute = required_attribute
                    else:
                        if not attribute in self.object_class.Attributes:
                            continue
                    name = attribute.name.lower()
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
