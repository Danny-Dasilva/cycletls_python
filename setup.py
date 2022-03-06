from setuptools import setup, find_packages

setup(
    name='cycletls',
    version='0.0.1',
    packages=find_packages(exclude=['tests*']),
    license='none',
    description='A python package for spoofing TLS',
    long_description=open('README.md').read(),
    install_requires=[],
    url='github.com/Danny-Dasilva/cycletls_python',
    author='Danny-Dasilva',
    author_email='dannydasilva.solutions@gmail.com'
)
