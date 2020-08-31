from functools import lru_cache


class classproperty(object):
    def __init__(self, fget):
        self.fget = fget

    def __get__(self, owner_self, owner_cls):
        return self.fget(owner_cls)


class BaseFactory:
    @classproperty
    @lru_cache()
    def _entities(cls):
        return {}

    @classmethod
    def registered(cls):
        return list(cls._entities.keys())

    @classmethod
    def register(cls, name: str):
        """decorator to register a class to the factory
        Should be used as follows:

        .. code:: python
            @FactorySubClass.register("name")
            class SubClassImpl:
                pass

        :param name: name with which the entity should be accessed
        """
        def wrapper(klass):
            cls._entities[name] = klass
            klass.__registered_name__ = name
            return klass
        return wrapper

    @classmethod
    def get(cls, name: str):
        """gets an entity from the factory by named

        :param name: name of the entity
        :return: the entity class
        :raise ValueError: if the entity does not exist
        """
        if name not in cls._entities:
            raise ValueError("{0} not registered".format(name))
        return cls._entities[name]

    @classmethod
    def create(cls, name: str, *args, **kwargs):
        """creates an entity

        :param name: name of the entity
        :return: the entity instance
        """
        return cls.get(name)(*args, **kwargs)
