
test:
	flake8 yargy tests
	pytest -vv --doctest-modules yargy tests

exec-docs:
	jupyter nbconvert \
		--ClearMetadataPreprocessor.enabled=True \
		--execute --to notebook --inplace \
		docs/*.ipynb
