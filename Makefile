
test:
	flake8 yargy tests
	pytest -vv --doctest-modules yargy tests

exec-docs:
	python -m nbconvert \
		--execute --to notebook --inplace \
		docs/*.ipynb
