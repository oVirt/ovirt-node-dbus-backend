This package provides a python-dbus provider which accepts arbitrary classes and creates objects to access configuration data over dbus.

Classes will be populated on the bus with an interface of "org.ovirt.node.class".

A systemd unit file is provided along with a small startup script which will automatically add anything from ovirt.node.config.defaults with a method name which starts with configure\*

Logging is provided via journald
