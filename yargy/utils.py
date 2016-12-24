from itertools import count, takewhile

try:
    # Python 2
    unicode = unicode
except NameError:
    # Python 3
    unicode = str

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

def get_normalized_text(tokens):
    '''
    Returns text from first mophology form of each token in given tokens
    '''
    return ' '.join(
        (unicode(token.forms[0]['normal_form']) for token in tokens)
    )
