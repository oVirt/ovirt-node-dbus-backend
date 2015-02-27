#!/usr/bin/python

import sys
import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
import gobject

DBusGMainLoop(set_as_default=True)

class DBusBackend(dbus.service.Object):
    name = None
    path = None

    def __init__(self, name, leaf="/Service"):
        bus = dbus.SessionBus()
        uid = dbus.service.BusName(name, bus=bus)
        path = "/" + name.replace(".", "/")
        dbus.service.Object.__init__(self, uid, leaf)
        self.path = path
        self.name = name
