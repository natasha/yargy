
from setuptools import setup, find_packages


with open('README.md') as file:
    description = file.read()


with open('requirements/main.txt') as file:
    requirements = [_.strip() for _ in file]


setup(
    name='yargy',
    version='0.14.0',

    description='Rule-based facts extraction for Russian language',
    long_description=description,
    long_description_content_type='text/markdown',

    url='https://github.com/natasha/yargy',
    author='Yargy contributors',
    author_email='d.a.veselov@yandex.ru, alex@alexkuk.ru',
    license='MIT',

    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
    ],
    keywords='natural language processing, russian morphology, glr, parser',

    packages=find_packages(),
    install_requires=requirements,
)
