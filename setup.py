
from setuptools import setup, find_packages


with open('README.md') as file:
    description = file.read()


setup(
    name='yargy',
    version='0.15.1',

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

    packages=find_packages(
        exclude=['tests']
    ),
    install_requires=[
        'pymorphy2'
    ]
)
