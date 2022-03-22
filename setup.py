from setuptools import setup, find_packages
import pathlib
# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()
setup(
    name='cycletls',
    version='0.0.1',
    packages=find_packages(exclude=['tests*']),
    license='none',
    description='A python package for spoofing TLS',
    long_description_content_type="text/markdown",
    long_description=README,
    install_requires=[],
    url='https://github.com/Danny-Dasilva/cycletls_python',
    author='Danny-Dasilva',
    author_email='dannydasilva.solutions@gmail.com'
)
