class InterpretationObject(object):

    '''
    Base class for object interpretation
    '''

    Attributes = None

    def __init__(self, **kwargs):
        for key in self.Attributes.__members__.keys():
            # set default values for object attributes
            self.__dict__[key.lower()] = None
        for key, value in kwargs.items():
            self.__dict__[key] = value

    def __iter__(self):
        for k, v in self.__dict__.items():
            yield k, v

    def __eq__(self, other):
        raise NotImplementedError

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
                    fields[field.name.lower()] = token
            if fields:
                yield self.object_class(**fields)
