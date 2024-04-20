from pathlib import Path
from setuptools import (setup,
                        find_packages)

PARENT_DIR = Path(__file__).parent
README_FILE = (PARENT_DIR / "README.md").read_text()

setup(
    name="biodbs",
    version="0.0.1",
    description="bioDBs is a Python package for getting data from biological databases.",
    long_description=README_FILE,
    long_description_content_type="text/markdown",
    url="https://github.com/qwerty239qwe/biodbs",
    author="qwerty239qwe",
    author_email="qwerty239qwe@gmail.com",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
    ],
    packages=find_packages(exclude=()),
    include_package_data=True,
    install_requires=["pandas",
                      "tqdm",
                      "aiohttp",
                      "requests",
                      "beautifulsoup4",
                      "defusedxml"],
    entry_points={},
)