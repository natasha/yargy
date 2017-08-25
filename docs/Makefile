
%.rst: %.ipynb
	jupyter nbconvert --to rst $<

build: index.rst reference.rst
	sphinx-build -M html . build

clean:
	rm -rf build index_files index.rst reference.rst reference_files
