#!/usr/bin/env python

from subprocess import check_call as run
from os import getcwd, chdir
from os.path import join
from shutil import rmtree, copytree
from tempfile import mkdtemp
from contextlib import contextmanager


REPO = 'git@github.com:alexanderkuk/yargy.git'


@contextmanager
def tmpdir():
    try:
        path = mkdtemp()
        yield path
    finally:
        rmtree(path)


@contextmanager
def cwd(path):
    old_path = getcwd()
    try:
        chdir(path)
        yield
    finally:
        chdir(old_path)


def publish():
    with tmpdir() as root:
        path = join(root, 'html')
        copytree('build/html', path)
        with cwd(path):
            run(['touch', '.nojekyll'])
            run(['git', 'init'])
            run(['git', 'add', '.'])
            run(['git', 'commit', '-m', 'up'])
            run(['git', 'push', '--force', REPO, 'master:gh-pages'])


if __name__ == '__main__':
    publish()
