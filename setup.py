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
    Determine which platform-specific binary to include in the package.
    """
    system = platform.system()
    machine = platform.machine().lower()

    # Map architecture names
    if machine in ("x86_64", "amd64"):
        arch = "amd64"
    elif machine in ("aarch64", "arm64"):
        arch = "arm64"
    else:
        arch = machine

    # Determine binary name
    if system == "Linux":
        binary = f"dist/cycletls-linux-{arch}"
    elif system == "Darwin":  # macOS
        binary = f"dist/cycletls-darwin-{arch}"
    elif system == "Windows":
        binary = f"dist/cycletls-windows-{arch}.exe"
    else:
        # Fallback - include all binaries
        return ['dist/*']

    # Check if the platform-specific binary exists
    if os.path.exists(os.path.join(HERE, binary)):
        return [binary]
    else:
        # Fallback - include all binaries if specific one doesn't exist
        return ['dist/*']


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
        'pydantic>=1.8.0',
        'websocket-client>=1.0.0',
        'psutil>=5.8.0',
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
