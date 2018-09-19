from __future__ import unicode_literals

import sys

_PY36 = sys.version_info[:2] >= (3, 6)

collect_ignore = []

if not _PY36:
    collect_ignore.append("test_class_based_fact_definition.py")
