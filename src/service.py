#!/usr/bin/python

import sys
import dbus
from dbus.mainloop.glib import DBusGMainLoop
import gobject
from testers import Unwrapped, Test
from factory import DBusFactory
from wrappers import ConfigDefaultsWrapper

BUS_NAME = "org.ovirt.node"
BUS_PATH = "/org.ovirt.node"

DBusGMainLoop(set_as_default=True)

if __name__ == "__main__":
    print sys.argv
    if "-d" in sys.argv:
        DBusGMainLoop(set_as_default=True)
        loop = gobject.MainLoop()
        print "listening ..."
        if "--test" in sys.argv:
            c = ConfigDefaultsWrapper(Test)
            d = DBusFactory(BUS_NAME, c, instance=c.instance)
            d.service_factory()
            p = DBusFactory(BUS_NAME, Unwrapped)
            p.service_factory()
        loop.run()

    elif "-c" in sys.argv and "--test" in sys.argv:
        bus = dbus.SystemBus()
        obj = bus.get_object(BUS_NAME, "/org/ovirt/node/Test")
        helloservice = dbus.Interface(obj, "org.ovirt.node")
        print helloservice.configure_one("/files/etc/hostname/hostname")
        print helloservice.configure_multi(1, 2)
        print helloservice.configure_arr(["1", "2"])
        obj = bus.get_object(BUS_NAME, "/org/ovirt/node/Unwrapped")
        unwrapped = dbus.Interface(obj, "org.ovirt.node")
        unwrapped.configure("/files/etc/resolv.conf/nameserver[1]")
        print unwrapped.configure_return()
