#!/usr/bin/env python

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(name="mwdblib",
      version="2.2.1",
      description="malwaredb API bindings for Python",
      author="psrok1",
      package_dir={'mwdblib': 'src'},
      packages=['mwdblib'],
      url="https://github.com/CERT-Polska/mwdblib",
      install_requires=open("requirements.txt").read().splitlines(),
      classifiers=[
        "Programming Language :: Python",
        "Operating System :: OS Independent",
      ])
