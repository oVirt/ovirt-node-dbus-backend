#!/usr/bin/python

import sys
import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
import gobject
import augeas
from pprint import pprint

BUS_NAME = "org.ovirt.node"
BUS_PATH = "/org.ovirt.node"

DBusGMainLoop(set_as_default=True)


class Test(object):
    def get(self, path):
        import augeas
        print "Called"
        print path
        return augeas.augeas().get(path)

    def configure(self, path):
        return self.get(path)

    def transaction(self):
        print "Running transaction"


class DBusFactory(object):
    name = BUS_NAME

    def __init__(self, name):
        path = "/" + name.replace(".", "/")
        self.path = path
        self.name = name

    def service_factory(self, method):
        path = self.path
        name = self.name
        leaf = "/org/ovirt/node/%s/%s" % (method.im_class.__name__,
                                          method.__name__)

        class Service(dbus.service.Object):
            def __init__(self):
                bus = dbus.service.BusName(name, bus=dbus.SystemBus())
                path = "/" + name.replace(".", "/")
                dbus.service.Object.__init__(self, bus, leaf)

            def closure(self, path):
                return method(method.im_class(), path)

            closure.__name__ = method.__name__
            locals()[method.__name__] = closure
            print "Exporting %s" % method.__name__
            dbus.service.method(name, in_signature="s")(
                locals()[method.__name__])

        return Service()

class ClassParser(object):

    def __init__(self, cls):
        self._cls = cls

    @property
    def methods(self):
       funcs = [getattr(self._cls, func) for func in dir(self._cls) if
                func.startswith("configure")]
       return funcs

if __name__ == "__main__":
    print sys.argv
    if "-d" in sys.argv:
        DBusGMainLoop(set_as_default=True)
        loop = gobject.MainLoop()
        print "listening ..."
        d = DBusFactory(BUS_NAME)
        c = ClassParser(Test)
        [d.service_factory(x) for x in c.methods]
        loop.run()

    elif "-c" in sys.argv:
        bus = dbus.SystemBus()
        obj = bus.get_object(BUS_NAME, "/org/ovirt/node/Test/configure")
        helloservice = dbus.Interface(obj, "org.ovirt.node")
        print helloservice.configure("/files/etc/hostname/hostname")
        print helloservice.configure("/files/etc/resolv.conf/nameserver[1]")
