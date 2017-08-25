# coding: utf-8
from __future__ import unicode_literals

from yargy import Parser, rule, and_, not_, fact
from yargy.predicates import gram
from yargy.relations import gnc_relation
from yargy.pipelines import MorphPipeline


def test_person():
    Name = fact(
        'Name',
        ['first', 'last'],
    )
    Person = fact(
        'Person',
        ['position', 'name']
    )

    LAST = and_(
        gram('Surn'),
        not_(gram('Abbr')),
    )
    FIRST = and_(
        gram('Name'),
        not_(gram('Abbr')),
    )

    class PositionPipeline(MorphPipeline):
        grammemes = {'Position'}
        keys = [
            'управляющий директор',
            'вице-мэр'
        ]

    POSITION = gram('Position')

    gnc = gnc_relation()

    NAME = rule(
        FIRST.match(gnc).interpretation(
            Name.first
        ),
        LAST.match(gnc).interpretation(
            Name.last
        )
    ).interpretation(
        Name
    )

    PERSON = rule(
        POSITION.interpretation(
            Person.position
        ),
        NAME.interpretation(
            Person.name
        )
    ).interpretation(
        Person
    )

    parser = Parser(PERSON, pipelines=[PositionPipeline()])

    matches = list(parser.match('управляющий директор Иван Ульянов'))
    assert len(matches) == 1

    assert matches[0].fact == Person(
        position='управляющий директор',
        name=Name(
            first='Иван',
            last='Ульянов'
        )
    )
