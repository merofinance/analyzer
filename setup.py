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
    }
)
