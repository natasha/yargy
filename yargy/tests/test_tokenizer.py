# coding: utf-8
from __future__ import unicode_literals
import pytest

from yargy.tokenizer import Tokenizer


@pytest.fixture
def tokenizer():
    return Tokenizer()


def test_that_tokenizer_doesnt_drop_symbols(tokenizer):
    tokens = list(tokenizer('Ханты – Мансийского'))
    assert [t.value for t in tokens] == ['Ханты', '–', 'Мансийского']
    assert tokens[1].forms[0].grammemes == {'OTHER'}
