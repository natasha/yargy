# Yargy [![Build Status](https://travis-ci.org/bureaucratic-labs/yargy.svg?branch=master)](https://travis-ci.org/bureaucratic-labs/yargy) [![Documentation Status](https://readthedocs.org/projects/yargy/badge/?version=latest)](http://yargy.readthedocs.io/en/latest/?badge=latest)

`Yargy` is a GLR-parser, that uses russian morphology for facts extraction process, and written in pure python

# Install

`Yargy` supports both Python 2.7+ / 3.3+ versions including PyPy.

```bash
$ pip install yargy
```

# Usage

```python
from yargy import Parser, fact
from yargy.predicates import gram
from yargy.pipelines import MorphPipeline


Person = fact(
    'Person',
    ['position', 'name']
)
Name = fact(
    'Name',
    ['first', 'last']
)


class PositionsPipeline(MorphPipeline):
    grammemes = {'Position'}
    keys = [
        'премьер министр',
        'президент'
    ]


NAME = rule(
    gram('Name').interpretation(
        Name.first.inflected()
    ),
    gram('Surn').interpretation(
        Name.last.inflected()
    )
).interpretation(
    Name
)
PERSON = rule(
    gram('Position').interpretation(
        Person.position.inflected()
    ),
    NAME.interpretation(
        Person.name
    )
).interpretation(
    Person
)


parser = Parser(PERSON, pipelines=[PositionsPipeline()])
text = '''
12 марта по приказу президента Владимира Путина ...
'''
for match in parser.findall(text):
    print(match.fact)
```

And in output you will see something like this:
```
Person(position='президент', name=Name(first='владимир', last='путин'))
```

For more examples details on grammar syntax, predicates and pipelines see [Yargy documentation](http://yargy.readthedocs.io/en/latest/).

# License

Source code of `yargy` is distributed under MIT license (allows modification and commercial usage)

# Changelog

## 0.9 (dev)
Major update required to support recursive grammar.
* Library API changed including grammar DSL and parser API
* Components updated: tokenizer, pipelines, parser, interpretation

## 0.6.0
* Initial object interpretation support
* Replaced custom tree-like struct used in `combinator.resolve_matches` method with `IntervalTree`
* `number_match` and `case_match` labels now have understand same arguments as `gnc_match` label

## 0.5.1 - 0.5.3
* Support `match_all_disambiguation_forms` argument in `gnc_match` label
* New token types - `ROMN` for roman numbers, like `XXI`, `EMAIL` for emails and `PHONE` for phone numbers
* New labels - `and_` & `or_`
* Implemented `get_normalized_text` function that returns normalized text from parsed tokens

## 0.5.0
* Partial morphology disambiguation solving support (`gnc_match` label now accepts optional boolean argument `solve_disambiguation`, which when is True, reduces number of token forms in result match)
* Rewrited labels, now they're function-based
* Rewrited tokenizer's `transform` function for better extending
* Tokenizer now adds different types of grammemes for different types of quotes (e.g. `L-QUOTE` for `«` quote)
* Implemented DAWG-based pipeline, which shows better performance over dictionary-based pipeline

## 0.4.1 - 0.4.6
* Reimplemented `resolve_matches` method in `Combinator`
* [fix] Fixed error at parsing float range with comma as delimiter
* [fix] Additional checks for terminal rule at `reduce` grammars method
* [fix] Fixed requirements in setup.py
* [fix] Tokenizer now correctly understands range values on Python2.x and PyPy platforms
* [fix] Create new grammars with terminal rule instead of appending it to original one

## 0.4
* Replaced shift-reduce parser with GLR parser, because it provides much more performance on multiple grammars (linear time with GLR vs. exponental time with shift-reduce parser).
* Pipelines support
* Added support for Python 2.7 & PyPy

## 0.3
* Implemented `gnc-match`, `in` labels

## 0.2
* Implemented `gender-match`, `number-match`, `case-match` labels
* Replace `is-title` label with `is-capitalized` label, due to http://bugs.python.org/issue7008
* Tokenizer now understands integer and float ranges (actually, two numbers separated by dash)

## 0.1
* Initial release
