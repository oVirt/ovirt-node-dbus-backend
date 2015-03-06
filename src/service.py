#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# __init__.py - Copyright (C) 2015 Red Hat, Inc.
# Written by Ryan Barry <rbarry@redhat.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA  02110-1301, USA.  A copy of the GNU General Public License is
# also available at http://www.gnu.org/copyleft/gpl.html.


import dbus
from dbus.mainloop.glib import DBusGMainLoop
import gobject
import logging
import sys
from testers import Unwrapped, Wrapped
from factory import DBusFactory
from wrappers import ConfigDefaultsWrapper
import log

logger = None

BUS_NAME = "org.ovirt.node"

DBusGMainLoop(set_as_default=True)

if __name__ == "__main__":
    log.configure_logging(True) if '--debug' in sys.argv else \
        log.configure_logging(False)
    logger = logging.getLogger(__name__)
    if "-d" in sys.argv:
        DBusGMainLoop(set_as_default=True)
        loop = gobject.MainLoop()
        logger.info("listening ...")
        if "--test" in sys.argv:
            c = ConfigDefaultsWrapper(Wrapped)
            d = DBusFactory(BUS_NAME, c, instance=c.instance)
            d.service_factory()
            p = DBusFactory(BUS_NAME, Unwrapped)
            p.service_factory()
        else:
            try:
                from ovirt.node.config import defaults
            except ImportError as e:
                import sys
                logger.error("ovirt.node.config.defaults could not be "
                             "imported. Is ovirt-node-lib-config installed? "
                             "If so, try manually importing it and seeing if "
                             "a dependency is missing")
                sys.exit(1)
            import inspect
            for name, obj in inspect.getmembers(defaults):
                if inspect.isclass(obj) and \
                        issubclass(obj, defaults.NodeConfigFileSection):
                    c = ConfigDefaultsWrapper(obj)
                    d = DBusFactory(BUS_NAME, c, instance=c.instance)
                    d.service_factory()
        loop.run()

    elif "-c" in sys.argv and "--test" in sys.argv:
        bus = dbus.SystemBus()
        obj = bus.get_object(BUS_NAME, "/org/ovirt/node/Wrapped")
        helloservice = dbus.Interface(obj, "org.ovirt.node")
        print helloservice.configure_one("/files/etc/hostname/hostname")
        print helloservice.configure_multi(1, 2)
        print helloservice.configure_arr(["1", "2"])
        obj = bus.get_object(BUS_NAME, "/org/ovirt/node/Unwrapped")
        unwrapped = dbus.Interface(obj, "org.ovirt.node")
        unwrapped.configure("/files/etc/resolv.conf/nameserver[1]")
        print unwrapped.configure_return()
