#!/usr/bin/python
import augeas

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
        print "Running transaction"
        return self.output
