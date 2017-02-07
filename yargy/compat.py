try:
    # Python 2
    str = unicode
    string_type = basestring
    range = xrange
    RUNNING_ON_PYTHON_2_VERSION = True
except NameError:
    # Python 3
    str = str
    string_type = str
    range = range
    RUNNING_ON_PYTHON_2_VERSION = False

try:
    # Python 3.4+
    from functools import lru_cache
except ImportError:
    # Backport
    from backports.functools_lru_cache import lru_cache
