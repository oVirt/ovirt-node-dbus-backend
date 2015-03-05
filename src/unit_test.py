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

from dbus.mainloop.glib import DBusGMainLoop
#import dbusmock
import mock
import unittest
from testers import Unwrapped
from factory import DBusFactory

DBusGMainLoop(set_as_default=True)


class TestFactory(dbusmock.DBusTestCase):
    @classmethod
    def setUpClass(cls):
        cls.start_system_bus()
        cls.dbus_con = cls.get_dbus(system_bus=True)

    def setUp(self):
        self.p_mock = self.spawn_server('org.ovirt.node',
                                        '/org/ovirt/node',
                                        'org.ovirt.node',
                                        system_bus=True)

    @mock.patch('augeas.Augeas.get')
    def test_unwrapped_augeas_no_dbus(self, mock_augeas):
        mock_augeas.return_value = "test_value"
        instance = DBusFactory("org.ovirt.node", Unwrapped,
                               bus=self.dbus_con)
        instance.service_factory()
        instance.configure(instance, "x")
        self.assertEqual(instance.configure_return(instance),
                         "test_value")

if __name__ == "__main__":
    unittest.main(testRunner=unittest.TextTestRunner())
