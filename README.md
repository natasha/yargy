# yargy [![Build Status](https://travis-ci.org/bureaucratic-labs/yargy.svg?branch=master)](https://travis-ci.org/bureaucratic-labs/yargy)

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

Next labels use raw token value (e.g. when word='сказали', it'll use 'сказали' as matching value, not normal form of that word - 'сказать') in matching.  

| Name | Description | Usage |
| ---- | ----------- | ----- |
| `eq` | Same as `==` in Python | `('eq', 1)` will match `1` and not `sample` |
| `not-eq` | Same as `!=` in Python | `('not-eq', 0)` will match everything except `0` |
| `gt` | Same as `>` in Python | `('gt', 0)` |
| `lt` | Same as `<` in Python | `('lt', 1990)` |
| `gte` | Same as `>=` in Python | `('gte', 10)` |
| `lte` | Same as `<=` in Python | `('lte', 1990)` |
| `in` | Same as `in` in Python | `('in', range(0, 10))` will match number in range between 0 and 10 |
| `not-in` | Same as `not XXX in YYY` in Python | `('not-in', [1, 2, 3])` will match everything except `1`, `2` and `3`. | 
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

Pipelines is a way to preprocess stream of tokens before passing it to parser. For example, pipeline can merge multiple nearby tokens into one and set your grammemes to it, like `['нижний', 'новгород'] ~> ['нижний_новгород/Geox:City']`  
