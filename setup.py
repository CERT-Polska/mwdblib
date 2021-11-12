#!/usr/bin/env python

from setuptools import setup

"""
We can't just import __version__ without installed dependencies
"""

version_info = {}
with open("src/__version__.py") as f:
    exec(f.read(), version_info)

setup(name="mwdblib",
      version=version_info["__version__"],
      description="MWDB API bindings for Python",
      author="psrok1",
      package_dir={'mwdblib': 'src',
                   'mwdblib.api': 'src/api',
                   'mwdblib.cli': 'src/cli',
                   'mwdblib.cli.formatters': 'src/cli/formatters'},
      packages=['mwdblib', 'mwdblib.api', 'mwdblib.cli', 'mwdblib.cli.formatters'],
      package_data={"mwdblib": ["*.pyi", "py.typed"]},
      url="https://github.com/CERT-Polska/mwdblib",
      python_requires='>=3.6',
      install_requires=[
          "requests",
          "python-dateutil",
          "keyring>=18.0.0"
      ],
      extras_require={
          "cli": [
              "click>=7.0",
              "click-default-group",
              "beautifultable>=1.0.0",
              "humanize>=0.5.1"
          ]
      },
      entry_points={
          "console_scripts": [
              'mwdb = mwdblib.cli:main [cli]'
          ]
      },
      classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: MIT License",
      ])
