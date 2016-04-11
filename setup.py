# -*- coding: utf-8 -*-

from setuptools import setup
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

__version__ = None
with open(path.join(here, 'senapy', '__version.py')) as __version:
    exec(__version.read())
assert __version__ is not None

with open(path.join(here, 'README.md')) as readme:
    LONG_DESC = readme.read().decode('utf-8')

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
        'Programming Language :: Python :: 2.7',
    ],

    keywords='scraping politics data',

    packages=['senapy', 'senapy.parsing'],

    install_requires=['pathlib', 'Click', 'requests', 'beautifulsoup4'],
)