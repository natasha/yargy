
test:
	pytest --pep8 --flakes --doctest-modules -v yargy \
		--cov-report term-missing --cov-report xml \
		--cov-config setup.cfg --cov yargy

wheel:
	python setup.py bdist_wheel

version:
	bumpversion minor

upload:
	twine upload dist/*

clean:
	find . \
		-name '*.pyc' \
		-o -name __pycache__ \
		-o -name .ipynb_checkpoints \
		-o -name .DS_Store \
		| xargs rm -rf

	rm -rf dist/ build/ .pytest_cache/ .cache/ \
		*.egg-info/ coverage.xml .coverage
