"""Setup script for the Loggamera integration."""
from setuptools import setup, find_packages

setup(
    name="loggamera",
    version="0.1.0",
    description="Home Assistant integration for Loggamera",
    url="https://github.com/YourUsername/ha-loggamera-integration",
    author="YourName",
    author_email="your.email@example.com",
    license="MIT",
    packages=find_packages(),
    install_requires=[
        "homeassistant>=2023.1.0",
        "requests>=2.25.0",
    ],
    zip_safe=False,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)