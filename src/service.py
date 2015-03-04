#!/usr/bin/python

import sys
import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
import gobject
from decorator import decorator

BUS_NAME = "org.ovirt.node"
BUS_PATH = "/org.ovirt.node"

DBusGMainLoop(set_as_default=True)


class Test(object):
    """
    A class which mimics the basic structure and modules used by
    normal ovirt.node.config.defaults classes so the functionality
    can be easily tested
    """

    output = "Not run yet"

    def get(self, path):
        import augeas
        print "Called"
        print path
        return augeas.augeas().get(path)

    def configure_one(self, path):
        self.output = self.get(path)

    def configure_multi(self, a, b):
        self.output = "%s, %s" % (a, b)

    def configure_arr(self, x):
        self.output = "%s" % x

    def transaction(self):
        print "Running transaction"
        return self.output


class DBusFactory(object):
    """
    Generate dbus objects from python classes which are passed in.
    Take the interface as input, but generate the paths dynamically
    from method and class names

    Pass in an instance of the base class if it's a wrapped class
    """
    name = BUS_NAME

    def __init__(self, name, cls, instance=None):
        self.cls = cls
        self.name = name
        self.instance = instance or cls

    def service_factory(self):
        """
        Introspect a class passed in and wrap it. We assume that
        the method needs "self" as the first argument, since static or
        standalone methods would not need to be passed into a factory
        to easily get on dbus
        """

        name = self.name
        cls = self.cls
        instance = self.instance

        class Service(dbus.service.Object):
            def __init__(self):
                path = "/" + name.replace(".", "/")
                leaf = "%s/%s" % (path, cls.__name__)
                bus = dbus.service.BusName(name, bus=dbus.SystemBus())
                dbus.service.Object.__init__(self, bus, leaf)

            def methods(cls_iter=self):
                """
                Loop over whatever class is passed in and get a list of all
                the methods which start with configur, then return them
                """
                funcs = [getattr(cls_iter, func) for func in dir(cls_iter) if
                         func.startswith("configure")]
                return funcs

            # Because dbus-python doesn't like to export functions with varargs
            # we need to create
            def closure(method):
                # Use the decorator here because it preserves the argspec,
                # and dbus-python doesn't deal with varargs very well unless
                # we do this
                @decorator
                def dec(func, *args, **kwargs):
                    # Sub out self if it isn't right. Mostly being a wrapped
                    # class
                    if not isinstance(args[0], method.im_class):
                        args_list = list(args)
                        args_list[0] = self.instance
                        args = args_list
                    return func(*args)
                return dec

            for method in methods(self.cls):
                # In order to get the right name on the bus on EL7 and later
                # distros, re-set the name, and add it to the class, because
                # decorator parsing order needs it to be realized at
                # instantiation, and we can't dynamically add them afterwards
                # and have them show up
                closed = closure(method)(method)
                closed.__name__ = method.__name__
                setattr(self, method.__name__, closed)

            for method in methods():
                # Add to local variables so we can export it but still do
                # some metaprogramming, like resetting the class name, which
                # we can't do without referencing it directly
                locals()[method.__name__] = method
                locals()[method.__name__].im_class = instance.__class__
                print "Exporting %s on %s" % (method.__name__, name)
                dbus.service.method(name)(locals()[method.__name__])

        return Service()


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
            # in one go from dbus
            def wrapper(cls):
                @decorator
                def dec(func, *args, **kwargs):
                    func(*args)
                    return self.instance.transaction()
                return dec

            # Pass in the real attributes make the wrapper transparent
            wrapped = wrapper(self.cls)(func.im_func)
            wrapped.im_class = self.cls
            wrapped.__name__ = func.__name__
            setattr(self, func.__name__, wrapped)


if __name__ == "__main__":
    print sys.argv
    if "-d" in sys.argv:
        DBusGMainLoop(set_as_default=True)
        loop = gobject.MainLoop()
        print "listening ..."
        c = ConfigDefaultsWrapper(Test)
        d = DBusFactory(BUS_NAME, c, instance=c.instance)
        d.service_factory()
        loop.run()

    elif "-c" in sys.argv:
        bus = dbus.SystemBus()
        obj = bus.get_object(BUS_NAME, "/org/ovirt/node/Test")
        helloservice = dbus.Interface(obj, "org.ovirt.node")
        print helloservice.configure_one("/files/etc/hostname/hostname")
        print helloservice.configure_one("/files/etc/resolv.conf/nameserver[1]"
                                         )
        print helloservice.configure_multi(1, 2)
        print helloservice.configure_arr([1, 2])
