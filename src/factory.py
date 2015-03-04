import dbus
import dbus.service
from decorator import decorator
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

    def service_factory(self):
        """
        Introspect a class passed in and wrap it. We assume that
        the method needs "self" as the first argument, since static or
        standalone methods would not need to be passed into a factory
        to easily get on dbus
        """

        name = self.name
        cls = self.cls
        instance = self.instance

        class Service(dbus.service.Object):
            def __init__(self):
                path = "/" + name.replace(".", "/")
                leaf = "%s/%s" % (path, cls.__name__)
                bus = dbus.service.BusName(name, bus=dbus.SystemBus())
                dbus.service.Object.__init__(self, bus, leaf)

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
                the methods which start with configur, then return them
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
                # Add to local variables so we can export it but still do
                # some metaprogramming, like resetting the class name, which
                # we can't do without referencing it directly
                locals()[method.__name__] = method
                locals()[method.__name__].im_class = instance.__class__
                print "Exporting %s on %s" % (method.__name__, name)
                dbus.service.method(name)(locals()[method.__name__])

        return Service()
