# coding: utf-8
from __future__ import unicode_literals
import pytest


from yargy import and_, or_, not_
from yargy.tokenizer import MorphTokenizer
from yargy.predicates import (
    normalized,
    dictionary,
    gram,
    custom
)


def test_predicate():
    tokenizer = MorphTokenizer()
    predicate = or_(
        normalized('московским'),
        and_(
            gram('NOUN'),
            not_(gram('femn'))
        )
    )
    predicate = predicate.activate(tokenizer)

    tokens = tokenizer('московский зоопарк')
    values = [predicate(_) for _ in tokens]
    assert values == [True, True]

    tokens = tokenizer('московская погода')
    values = [predicate(_) for _ in tokens]
    assert values == [True, False]


def test_checks():
    tokenizer = MorphTokenizer()
    with pytest.raises(ValueError):
        gram('UNK').activate(tokenizer)

    with pytest.raises(ValueError):
        custom(lambda _: True, types='UNK').activate(tokenizer)
