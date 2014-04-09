class Base(object): pass

class Singleton(object):
	class __metaclass__(type):
		def __call__(cls, *args, **kwargs):
			if not getattr(cls, 'instance', None):
				cls.instance = cls.__new__(cls, *args, **kwargs)
				cls.instance.__init__(*args, **kwargs)
			return cls.instance