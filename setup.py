# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

__version__ = None
with open(path.join(here, 'senapy', '__version.py')) as __version:
    exec(__version.read())
assert __version__ is not None

with open(path.join(here, 'README.md')) as readme:
    LONG_DESC = readme.read()

with open(path.join(here, 'requirements.txt')) as f:
    requirements = []
    for req in f.read().splitlines():
        requirements.append(req)

setup(
    name='senapy',
    version=__version__,

    description='Python client for senat.fr website',
    long_description=LONG_DESC,
    license="MIT",

    url='https://github.com/regardscitoyens/senapy',
    author='Regards Citoyens',
    author_email='contact@regardscitoyens.org',

    include_package_data=True,

    classifiers=[
        'Development Status :: 1 - Planning',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
    ],

    keywords='scraping politics data',

    packages=find_packages(),

    install_requires=requirements,

    scripts=['bin/senapy-cli'],
)
