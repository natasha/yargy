import sys

sys.path.append('..')

source_suffix = '.rst'
master_doc = 'index'

html_theme = 'alabaster'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
]
