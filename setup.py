from setuptools import setup


setup(
    name="backd",
    packages=["backd"],
    install_requires=[
        "pymongo",
        "stringcase",
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
