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
import re
from decorator import decorator
from ovirt.node.utils.console import TransactionProgress


class ConfigDefaultsWrapper(object):
    """
    A class which steps through classes in the same format as
    config.defaults classes. Namely, we want to export methods which
    start with configure, and we want to make sure the transaction
    is run when they're triggered.

    Run through the list and dynamically add them to this class
    inside closures

    >>> class Dummy(object):
    ...     def configure(self):
    ...         pass
    ...     def configure_extra(self):
    ...         pass
    ...     def dontexport(self):
    ...         pass
    >>> c = ConfigDefaultsWrapper(Dummy)
    >>> [getattr(c, func).__name__ for func in dir(c) if
    ...     func.startswith("configure")]
    ['configure', 'configure_extra']
    """

    def __init__(self, cls):
        self.cls = cls
        self.__name__ = cls.__name__
        self.populate()
        self.instance = cls()

    def dbus_unwrapper(self, arg):
        """
        Convert Dbus types into something ovirt.node.valid can deal
        with. config.defaults seems to be fine on its own, but better
        safe than sorry with types

        >>> class Dummy(object):
        ...     pass
        >>> c = ConfigDefaultsWrapper(Dummy)
        >>> c.dbus_unwrapper(dbus.String("test"))
        u'test'
        >>> c.dbus_unwrapper(dbus.Int32(12345))
        12345
        >>> c.dbus_unwrapper(dbus.Boolean(False))
        False
        >>> c.dbus_unwrapper(dbus.Array([dbus.Int32(123), dbus.String("x")]))
        [123, u'x']
        """
        if type(arg) is dbus.String:
            return "%s" % arg
        if type(arg) is dbus.Array:
            return [self.dbus_unwrapper(x) for x in arg]
        if type(arg) is dbus.Int32:
            return int(arg)
        if type(arg) is dbus.Boolean:
            return bool(arg)
        else:
            return arg

    def populate(self):
        funcs = [getattr(self.cls, func) for func in dir(self.cls) if
                 func.startswith("configure")]

        for func in funcs:
            # Run in another closure so the transaction can be triggered
            # in one go from dbus. Also, use decorate.decorate again so
            # we keep the original argspec and dbus-python is happy
            @decorator
            def dec(func, *args, **kwargs):
                unwrapped_args = [self.dbus_unwrapper(arg) for arg in args]
                args = unwrapped_args
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

    >>> from ovirt.node.utils import Transaction
    >>> class StepA(Transaction.Element):
    ...     title = "StepA"
    ...     def commit(self):
    ...         pass
    >>> class StepB(Transaction.Element):
    ...     title = "StepB"
    ...     def commit(self):
    ...         pass
    >>> t = Transaction("Doctest", [StepA(), StepB()])
    >>> print TransactionWrapper(t, is_dry=False).run()
    Doctest
    -------
    Checking pre-conditions ...
    (1/2) StepA
    (2/2) StepB
    All changes were applied successfully.
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
            self.texts = [re.sub(r'\n', '', x) for x in self.texts]
            return "\n".join(filter(bool, self.texts))
        else:
            self.update("There were no changes, nothing to do.")

    def __print_title(self):
        self.texts.extend([self.transaction.title,
                           "-" * len(self.transaction.title)])
