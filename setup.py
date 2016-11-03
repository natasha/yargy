from setuptools import setup, find_packages

setup(
    name='yargy',
    version='0.3.0',
    description='Tiny rule-based facts extraction package',
    url='https://github.com/bureaucratic-labs/yargy',
    author='Dmitry Veselov',
    author_email='d.a.veselov@yandex.ru',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7'
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    keywords='natural language processing, russian morphology, tomita',
    packages=find_packages(),
    install_requires=[
        'pymorphy2',
        'enum34',
        'backports.functools-lru-cache',
    ],
)
