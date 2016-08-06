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

# Internals

`yargy` parses russian text into AST, adds morphology information to `word` tags, then compares AST to given rules.
