# coding: utf-8
from __future__ import unicode_literals
from itertools import product

try:
    # C-based DAWG
    from dawg import CompletionDAWG, RecordDAWG
    c_based_dawg = True
except ImportError:
    # Pure python DAWG version
    from dawg_python import CompletionDAWG, RecordDAWG
    c_based_dawg = False

try:
    # Python 2
    unicode = unicode
except NameError:
    # Python 3
    unicode = str

from yargy.tokenizer import Token


class Pipeline(object):

    '''
    Pipelines allows to combine rule-based named-entity recognition
    with dictionary-based recognition. For example, OpenCorpora doesn't have
    enough geo-related words, so we can use GeoNames and/or Wikipedia data for
    that purposes.
    '''

    def __call__(self, stream):
        self.stream = stream
        return self

    def __iter__(self):
        return self

    def next(self):
        # Python 2
        return self.__next__()

    def __next__(self):
        # Python 3
        raise NotImplementedError

class DictionaryPipeline(Pipeline):

    '''
    Simple dictionary-based pipeline that merges multiple tokens
    into one (like gazetteer in Tomita-parser does)
    For example, it can merge ['нижний', 'новгород'] into one multitoken
    ['нижний_новгород'] and add specific morphology info to it, like
    user-defined grammeme 'Geox/City'
    '''

    DICTIONARY_WORD_SEPARATOR = '_'

    def __init__(self, dictionary):
        self.dictionary = dictionary

    def merge_stack(self, stack):
        '''
        This method produces all available combinations of words in stack
        '''
        words = [set() for _ in stack]
        for (index, token) in enumerate(stack):
            for form in (token.forms or []):
                normal_form = form['normal_form']
                words[index] |= {unicode(normal_form).lower(),}
            words[index] |= {unicode(token.value).lower(),}
        return product(*words)

    def matches_prefix(self, stack):
        words = self.merge_stack(stack)
        for form in words:
            string = self.DICTIONARY_WORD_SEPARATOR.join(form) + '_'
            for key in self.dictionary.keys():
                if key.startswith(string):
                    return True
        return False

    def matches_complete_word(self, stack):
        words = self.merge_stack(stack)
        for form in words:
            string = self.DICTIONARY_WORD_SEPARATOR.join(form)
            if string in self.dictionary:
                return True, string
        return False, None

    def get_position(self, stack):
        if len(stack) >= 2:
            head = stack[0]
            tail = stack[-1]
            start, end = head.position[0], tail.position[1]
        else:
            start, end = stack[0].position
        return start, end

    def get_original_form(self, stack):
        return self.DICTIONARY_WORD_SEPARATOR.join(
            (unicode(x.value) for x in stack)
        )

    def create_new_token(self, stack, match):
        return Token(
            self.get_original_form(stack),
            self.get_position(stack),
            self.dictionary.get(match),
        )

    def get_next_token(self):
        stack = []
        while True:
            try:
                token = next(self.stream)
            except StopIteration:
                break
            possible_stack = stack + [token]
            match = self.matches_prefix(possible_stack)
            if match:
                stack.append(token)
            else:
                match, key = self.matches_complete_word(possible_stack)
                if match:
                    yield self.create_new_token(possible_stack, key)
                else:
                    for prev_token in stack:
                        yield prev_token
                    yield token
                stack = []
        if stack:
            match, key = self.matches_complete_word(stack)
            if match:
                yield self.create_new_token(stack, key)
            else:
                for prev_token in stack:
                    yield prev_token
                yield token
            stack = []

    def __next__(self):
        return next(self.get_next_token())


class DAWGPipeline(DictionaryPipeline):

    '''
    Special type of pipeline that uses DAWG-based dictionaries for article lookups
    '''

    def __init__(self, dictionary=RecordDAWG('>I'), dictionary_path=None):
        self.dictionary = dictionary
        if dictionary_path:
            self.dictionary.load(dictionary_path)

    def matches_prefix(self, stack):
        words = self.merge_stack(stack)
        for form in words:
            key = '{0}_'.format(self.DICTIONARY_WORD_SEPARATOR.join(form))
            if self.dictionary.keys(key):
                return True
        return False

    def matches_complete_word(self, stack):
        words = self.merge_stack(stack)
        for form in words:
            key = self.DICTIONARY_WORD_SEPARATOR.join(form)
            if key in self.dictionary:
                return True, key
        return False, None

class CustomGrammemesPipeline(DAWGPipeline):

    '''
    Pipeline that uses CompletionDAWG data structure of article lookup
    Can either build dictionaries on-the-fly (on CPython platform \w installed C-based DAWG package)
    and load compiled dictionary from provided path
    When article is found, pipeline sets user-defined grammemes to token from `Grammemes` attribute
    When `Replace` attribute equals to False, pipeline appends found article grammemes
    to result token, instead of replacing original one (affects only articles with words count equal to 1)
    '''

    Grammemes = None
    Dictionary = None
    Path = None
    Replace = False

    def __init__(self, dictionary=None):
        if not dictionary:
            if self.Dictionary and c_based_dawg:
                dictionary = CompletionDAWG(self.Dictionary)
            else:
                if self.Path:
                    dictionary = CompletionDAWG()
                    super(CustomGrammemesPipeline, self).__init__(
                        dictionary=dictionary,
                        dictionary_path=self.Path,
                    )
                else:
                    raise NotImplementedError(
                        'You platform doesn\'t supports on-the-fly dictionary building. Please, define \'Path\' attribute'
                    )
        super(CustomGrammemesPipeline, self).__init__(
            dictionary=dictionary,
        )

    def create_new_token(self, stack, match):
        form = {
            'grammemes': self.Grammemes,
            'normal_form': match,
        }
        if self.Replace or len(stack) > 1:
            forms = [
                form,
            ]
        else:
            forms = stack[0].forms + [
                form,
            ]
        return Token(
            self.get_original_form(stack),
            self.get_position(stack),
            forms,
        )

    def build(self):
        if c_based_dawg:
            self.dictionary.save(self.Path)
        else:
            raise NotImplementedError('You platform doesn\'t support building of dictionaries')
