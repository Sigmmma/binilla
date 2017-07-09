#!/usr/bin/env python
from os.path import dirname, join
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

curr_dir = dirname(__file__)

#               YYYY.MM.DD
release_date = "2017.07.09"
version = (0, 9, 27)  # DONT FORGET TO UPDATE THE VERSION IN app_window.py

try:
    try:
        long_desc = open(join(curr_dir, "readme.rst")).read()
    except Exception:
        long_desc = open(join(curr_dir, "readme.md")).read()
except Exception:
    long_desc = 'Could not read long description from readme.'

setup(
    name='binilla',
    description='A universal binary structure editor built on supyr_struct.',
    long_description=long_desc,
    version='%s.%s.%s' % version,
    url='http://bitbucket.org/moses_of_egypt/binilla',
    author='Devin Bobadilla',
    author_email='MosesBobadilla@gmail.com',
    license='MIT',
    packages=[
        'binilla',
        ],
    package_data={
        '': ['*.txt', '*.md', '*.rst', '*.pyw'],
        'binilla': [
            'styles/*.*',
            ]
        },
    platforms=["POSIX", "Windows"],
    keywords="binilla, binary, data structure",
    install_requires=['supyr_struct'],
    requires=['supyr_struct'],
    provides=['binilla'],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        ],
    zip_safe=False,
    )
