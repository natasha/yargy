# coding: utf-8
from __future__ import unicode_literals

import sys

sys.path.append('..')

source_suffix = '.rst'
source_encoding= 'utf-8'
master_doc = 'index'

language='ru'

html_theme = 'alabaster'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
]
