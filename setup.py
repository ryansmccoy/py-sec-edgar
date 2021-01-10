#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = ['beautifulsoup4',
                'feedparser',
                'html5lib',
                'openpyxl',
                'requests',
                'xlrd',
                'python-dotenv',
                'pandas',
                'lxml',
                'chardet',
                'numpy',
                'pytest',
                'click',
                'pyarrow']

setup_requirements = ['pytest-runner', ]

test_requirements = ['pytest', ]

setup(
    author="Ryan S. McCoy",
    author_email='github@ryansmccoy.com',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Operating System :: Unix',
        'Operating System :: POSIX',
        'Operating System :: Microsoft :: Windows',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    description="Python application used to download SEC Edgar filings",
    data_files=[('refdata', ['refdata/*.csv.zip'])],
    entry_points={
        'console_scripts': [
            'py-sec-edgar=py_sec_edgar.__main__:main',
        ],
    },
    install_requires=requirements,
    license="MIT license",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords=['py-sec-edgar','sec-edgar', '10-K','financial', 'public'],
    name='py-sec-edgar',
    packages=find_packages(include=['py_sec_edgar']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/ryansmccoy/py-sec-edgar',
    version='1.0',
    zip_safe=False,
)
