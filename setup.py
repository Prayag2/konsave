from setuptools import setup, find_packages


def read_desc():
    with open('README.md', 'r') as desc:
        return desc.read()


setup(
    name="Konsave",
    use_scm_version=True,
    setup_requires=['setuptools_scm'],
    author="Prayag Jain",
    author_email="prayagjain2@gmail.com",
    description="A program that lets you save your Plasma configuration in an instant!",
    long_description=read_desc(),
    long_description_content_type="text/markdown",
    url="https://www.github.com/prayag2/konsave/",
    packages=find_packages(),
    package_data={'config': ['conf.yaml']},
    include_package_data=True,
    install_requires=['PyYaml'],
    classifiers=[
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: POSIX",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
        'Programming Language :: Python'
    ],
    entry_points={
        'console_scripts': [
            "konsave = konsave.__main__:main"
        ]
    }
)
