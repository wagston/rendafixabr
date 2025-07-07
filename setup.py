from setuptools import setup, find_namespace_packages

# Read the contents of your README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements from requirements.txt
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="rendafixabr",
    version="0.1.1",
    author="Wagston Staehler",
    author_email="wagston.staehler@gmail.com",
    description="Funções para coletar dados e gerar análises simples dos títulos públicos brasileiros",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_namespace_packages("src", exclude=["docs", "tests"]),
    package_dir={"": "src"},
    url="https://github.com/wagston/rendafixabr",
    # packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Financial and Insurance Industry",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Office/Business :: Financial",
        "Topic :: Scientific/Engineering :: Information Analysis",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    keywords="finance, brazilian bonds, tesouro direto, bmf, b3, fixed income",
    project_urls={
        "Bug Reports": "https://github.com/wagston/rendafixabr/issues",
        "Source": "https://github.com/wagston/rendafixabr",
        "Documentation": "https://github.com/wagston/rendafixabr#readme",
    },
)
