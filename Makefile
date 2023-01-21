
test:
	flake8 yargy tests
	pytest -vv --doctest-modules yargy tests

exec-docs:
	python -m nbconvert \
		--ExecutePreprocessor.kernel_name=python3 \
		--ClearMetadataPreprocessor.enabled=True \
		--execute --to notebook --inplace \
		docs/*.ipynb
