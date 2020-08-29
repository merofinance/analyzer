from setuptools import setup


setup(
    name="miru",
    packages=["miru"],
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
