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
    ('word', 'Василий', (292, 299), {'grammemes': {'nomn', 'Name', 'masc', 'anim', 'NOUN', 'sing'}, 'forms': {'василий'}}), 
    ('word', 'говорил', (300, 307), {'grammemes': {'impf', 'tran', 'masc', 'indc', 'past', 'VERB', 'sing'}, 'forms': {'говорить'}})
]
[
    ('word', 'Пьер', (771, 775), {'grammemes': {'nomn', 'Name', 'masc', 'anim', 'NOUN', 'sing'}, 'forms': {'пьер'}}),
    ('word', 'был', (776, 779), {'grammemes': {'intr', 'impf', 'masc', 'indc', 'past', 'VERB', 'sing'}, 'forms': {'быть'}})
]
[
    ('word', 'Элен', (40, 44), {'grammemes': {'Name', 'Fixd', 'Sgtm', 'loct', 'anim', 'accs', 'NOUN', 'gent', 'ablt', 'femn', 'plur', 'datv', 'sing', 'nomn'}, 'forms': {'элен', 'элена'}}),
    ('word', 'сказала', (49, 56), {'grammemes': {'tran', 'indc', 'past', 'VERB', 'sing', 'perf', 'femn'}, 'forms': {'сказать'}})]
[
    ('word', 'Ипполит', (6, 13), {'grammemes': {'nomn', 'Name', 'masc', 'anim', 'NOUN', 'sing'}, 'forms': {'ипполит'}}),
    ('word', 'перенес', (14, 21), {'grammemes': {'tran', 'masc', 'indc', 'past', 'VERB', 'sing', 'perf'}, 'forms': {'перенести'}})
]
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
| `number-match` | Checks that words have same number grammemes | `('number-match', -1)` - will match `были` for `
дрова` and not `перенесли` for `ипполит` | 
| `case-match` | Checks that words have same case grammemes | `('case-match', -1)` - will match `красивому Ипполиту` and not `красивая Анну` |
