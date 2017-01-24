# coding: utf-8

from __future__ import unicode_literals
from itertools import count, takewhile


def frange(start, stop, step):
    return takewhile(lambda x: x <= stop, (start + i * step for i in count()))

def get_tokens_position(tokens):
    if not tokens:
        return None
    head, tail = tokens[0], tokens[-1]
    return head.position[0], tail.position[1]

def get_original_text(text, tokens):
    '''
    Returns original text captured by parser grammars
    '''
    position = get_tokens_position(tokens)
    if not position:
        return None
    else:
        start, end = position
    return text[start:end]

def get_desired_index_matches(matches, *indexes):
    for (n, tokens) in matches:
        if n in indexes:
            yield (n, tokens)


# stealed from rosettacode
ROMAN_VALUES = (
    ('I', 1),
    ('IV', 4),
    ('V', 5),
    ('IX', 9),
    ('X', 10),
    ('XL', 40),
    ('L', 50),
    ('XC', 90),
    ('C', 100),
    ('CD', 400),
    ('D', 500),
    ('CM', 900),
    ('M', 1000),
)
 
def decode_roman_number(number):
    total = 0
    for symbol, value in reversed(ROMAN_VALUES):
        while number.startswith(symbol):
            total += value
            number = number[len(symbol):]
    return total
