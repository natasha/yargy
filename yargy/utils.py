from itertools import count, takewhile

def frange(start, stop, step):
    return takewhile(lambda x: x <= stop, (start + i * step for i in count()))
