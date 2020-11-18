from setuptools import setup

setup(
    name="backd",
    packages=["backd"],
    install_requires=[
        "pymongo",
        "stringcase",
        "smart-open",
        "tqdm",
        "matplotlib",
        "pandas",
        "python-dotenv",
        "ethereum-tools",
        "rusty-rlp",
    ],
    extras_require={
        "dev": [
            "pylint",
            "black",
            "pytest-profiling",
            "ipython",
            "jupyter",
            "pytest",
            "web3",
        ]
    },
    entry_points={
        "console_scripts": ["backd=backd.cli:run"],
    },
)
