# yargy [![Build Status](https://travis-ci.org/bureaucratic-labs/yargy.svg?branch=master)](https://travis-ci.org/bureaucratic-labs/yargy)

```python
from yargy import FactParser

text = open("leo-tolstoy-war-and-peace.txt").read()

rules = (("word", {"labels": [
            ("gram", "Name"),
        ]}), 
         ("word", {"labels": [
            ("gram", "VERB"),
            ("gender-match", 0), # labels index is rule-based, 
                                 # so this VERB will be
                                 # compared with word
                                 # that matches rules[0]
        ]}), 
         ("$", {})
)

parser = FactParser(rules)

for line in text.splitlines():
    for result in parser.parse(line):
        print(result)

"""
Will print:
[
    ('word', 'Василий', (292, 299), ...), 
    ('word', 'говорил', (300, 307), ...),
],
[
    ('word', 'Пьер', (771, 775), ...),
    ('word', 'был', (776, 779), ...),
],
[
    ('word', 'Элен', (40, 44), ...),
    ('word', 'сказала', (49, 56), ...),
],
[
    ('word', 'Ипполит', (6, 13), ...),
    ('word', 'перенес', (14, 21), ...),
],
"""
```

# Labels

| Name | Description | Usage |
| ---- | ----------- | ----- |
| `gram` | Checks that word contains given grammeme | `('gram', 'NOUN')` |
| `gram-any` | Checks that word contains any of given grammemes | `('gram-any', ['NOUN', 'VERB'])` |
| `gram-in` | Checks that word contains all of given grammemes | `('gram-in', ['NOUN', 'Name'])` |
| `gram-not` | Reversed version of `gram` | `('gram-not', 'NOUN')` |
| `gram-not-in` | Reversed version of `gram-in` | `('gram-not-in', ['ADJS', 'ADJF'])` |
| `dictionary` | Checks that normal form of word exists in given dictionary | `('dictionary', ['говорить'])` - will match `говорил`, `говорила`, `говорили`.
| `gender-match` | Checks that words have same gender grammemes | `('gender-match', -1)` - will check candidate word with word at `-1` index in stack (actually, previous word) for gender equality. E.g. when previous_word=`Пьер` it will match `был` and not `была` |
| `number-match` | Checks that words have same number grammemes | `('number-match', -1)` - will match `были` for `дрова` and not `перенесли` for `ипполит` |
| `case-match` | Checks that words have same case grammemes | `('case-match', -1)` - will match `красивому Ипполиту` and not `красивая Анну` |
| `gnc-match` | Combination of `gender-match`, `number-match` and `case-match` | `('gnc-match', -1)` |

Next labels can be used in comparing of raw token values.  
In tokenization process, `yargy` converts numbers in given text to python `int`/`float`, so when text=`1 ипполит` output of tokenizer'll be roughly equal to `[('int', ...), ('word', ...), ...]`  
Also `yargy` tries to parse:
* dates & datetime, result converted to `datetime.datetime` object  
* int & float ranges, result represented as `range`  

| Name | Description | Usage |
| ---- | ----------- | ----- |
| `eq` | Same as `==` in Python | `('eq', 1)` will match `1` and not `sample` |
| `gt` | Same as `>` in Python | `('gt', 0)` |
| `lt` | Same as `<` in Python | `('lt', 1990)` |
| `gte` | Same as `>=` in Python | `('gte', 10)` |
| `lte` | Same as `<=` in Python | `('lte', 1990)` |
| `in` | Same as `in` in Python | `('in', range(0, 10))` will match number in range between 0 and 10 |
