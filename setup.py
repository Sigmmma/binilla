#!/usr/bin/env python
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

import binilla

long_desc = open(join(curr_dir, "README.RST")).read()

setup(
    name='binilla',
    description='A universal binary structure editor built on supyr_struct.',
    long_description=long_desc,
    version='%s.%s.%s' % binilla.__version__,
    url=binilla.__website__,
    author=binilla.__author__,
    author_email='MosesBobadilla@gmail.com',
    license='MIT',
    packages=[
        'binilla',
        'binilla.defs',
        'binilla.widgets',
        'binilla.widgets.field_widgets',
        'binilla.windows',
        ],
    package_data={
        'binilla': [
            'styles/*.*', '*.[tT][xX][tT]', '*.[mM][dD]', '*.RST', '*.pyw'
            ]
        },
    platforms=["POSIX", "Windows"],
    keywords="binilla, binary, data structure",
    # arbytmap can be removed from the dependencies if you cannot install
    # it for some reason, though it will prevent certain things from working.
    install_requires=['supyr_struct', 'arbytmap', 'threadsafe_tkinter',
                      'tkcolorpicker'],
    requires=['supyr_struct', 'arbytmap', 'threadsafe_tkinter',
              'tkcolorpicker'],
    provides=['binilla'],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3 :: Only",
        ],
    zip_safe=False,
    )
