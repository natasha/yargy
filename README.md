# yargy

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
