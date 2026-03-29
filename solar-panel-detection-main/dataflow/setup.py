"""
Setup file for Dataflow pipeline dependencies
"""

import setuptools

setuptools.setup(
    name='openbuildings-import',
    version='1.0.0',
    install_requires=[
        'psycopg2-binary==2.9.9',
    ],
    packages=setuptools.find_packages(),
)
