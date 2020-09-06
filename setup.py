from setuptools import setup


setup(
    name="backd",
    packages=["backd"],
    install_requires=[
        "pymongo",
        "stringcase",
        "smart-open",
    ],
    extras_require={
        "dev": [
            "pylint",
            "ipython",
            "jupyter",
            "pytest",
        ]
    },
    entry_points = {
        "console_scripts": ["backd=backd.cli:run"],
    }
)
