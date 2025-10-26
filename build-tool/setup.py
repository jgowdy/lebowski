#!/usr/bin/env python3
"""
Lebowski - Re-empowering Users Through Reproducible Builds

Setup script for the lebowski build tool.
"""

from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="lebowski",
    version="0.1.0-alpha",
    author="Lebowski Project",
    author_email="opinions@lebowski.org",
    description="Build Debian packages with custom opinions - reproducibly",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/lebowski-project/lebowski",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Topic :: Software Development :: Build Tools",
        "Topic :: System :: Operating System",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires='>=3.9',
    install_requires=[
        "PyYAML>=6.0",
        "python-debian>=0.1.49",
        "click>=8.0",
        "requests>=2.28",
    ],
    entry_points={
        'console_scripts': [
            'lebowski=lebowski.cli:main',
        ],
    },
    include_package_data=True,
)
