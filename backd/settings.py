import os
from os import path
import inspect


def _is_test():
    stack = inspect.stack()
    return any(x[0].f_globals["__name__"].startswith("_pytest.") for x in stack)


def _get_backd_env():
    if "BACKD_ENV" in os.environ:
        return os.environ["BACKD_ENV"]
    if _is_test():
        return "test"
    return "development"


def _get_database_url():
    default_url = "mongodb://localhost:27017/backd-data"
    if BACKD_ENV == "test":
        default_url = "mongodb://localhost:27017/backd-test"
    return os.environ.get("DATABASE_URL", default_url)

BACKD_ENV = _get_backd_env()

DATABASE_URL = _get_database_url()

PROJECT_ROOT = path.dirname(path.dirname(__file__))
