from setuptools import find_packages
from setuptools import setup

long_description: str

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="faapi",
    version="2.2.0",
    author="MatteoCampinoti94",
    author_email="matteo.campinoti94@gmail.com",
    description="Python module to implement API-like functionality for the FurAffinity.net website.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitlab.com/MatteoCampinoti94/FAAPI",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: European Union Public Licence 1.2 (EUPL 1.2)",
        "Development Status :: 5 - Production/Stable"
        "Intended Audience :: Developers",
        "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
    ],
    python_requires='>=3.8',
)
