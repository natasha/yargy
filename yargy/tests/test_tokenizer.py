# coding: utf-8
from __future__ import unicode_literals
import pytest

from yargy.morph import (
    Form,
    Grams
)
from yargy.token import (
    Token,
    MorphToken,
    TagToken,
    MorphTagToken,

    join_tokens
)
from yargy.tokenizer import (
    RUSSIAN,
    LATIN,
    INT,
    PUNCT,
    EOL,
    OTHER,

    EMAIL_RULE,

    Tokenizer,
    MorphTokenizer,
    TagMorphTokenizer
)


def test_types():
    tokenizer = Tokenizer()
    tokens = list(tokenizer('Ростов-на-Дону'))
    assert tokens == [
        Token('Ростов', (0, 6), RUSSIAN),
        Token('-', (6, 7), PUNCT),
        Token('на', (7, 9), RUSSIAN),
        Token('-', (9, 10), PUNCT),
        Token('Дону', (10, 14), RUSSIAN)
    ]

    tokens = list(tokenizer('vk.com'))
    assert tokens == [
        Token('vk', (0, 2), LATIN),
        Token('.', (2, 3), PUNCT),
        Token('com', (3, 6), LATIN)
    ]

    tokens = list(tokenizer('1 500 000$'))
    assert tokens == [
        Token('1', (0, 1), INT),
        Token('500', (2, 5), INT),
        Token('000', (6, 9), INT),
        Token('$', (9, 10), PUNCT)
    ]

    tokens = list(tokenizer('π'))
    assert tokens == [Token('π', (0, 1), OTHER)]


def test_check_type():
    tokenizer = Tokenizer()
    with pytest.raises(ValueError):
        tokenizer.check_type('UNK')

    tokenizer.remove_types(EOL)
    with pytest.raises(ValueError):
        tokenizer.check_type(EOL)


def test_change_rules():
    tokenizer = Tokenizer().add_rules(EMAIL_RULE)
    values = tokenizer.split('mailto:me@host.ru')
    assert values == ['mailto', ':', 'me@host.ru']

    tokenizer = Tokenizer().remove_types(EOL)
    text = """
hi,

the
"""
    values = tokenizer.split(text)
    assert values == ['hi', ',', 'the']


def test_morph():
    tokenizer = MorphTokenizer()
    tokens = list(tokenizer('dvd-диски'))
    assert tokens == [
        Token('dvd', (0, 3), LATIN),
        Token('-', (3, 4), PUNCT),
        MorphToken('диски', (4, 9), RUSSIAN, forms=[
            Form('диск', Grams({'NOUN', 'inan', 'masc', 'nomn', 'plur'})),
            Form('диск', Grams({'NOUN', 'accs', 'inan', 'masc', 'plur'}))
        ])
    ]


INSIDE = 'I'
OUTSIDE = 'O'


def tagger(tokens):
    for token in tokens:
        if token.type == INT and int(token.value) % 2 == 1:
            tag = INSIDE
        else:
            tag = OUTSIDE
        yield token.tagged(tag)


def test_tagger():
    tokenizer = TagMorphTokenizer(tagger)
    tokens = list(tokenizer('3-ёх морей'))
    assert tokens == [
        TagToken('3', (0, 1), INT, tag=INSIDE),
        TagToken('-', (1, 2), PUNCT, tag=OUTSIDE),
        MorphTagToken('ёх', (2, 4), RUSSIAN, tag=OUTSIDE, forms=[
            Form('ёх', Grams({'UNKN'}))
        ]),
        MorphTagToken('морей', (5, 10), RUSSIAN, tag=OUTSIDE, forms=[
            Form('море', Grams({'NOUN', 'gent', 'inan', 'neut', 'plur'}))
        ])
    ]


def test_join_tokens():
    tokenizer = Tokenizer()
    tokens = tokenizer('pi =        3.14')
    assert join_tokens(tokens) == 'pi = 3.14'
