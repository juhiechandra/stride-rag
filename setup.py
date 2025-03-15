"""
Setup script for Stride RAG

This script installs the Stride RAG package and its dependencies.
"""

from setuptools import setup, find_packages
import os

# Read requirements from requirements.txt
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

# Read long description from README.md
with open('README.md', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="stride-rag",
    version="1.0.0",
    description="A multimodal Retrieval Augmented Generation system",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Stride RAG Team",
    author_email="info@example.com",
    url="https://github.com/yourusername/stride-rag",
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    entry_points={
        "console_scripts": [
            "stride-rag=api.main:run_app",
        ],
    },
)
