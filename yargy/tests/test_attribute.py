# coding: utf-8
from __future__ import unicode_literals


from yargy import Parser, rule, fact
from yargy.predicates import gram, dictionary

Money = fact(
    'Money',
    ['count', 'base', 'currency']
)


def test_constant_attribute():
    MONEY_RULE = rule(
        gram('INT').interpretation(
            Money.count
        ),
        dictionary({'тысяча'}).interpretation(
            Money.base.const(10**3)
        ),
        dictionary({'рубль', 'доллар'}).interpretation(
            Money.currency
        ),
    ).interpretation(Money)

    parser = Parser(MONEY_RULE)
    matches = list(parser.match('1 тысяча рублей'))
    assert matches[0].fact == Money(count=1, base=1000, currency='рублей')
