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
from decorator import decorator
import logging
from ovirt.node.utils.console import TransactionProgress
from ovirt.node.utils import Transaction

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
                def dbus_unwrapper(arg):
                    if type(arg) is dbus.String:
                        return "%s" % arg
                    else:
                        return arg
                wrapped_args = [dbus_unwrapper(arg) for arg in args]
                args = wrapped_args
                func(*args)
                return TransactionWrapper(self.instance.transaction(),
                                          is_dry=False).run()

            # Pass in the real attributes make the wrapper transparent
            wrapped = dec(func.im_func)
            wrapped.im_class = self.cls
            wrapped.__name__ = func.__name__
            setattr(self, func.__name__, wrapped)


class TransactionWrapper(TransactionProgress):
    """
    Run a transaction inside Dbus. Return the output as a string
    """

    def __init__(self, transaction, is_dry, initial_text=""):
        super(TransactionWrapper, self).__init__(transaction, is_dry,
                                                 initial_text)
    def _print_func(self, txt):
        pass

    def run(self):
        if self.transaction:
            self.logger.debug("Initiating transaction")
            super(TransactionWrapper, self).run_transaction()
            return "\n".join(self.texts)
        else:
            self.update("There were no changes, nothing to do.")

    def __print_title(self):
        self.texts.extend([self.transaction.title,
                           "-" * len(self.transaction.title)])
