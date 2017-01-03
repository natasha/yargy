from itertools import count, takewhile
from pymorphy2.tagset import OpencorporaTag
from pymorphy2.analyzer import Parse

from yargy.morph import Analyzer

try:
    # Python 2
    unicode = unicode
except NameError:
    # Python 3
    unicode = str


class InflectingTag(OpencorporaTag):

    typed_grammemes = False


def frange(start, stop, step):
    return takewhile(lambda x: x <= stop, (start + i * step for i in count()))

def get_original_text(text, tokens):
    '''
    Returns original text captured by parser grammars
    '''
    if not tokens:
        return None
    head, tail = tokens[0], tokens[-1]
    start, end = head.position[0], tail.position[1]
    return text[start:end]

def get_normalized_text(tokens, morph_analyzer=Analyzer, required_grammemes={'nomn', 'sing'}):
    '''
    Returns text from first mophology form of each token in given tokens
    '''
    words = []
    for token in tokens:
        form = token.forms[0]
        if form.get('score', None):
            # rebuild original pymorphy2 Parse object, due to https://github.com/OpenCorpora/opencorpora/issues/746#issuecomment-218672616
            tag = InflectingTag(','.join(form['grammemes']))
            word = Parse(
                token.value,
                tag,
                form['normal_form'],
                form['score'],
                form['methods_stack'],
            )
            word._morph = morph_analyzer
            normalized = word.inflect(required_grammemes)
            if normalized:
                normalized = normalized.word
            else:
                normalized = form['normal_form']
            words.append(normal_form)
        else:
            words.append(
                unicode(form['normal_form'])
            )
    return ' '.join(words)
