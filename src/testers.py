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

import augeas
import logging

logger = logging.getLogger(__name__)


class Unwrapped(object):
    """
    A class which mimics possible future design or external Dbus services
    which do not require transactions to be run every time
    """

    output = "Not run yet"

    def configure(self, path):
        self.output = augeas.augeas().get(path)

    def configure_return(self):
        return self.output


class Test(object):
    """
    A class which mimics the basic structure and modules used by
    normal ovirt.node.config.defaults classes so the functionality
    can be easily tested
    """

    output = "Not run yet"

    def get(self, path):
        return augeas.augeas().get(path)

    def configure_one(self, path):
        self.output = self.get(path)

    def configure_multi(self, a, b):
        self.output = "%s, %s" % (a, b)

    def configure_arr(self, x):
        self.output = "%s" % ",".join(i for i in x)

    def transaction(self):
        logger.debug("Running transaction")
        return self.output
