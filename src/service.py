#!/usr/bin/python

import sys
import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
import gobject
import augeas
from pprint import pprint

BUS_NAME = "org.augeasproject.Augeas"
BUS_PATH = "/org/augeasproject/Augeas"

DBusGMainLoop(set_as_default=True)

class Test(object):
    def get(self, path):
        import augeas
        print "Called"
        print path
        return augeas.augeas().get(path)

class DBusFactory(object):
    name = BUS_NAME

    def __init__(self, name, leaf="/Service"):
        path = "/" + name.replace(".", "/")
        self.path = path
        self.name = name

    def service_factory(self, method):
        path = self.path
        name = self.name
        leaf = "/Service"

        class Service(dbus.service.Object):
            def __init__(self):
                bus = dbus.service.BusName(name, bus=dbus.SessionBus())
                path = "/" + name.replace(".", "/")
                dbus.service.Object.__init__(self, bus, leaf)

            def closure(self, path):
                return method(path)

            closure.__name__ = method.__name__
            dbus.service.method(name)(closure)

        return Service()

if __name__ == "__main__":
    print sys.argv
    if "-d" in sys.argv:
        DBusGMainLoop(set_as_default=True)
        loop = gobject.MainLoop()
        print "listening ..."
        d = DBusFactory(BUS_NAME)
        x = d.service_factory(Test().get)
        loop.run()

    elif "-c" in sys.argv:
        bus = dbus.SessionBus()
        obj = bus.get_object(BUS_NAME, "/Service")
        helloservice = dbus.Interface(obj, "org.augeasproject.Augeas")
        print helloservice.closure("/files/etc/hostname/hostname")

