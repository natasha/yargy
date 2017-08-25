# coding: utf-8
from __future__ import unicode_literals
import pytest

from yargy.tokenizer import Tokenizer
from yargy.pipelines import MorphPipeline


class CustomPipeline(MorphPipeline):

    grammemes = {'item'}

    keys = [
        'текст',
        'текст песни',
        'материал',
        'информационный материал',
    ]


@pytest.fixture
def tokenizer():
    return Tokenizer()


@pytest.fixture
def morph_pipeline():
    return CustomPipeline()


def test_that_pipeline_doesnt_drops_tokens(tokenizer, morph_pipeline):
    tokens = tokenizer('текст песни музыкальной группы')
    tokens = list(morph_pipeline(tokens))
    assert len(tokens) == 3
    assert tokens[0].value == 'текст песни'


def test_that_pipeline_correctly_join_multitokens(tokenizer, morph_pipeline):
    tokens = tokenizer('Текст информационного материала под названием ...')
    tokens = list(morph_pipeline(tokens))
    assert len(tokens) == 7
    assert tokens[1].value == 'информационного материала'
