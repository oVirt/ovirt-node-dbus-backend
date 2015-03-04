from decorator import decorator

class ConfigDefaultsWrapper(object):
    """
    A class which steps through classes in the same format as
    config.defaults classes. Namely, we want to export methods which
    start with configure, and we want to make sure the transaction
    is run when they're triggered.

    Run through the list and dynamically add them to this class
    inside closures
    """

    def __init__(self, cls):
        self.cls = cls
        self.__name__ = cls.__name__
        self.populate()
        self.instance = cls()

    def populate(self):
        funcs = [getattr(self.cls, func) for func in dir(self.cls) if
                 func.startswith("configure")]

        for func in funcs:
            # Run in another closure so the transaction can be triggered
            # in one go from dbus. Also, use decorate.decorate again so
            # we keep the original argspec and dbus-python is happy
            @decorator
            def dec(func, *args, **kwargs):
                func(*args)
                return self.instance.transaction()

            # Pass in the real attributes make the wrapper transparent
            wrapped = dec(func.im_func)
            wrapped.im_class = self.cls
            wrapped.__name__ = func.__name__
            setattr(self, func.__name__, wrapped)
