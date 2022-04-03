#!/usr/bin/env python3

import sys
import shlex
import subprocess
from subprocess import run


def usage():
    print('Usage: release.py 1.0.3')


def run_command(cmd):
    proc = run(
        shlex.split(cmd),
        capture_output=True,
    )
    return proc.stdout.decode()


def git_tag(tag):
    print(f'Prepare git tag for {tag}')
    run_command(f'git tag -a -s -m "Release {tag}" {tag}')


def prepare_build(ver):
    print(f'Building project')
    output = run_command('poetry version -s').strip()
    if output != ver:
        print(f'Output of "poetry version -s" "{output}" does not match the provided version "{ver}"')
        print('Please update the version or pass the right parameter?')
        exit(1)
    output = run_command('poetry build')
    print(output)

def upload():
    print('Running twine to upload.')
    try:
        print(run_command('twine upload -s dist/*'))
    except Exception as e:
        print(f'Failed to upload: {e}')


def git_push():
    print(run_command('git push origin main --tags'))

def main():
    if not len(sys.argv) == 2:
        usage()
        exit(1)
    ver = sys.argv[1]
    print(f'Preparing a release {ver}')
    ver_tag = ver
    if not ver_tag.startswith('v'):
        ver_tag = f'v{ver_tag}'
    git_tag(ver_tag)
    prepare_build(ver)
    upload()
    git_push()


main()
