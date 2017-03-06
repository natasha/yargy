# coding: utf-8
from __future__ import unicode_literals

from enum import Enum

from pymorphy2.tagset import OpencorporaTag
from pymorphy2.analyzer import Parse

from yargy.morph import Analyzer
from yargy.tokenizer import Token
from yargy.compat import str


class InflectingTag(OpencorporaTag):

    typed_grammemes = False

class NormalizationType(Enum):

    Original = 0
    Inflected = 1
    Normalized = 2

def build_word_object(token, form, morph_analyzer=Analyzer):
    tag = InflectingTag(','.join(form['grammemes']))
    word = Parse(
        token.value,
        tag,
        form['normal_form'],
        form['score'],
        form['methods_stack'],
    )
    word._morph = morph_analyzer
    return word

def get_inflected_text(tokens, required_grammemes, morph_analyzer=Analyzer, delimiter=' '):
    if isinstance(tokens, Token):
        tokens = [tokens]
    words = []
    for token in tokens:
        form = token.forms[0]
        if form.get('methods_stack', None): # TODO: find better way for checking inflectability of word (:
            if token.normalization_type == NormalizationType.Inflected:
                # rebuild original pymorphy2 Parse object, due to https://github.com/OpenCorpora/opencorpora/issues/746#issuecomment-218672616
                word = build_word_object(token, form, morph_analyzer)
                normalized = word.inflect(required_grammemes)
                if normalized:
                    normalized = normalized.word
                else:
                    # sometimes pymorphy2 can't figure out how word looks with applied required_grammemes
                    normalized = form['normal_form']
                if not normalized:
                    raise ValueError('Can\'t figure out how word must look with given grammemes: {}'.format(word))
            elif token.normalization_type == NormalizationType.Original:
                normalized = token.value
            elif token.normalization_type == NormalizationType.Normalized:
                normalized = form['normal_form']
            else:
                raise NotImplementedError('Unknown normalization type: {}'.format(
                    token.normalization_type,
                ))
            words.append(normalized)
        else:
            words.append(
                str(token.value)
            )
    return delimiter.join(words)

def get_normalized_text(tokens, morph_analyzer=Analyzer):
    return get_inflected_text(tokens, {'nomn', 'sing'})
