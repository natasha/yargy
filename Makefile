
test:
	flake8
	pytest -vv yargy

exec-docs:
	jupyter nbconvert \
		--to notebook \
		--execute docs/*.ipynb \
		--inplace

clean:
	find . \
		-name '*.pyc' \
		-o -name __pycache__ \
		-o -name .ipynb_checkpoints \
		-o -name .DS_Store \
		| xargs rm -rf

	rm -rf dist/ build/ .pytest_cache/ .cache/ *.egg-info/
