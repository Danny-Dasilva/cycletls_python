from setuptools import setup, find_packages
import pathlib
import platform
import os

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# Determine which binary to include based on platform
def get_package_data():
    """
    Determine which shared library to include in the package.
    """
    system = platform.system()
    if system == "Windows":
        candidates = ["dist/cycletls.dll"]
    elif system == "Darwin":
        candidates = ["dist/libcycletls.dylib"]
    else:
        candidates = ["dist/libcycletls.so"]

    data = [path for path in candidates if os.path.exists(os.path.join(HERE, path))]

    header_path = os.path.join(HERE, "dist/libcycletls.h")
    if os.path.exists(header_path):
        data.append('dist/libcycletls.h')

    return data or ['dist/*']


setup(
    name='cycletls',
    version='1.0.0',
    packages=find_packages(exclude=['tests*', 'golang*', 'examples*']),
    package_data={
        'cycletls': get_package_data(),
    },
    include_package_data=True,
    license='MIT',
    description='Advanced TLS fingerprinting library with JA3, JA4, HTTP/2, HTTP/3, WebSocket, and SSE support',
    long_description_content_type="text/markdown",
    long_description=README,
    install_requires=[
        'cffi>=1.15.0',
        'orjson>=3.9.0',
        'msgpack>=1.0.0',
    ],
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-asyncio>=0.18.0',
            'black>=22.0.0',
            'isort>=5.10.0',
            'mypy>=0.950',
        ],
    },
    python_requires='>=3.8',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Security',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    keywords='tls fingerprinting ja3 ja4 http2 http3 websocket sse quic',
    url='https://github.com/Danny-Dasilva/cycletls_python',
    author='Danny-Dasilva',
    author_email='dannydasilva.solutions@gmail.com',
    project_urls={
        'Bug Reports': 'https://github.com/Danny-Dasilva/cycletls_python/issues',
        'Source': 'https://github.com/Danny-Dasilva/cycletls_python',
        'Documentation': 'https://github.com/Danny-Dasilva/cycletls_python#readme',
    },
)
