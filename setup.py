"""Setup module"""

from pathlib import Path
from typing import List

from setuptools import setup, find_packages


def _read_desc() -> str:
    """Reads the README.md.

    Returns:
        str: Contents of README.md file.
    """
    with open("README.md", "r") as desc:
        return desc.read()


def _read_reqs(path: Path) -> List[str]:
    """Reads a pip requirement file.

    Args:
        path (Path): Path to pip requirements file.

    Returns:
        :type: list of str: List of dependency identifiers.
    """
    with open(path, "r") as file:
        return file.readlines()


# Package requirements
_REQUIREMENTS: List[str] = _read_reqs(Path("requirements.txt"))
_REQUIREMENTS_DEV: List[str] = _read_reqs(Path("requirements_dev.txt"))

setup(
    name="Konsave",
    use_scm_version=True,
    setup_requires=["setuptools_scm"],
    author="Prayag Jain",
    author_email="prayagjain2@gmail.com",
    description="A program that lets you save your Plasma configuration in an instant!",
    long_description=_read_desc(),
    long_description_content_type="text/markdown",
    url="https://www.github.com/prayag2/konsave/",
    packages=find_packages(),
    package_data={"config": ["conf.yaml"]},
    include_package_data=True,
    python_requires=">=3.6",
    install_requires=_REQUIREMENTS,
    extras_require={"dev": _REQUIREMENTS_DEV},
    classifiers=[
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: POSIX",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
        "Programming Language :: Python",
    ],
    entry_points={"console_scripts": ["konsave = konsave.__main__:main"]},
)
