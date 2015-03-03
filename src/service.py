#!/usr/bin/python

import sys
import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
import gobject

BUS_NAME = "org.ovirt.node"
BUS_PATH = "/org.ovirt.node"

DBusGMainLoop(set_as_default=True)


class Test(object):
    """
    A class which mimics the basic structure and modules used by
    normal ovirt.node.config.defaults classes so the functionality
    can be easily tested
    """

    def get(self, path):
        import augeas
        print "Called"
        print path
        return augeas.augeas().get(path)

    def configure(self, path):
        self.output = self.get(path)

    def transaction(self):
        print "Running transaction"
        return self.output


class DBusFactory(object):
    """
    Generate dbus objects from python classes which are passed in.
    Take the interface as input, but generate the paths dynamically
    from method and class names
    """
    name = BUS_NAME

    def __init__(self, name):
        path = "/" + name.replace(".", "/")
        self.path = path
        self.name = name

    def service_factory(self, method):
        """
        Introspect a method passed in and wrap it. We assume that
        the method needs "self" as the first argument, since static or
        standalone methods would not need to be passed into a factory
        to easily get on dbus
        """

        path = self.path
        name = self.name
        leaf = "%s/%s/%s" % (path, method.im_class.__name__,
                             method.__name__)

        class Service(dbus.service.Object):
            def __init__(self):
                bus = dbus.service.BusName(name, bus=dbus.SystemBus())
                dbus.service.Object.__init__(self, bus, leaf)

            def closure(self, path):
                return method(method.im_class(), path)

            # In order to get the right name on the bus on EL7 and later
            # distros, re-set the name, and create a local variable with the
            # same name, so dbus's decorator can infer it
            closure.__name__ = method.__name__
            locals()[method.__name__] = closure
            print "Exporting %s" % method.__name__
            dbus.service.method(name, in_signature="s")(
                locals()[method.__name__])

        return Service()


class ConfigDefaultsParser(object):
    """
    A class which steps through classes in the same format as
    config.defaults classes. Namely, we want to export methods which
    start with configure, and we want to make sure the transaction
    is run when they're triggered.
    """

    def __init__(self, cls):
        self._cls = cls

    @property
    def methods(self):
        funcs = [getattr(self._cls, func) for func in dir(self._cls) if
                 func.startswith("configure")]

        wrapped_funcs = []
        for func in funcs:
            # Run in another closure so the transaction can be triggered
            # in one go from dbus
            def wrapped(cls, x):
                func(cls, x)
                return cls.transaction()

            # Pass in the real attributes make the wrapper transparent
            wrapped.im_class = func.im_class
            wrapped.__name__ = func.__name__
            wrapped_funcs.append(wrapped)
        return wrapped_funcs

if __name__ == "__main__":
    print sys.argv
    if "-d" in sys.argv:
        DBusGMainLoop(set_as_default=True)
        loop = gobject.MainLoop()
        print "listening ..."
        d = DBusFactory(BUS_NAME)
        c = ConfigDefaultsParser(Test)
        [d.service_factory(x) for x in c.methods]
        loop.run()

    elif "-c" in sys.argv:
        bus = dbus.SystemBus()
        obj = bus.get_object(BUS_NAME, "/org/ovirt/node/Test/configure")
        helloservice = dbus.Interface(obj, "org.ovirt.node")
        print helloservice.configure("/files/etc/hostname/hostname")
        print helloservice.configure("/files/etc/resolv.conf/nameserver[1]")
