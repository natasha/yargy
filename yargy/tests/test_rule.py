# coding: utf-8
from __future__ import unicode_literals
import pytest

from yargy import (
    rule,
    or_,
    forward
)


def assert_bnf(R, *bnf):
    assert list(R.normalized.as_bnf.source) == list(bnf)


def test_repeatable_optional():
    A = rule('a')
    assert_bnf(
        A.optional().repeatable(),
        "R0 -> 'a' | 'a' R0 | e",
    )
    assert_bnf(
        A.repeatable().optional(),
        "R0 -> 'a' | 'a' R0 | e",
    )
    assert_bnf(
        A.repeatable().optional().repeatable(),
        "R0 -> 'a' | 'a' R0 | e",
    )
    assert_bnf(
        A.repeatable().repeatable(),
        "R0 -> 'a' | 'a' R0"
    )
    assert_bnf(
        A.optional().optional(),
        "R0 -> 'a' | e",
    )


def test_or():
    assert_bnf(
        or_(rule('a'), rule('b')).named('A'),
        "A -> 'a' | 'b'"
    )


def test_flatten():
    assert_bnf(
        rule(rule('a')),
        "R0 -> 'a'"
    )


def test_activate():
    from yargy.pipelines import pipeline
    from yargy.predicates import gram
    from yargy.tokenizer import MorphTokenizer

    tokenizer = MorphTokenizer()

    A = pipeline(['a']).named('A')
    B = A.activate(tokenizer)
    assert_bnf(
        B,
        'A -> pipeline'
    )

    A = rule(gram('NOUN')).named('A')
    B = A.activate(tokenizer)
    assert_bnf(
        B,
        "A -> gram('NOUN')"
    )


def test_bnf():
    from yargy.interpretation import fact
    from yargy.relations import gnc_relation

    F = fact('F', ['a'])
    gnc = gnc_relation()

    assert_bnf(
        rule('a').named('A').interpretation(F),
        "F -> 'a'"
    )
    assert_bnf(
        rule('a').interpretation(F.a).interpretation(F),
        'F -> F.a',
        "F.a -> 'a'"
    )
    assert_bnf(
        rule('a').match(gnc).interpretation(F.a),
        "F.a^gnc -> 'a'"
    )
    assert_bnf(
        rule('a').interpretation(F.a).repeatable(),
        'R0 -> F.a | F.a R0',
        "F.a -> 'a'"
    )
    assert_bnf(
        rule('a').repeatable().interpretation(F.a),
        'F.a -> R1',
        "R1 -> 'a' | 'a' R1"
    )


def test_loop():
    A = forward()
    B = A.named('A')
    A.define(B)

    assert_bnf(
        A,
        'A -> A'
    )
