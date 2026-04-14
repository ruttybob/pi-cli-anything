"""Setup script for cli-anything-calculator.

Uses PEP 420 namespace packages so multiple cli-anything-* packages
can coexist under the cli_anything namespace.
"""

from setuptools import setup, find_namespace_packages

setup(
    name="cli-anything-calculator",
    version="1.0.0",
    description="CLI harness for the Simple Calculator GUI application",
    long_description=open("cli_anything/calculator/README.md").read(),
    long_description_content_type="text/markdown",
    author="cli-anything",
    license="MIT",
    packages=find_namespace_packages(include=["cli_anything.*"]),
    package_data={
        "cli_anything.calculator": ["skills/*.md"],
    },
    python_requires=">=3.10",
    install_requires=[
        "click>=8.0",
        "prompt_toolkit>=3.0",
    ],
    entry_points={
        "console_scripts": [
            "cli-anything-calculator=cli_anything.calculator.calculator_cli:cli",
        ],
    },
)
