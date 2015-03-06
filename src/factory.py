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
import dbus.service
from decorator import decorator
import logging
import types


class DBusFactory(object):
    """
    Generate dbus objects from python classes which are passed in.
    Take the interface as input, but generate the paths dynamically
    from method and class names

    Pass in an instance of the base class if it's a wrapped class
    """
    def __init__(self, name, cls, instance=None):
        self.cls = cls
        self.name = name
        self.instance = instance or cls()
        self.logger = logging.getLogger(__name__)

    def service_factory(self):
        """
        Introspect a class passed in and wrap it. We assume that
        the method needs "self" as the first argument, since static or
        standalone methods would not need to be passed into a factory
        to easily get on dbus
        """

        cls = self.cls
        instance = self.instance

        name = self.name
        path = "/" + name.replace(".", "/")
        leaf = "%s/%s" % (path, cls.__name__)
        logger = self.logger

        self.logger.debug("Factory started for %s" % self.cls.__name__)

        class Service(dbus.service.Object):
            def __init__(self):
                try:
                    bus = dbus.service.BusName(name, bus=dbus.SystemBus())
                    dbus.service.Object.__init__(self, bus, leaf)
                except dbus.exceptions.DBusException as e:
                    import sys
                    import traceback
                    logger.error("Something went wrong starting dbus or "
                                 "acquiring a handle to the system bus. "
                                 "Have the dbus policies been changed? ")
                    logger.error(traceback.format_exc())
                    sys.exit(1)

            def instance_method(obj):
                """
                Checks if an object is a bound method
                """
                if not isinstance(obj, types.MethodType):
                    # Not a method
                    return False
                if issubclass(obj.im_class, type) or isinstance(
                        obj.im_class, types.ClassType):
                    # Method is a classmethod
                    return False
                return True

            def methods(cls_iter=self):
                """
                Loop over whatever class is passed in and get a list of all
                the methods which start with configure, then return them
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
                # If it's unwrapped, pull out and bind the function so it can
                # be exported
                if instance_method(method):
                    method = method.im_func
                    method.im_class = method.__class__

                # In order to get the right name on the bus on EL7 and later
                # distros, re-set the name, and add it to the class, because
                # decorator parsing order needs it to be realized at
                # instantiation, and we can't dynamically add them afterwards
                # and have them show up
                closed = closure(method)(method)
                closed.__name__ = method.__name__
                setattr(self, method.__name__, closed)

            for method in methods():
                logger.debug("Found a function named %s" %
                             method.func_name)

                # Add to local variables so we can export it but still do
                # some metaprogramming, like resetting the class name, which
                # we can't do without referencing it directly
                locals()[method.__name__] = method
                locals()[method.__name__].im_class = instance.__class__
                logger.info("Exporting %s on %s: %s" % (method.__name__,
                            leaf, name))
                dbus.service.method(name)(locals()[method.__name__])

        return Service()
