# yargy [![Build Status](https://travis-ci.org/bureaucratic-labs/yargy.svg?branch=master)](https://travis-ci.org/bureaucratic-labs/yargy)

```python
from yargy import FactParser

text = "газета «Коммерсантъ» сообщила ..."
rules = (("word", {}), ("quote", {}), ("word", {}), ("quote", {}), ("$", {}))
parser = FactParser(rules)

for result in parser.parse(text):
    print(result)

"""
Will print:
[word('газета'), quote('«'), word('Коммерсантъ'), quote('»')]
"""
```

```python

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
[word('Василий'), word('говорил')]
[word('Василий'), word('желал')]
[word('Василий'), word('поморщился')]
[word('Пьер'), word('был')]
[word('Пьер'), word('пробурлил')]
[word('Пьер'), word('сделал')]
[word('Элен'), word('улыбалась')]
[word('Элен'), word('была')]
[word('Элен'), word('перешла')]
[word('Ипполит'), word('перенес')]
[word('Ипполит'), word('поражал')]
"""
```

# Internals

`yargy` parses russian text into AST, adds morphology information to `word` tags, then compares AST to given rules.
