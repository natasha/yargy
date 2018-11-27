
test:
	pytest --pep8 --flakes --doctest-modules -v yargy

wheel:
	python setup.py bdist_wheel --universal

upload:
	twine upload dist/*

clean:
	find yargy -name '*.pyc' -not -path '*/__pycache__/*' -o -name '.DS_Store*' | xargs rm
	rm -rf dist build *.egg-info
