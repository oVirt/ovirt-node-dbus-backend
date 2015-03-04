#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# log.py - Copyright (C) 2015 Red Hat, Inc.
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
import logging
import logging.config
"""
Logging for the oVirt Node Dbus Backend. Since we're running from
systemd, send default messages there and let journald handle it. Debug
goes in /tmp if we're running in debug mode.
"""

DEBUG_LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s %(message)s'
        }
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.StreamHandler'
        },
        'debug': {
            'level': 'DEBUG',
            'formatter': 'standard',
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': '/tmp/ovirt-node-dbus.debug.log'
        }
    },
    'loggers': {
        '': {
            'handlers': ['console', 'debug'],
            'level': 'DEBUG',
            'propagate': False
            }
    }
}

LOGGING = DEBUG_LOGGING.copy()
LOGGING.update({
    'handlers': {
        'console': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.StreamHandler'
        }
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False
        }
    }
})


def configure_logging(debug=False):
    log_config = DEBUG_LOGGING if debug else LOGGING
    logging.config.dictConfig(log_config)


def getLogger(name=None):
    if not getLogger._logger:
        if not logging.getLogger().handlers:
            configure_logging()
        getLogger._logger = logging.getLogger()
    fullname = ".".join([getLogger._logger.name, name]) if name else name
    return logging.getLogger(fullname)
getLogger._logger = None
