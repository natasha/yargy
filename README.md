# yargy [![Build Status](https://travis-ci.org/bureaucratic-labs/yargy.svg?branch=master)](https://travis-ci.org/bureaucratic-labs/yargy)

`Yargy` is a GLR-parser, that uses russian morphology for facts extraction process, and written in pure python

# Install

`Yargy` supports both Python 2.7+ / 3.3+ versions including PyPy.

```bash
$ pip install yargy
```

# Usage

```python
from yargy import Grammar, Parser


# This grammar matches two words
# First must have a 'Name' grammeme (see opencorpora grammemes table)
# Second must be a lastname.
person_grammar = Grammar('Firstname_and_Lastname', [
    {
        'labels': [
            ('gram', 'Name'),
        ],
    },
    {
        'labels': [
            ('gram', 'Surn'),
            ('gnc-match', -1), # must have same gender, number and case grammemes as previous word 
        ],
    },
])

# Parser object accepts list with grammars
# And some optional arguments like 'cache_size'
parser = Parser(
    [
        person_grammar,
    ],
    # Set up morphology parser cache - this will speedup extraction process
    # You can always tune cache size, depending on available memory resources
    # 50k is enough cache, for example, for first book of War and Peace by Leo Tolstoy
    # Which contains (roughly) 35k of word forms.
    cache_size=50000,
) 

text = 'Лев Толстой написал роман «Война и Мир»'

for (grammar, match) in parser.extract(text):
    # 'grammar' variable will contain your grammar objects
    # so in post-processing stage you can write constructions
    # like isinstance(parsed_grammar_type, (my, grammars, types))

    # 'match' variable will contain tokens, matched by grammar rules
    # each token have 'value' - actual value of token in text
    # 'position' - position of token in text (in (start, end) format)
    # and 'forms' attribute - which holds results of morphological analysis of token

    print(grammar, match)

'''
And in output you will see something like this:
Grammar(name='Firstname_and_Lastname', stack=[]) [Token(value='Лев', position=(0, 3), forms=[...]), Token(value='Толстой', position=(4, 11), forms=[...])]
'''

```

# Grammar syntax

```python

grammar = [
    # matches zero or more words by given labels
    {
        'labels': [
            ('gram', 'NOUN'),
        ],
        'repeatable': True,
        'optional': True,
    },
    # matches only one word and didn't include it in result
    {
        'labels': [
            ...
        ],
        'skip': True,
    },
]

```


# Labels

This labels use normal form of words to perform matching

| Name | Description | Usage |
| ---- | ----------- | ----- |
| `gram` | Checks that word contains given grammeme | `('gram', 'NOUN')` |
| `gram-any` | Checks that word contains any of given grammemes | `('gram-any', ['NOUN', 'VERB'])` |
| `gram-in` | Checks that word contains all of given grammemes | `('gram-in', ['NOUN', 'Name'])` |
| `gram-not` | Reversed version of `gram` | `('gram-not', 'NOUN')` |
| `gram-not-in` | Reversed version of `gram-in` | `('gram-not-in', ['ADJS', 'ADJF'])` |
| `dictionary` | Checks that normal form of word exists in given dictionary | `('dictionary', ['говорить'])` - will match `говорил`, `говорила`, `говорили`.
| `dictionary-not` | Reversed version of `dictionary` | `('dictionary-not', ['котик'])` - will match everything except `котик` in all forms (`котика`, `котики`, etc.) | 
| `gender-match` | Checks that words have same gender grammemes | `('gender-match', -1)` - will check candidate word with word at `-1` index in stack (actually, previous word) for gender | equality. E.g. when previous_word=`Пьер` it will match `был` and not `была` |
| `number-match` | Checks that words have same number grammemes | `('number-match', -1)` - will match `были` for `дрова` and not `перенесли` for `ипполит` |
| `case-match` | Checks that words have same case grammemes | `('case-match', -1)` - will match `красивому Ипполиту` and not `красивая Анну` |
| `gnc-match` | Combination of `gender-match`, `number-match` and `case-match` | `('gnc-match', -1)` |
| `custom` | Calls given function | `('custom', lambda: token, value, stack: 'VERB' in token['grammemes'])` will match tokens that have `VERB` in grammemes set. |  

Next labels use raw token value (e.g. when word=`сказали`, it'll use `сказали` as matching value, not normal form of that word - `сказать`).  

| Name | Description | Usage |
| ---- | ----------- | ----- |
| `eq` | Same as `==` in Python | `('eq', 1)` will match `1` and not `sample` |
| `not-eq` | Same as `!=` in Python | `('not-eq', 0)` will match everything except `0` |
| `gt` | Same as `>` in Python | `('gt', 0)` |
| `lt` | Same as `<` in Python | `('lt', 1990)` |
| `gte` | Same as `>=` in Python | `('gte', 10)` |
| `lte` | Same as `<=` in Python | `('lte', 1990)` |
| `in` | Same as `in` in Python | `('in', range(0, 10))` will match number in range between 0 and 10 |
| `not-in` | Same as `not XXX in YYY` in Python | `('not-in', [1, 2, 3])` will match everything except `1`, `2` and `3` | 
| `is-instance` | Same as `isinstance(value, types)` in Python | `('is-instance', (int, float))` will match int & float numbers but not strings | 

# Options

Its possible to define `optional` and `repeatable` rules.  
Options defined at rule dictionary as key with boolean value (true or false):

| Option | Regex equivalent |
| ------ | ---------------- |
| `optional` | `?` |  
| `repeatable` | `+` |  
| `optional` and `repeatable` | `*` |  

Also, you can use `skip` option if you want to match tokens, but didn't want to include it in result.

# Pipelines

Pipelines is a way to preprocess stream of tokens before passing it to parser. 
Actually pipeline can do same work as Gazetteer does in Tomita-parser, where result tokens call'd as `multiword`.

For example, we can merge geo-related tokens into one `multiword`, like this:
```
[Text] -> 'в нижнем новгороде...' -> [Tokenizer]
[Tokenizer] -> ['в', 'нижнем', 'новгороде'] -> [Pipeline(s)]
[Pipeline(s)] -> ['в', 'нижнем_новгороде'] -> [Parser] 
```

Multiple pipelines can be chained into one, if you need it.

# License

Source code of `yargy` is distributed under MIT license (allows modification and commercial usage)

# Version history

## 0.5 (dev)
* Recursive grammars support

## 0.4.3

* [fix] Fixed requirements in setup.py

## 0.4.2

* [fix] Tokenizer now correctly understands range values on Python2.x and PyPy platforms
* [fix] Create new grammars with terminal rule instead of appending it to original one

## 0.4.1

* Reimplemented `resolve_matches` method in `Combinator` 

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
