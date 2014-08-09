# -*- coding:utf-8 -*-
import logging
logger = logging.getLogger(__name__)
import weakref
from collections import namedtuple
from .langhelpers import reify

_display_repository = {}


def get_display(ob):
    return _display_repository[ob.__class__](ob)


def get_display_class(cls):
    return _display_repository[cls]


def as_display(src):
    def _wrap(dst):
        _display_repository[src] = dst
        return dst
    return _wrap

marker = object()
compute = namedtuple("compute", "fn")


class _Null(object):
    def __nonzero__(self):
        return False

    def __bool__(self):
        return False
null = _Null()


class Invalid(Exception):
    pass


class DisplayField(object):
    def __init__(self, subject, _name, options):
        self.subject = subject
        self._name = _name
        self._options = options

    def __getattr__(self, name):
        v = self._options.get(name, marker)
        if v is marker:
            raise AttributeError(name)

        if isinstance(v, compute):
            v = v.fn(self.raw_value)
        setattr(self, name, v)
        return v

    @reify
    def raw_value(self):
        return getattr(self.subject, self._name)

    @reify
    def value(self):
        if hasattr(self, "mapping"):
            return self.mapping(self.raw_value)
        return self.raw_value

    def __repr__(self):
        return "<DisplayField name={name!r} at 0x{id:x}>".format(name=self._name, id=id(self))


class DisplayPropertyFactory(object):
    def __init__(self, field_factory=DisplayField):
        self.field_factory = field_factory
        self.count = 0

    def __call__(self, name, **options):
        self.count += 1
        return DisplayProperty(name, self.count, self.field_factory, options)


class DisplayProperty(object):
    def __init__(self, name, c, field_factory, options):
        self.name = name
        self.c = c
        self.field_factory = field_factory
        self.options = options
        self.refs = weakref.WeakKeyDictionary()

    def __get__(self, instance, type=None):
        subject = instance.subject
        if "." in self.name:
            names = self.name.split(".")
            for k in names[:-1]:
                subject = getattr(subject, k)
            name = names[-1]
        else:
            name = self.name
        try:
            return self.refs[subject]
        except KeyError:
            v = self.refs[subject] = self.field_factory(subject, name, self.options.copy())
            return v


class MonitoringDisplay(object):
    def __init__(self, subject):
        self.subject = subject

    def __iter__(self):
        self.configure()
        for name in self._fields:
            yield getattr(self, name)

    def configure(self):
        cls = self.__class__
        if not hasattr(cls, "_fields"):
            names = []
            for k, v in self.__class__.__dict__.items():
                if isinstance(v, DisplayProperty):
                    names.append((v.c, k))
            cls._fields = [xs[1] for xs in list(sorted(names, key=lambda xs: xs[0]))]

    def inject(self, attrname, params, default=None):
        for f in self:
            setattr(f, attrname, params.get(f._name, default))


def list_display(display_cls):
    def _list_display(xs):
        return [display_cls(x) for x in xs]
    return _list_display


class Field(object):
    def __init__(self, subject, name, options):
        self.subject = subject
        self.name = name
        self._options = options

    def __getattr__(self, name):
        v = self._options.get(name, marker)
        if v is marker:
            raise AttributeError(name)

        if isinstance(v, compute):
            v = v.fn(self.raw_value)
        setattr(self, name, v)
        return v

    @property
    def raw_value(self):
        try:
            return self.subject[self.name]
        except KeyError:
            v = getattr(self, "initial", null)
            if v is null and self.required:
                raise
            self.subject[self.name] = v
            return v

    @reify
    def value(self):
        if hasattr(self, "mapping"):
            return self.mapping(self.raw_value)
        return self.raw_value

    @reify
    def validated(self):
        if hasattr(self.value, "validate"):
            self.value.validate()
            self.errors.extend(self.value.errors)
            return self.raw_value
        try:
            v = self.validation(self.raw_value)
            if v is None:
                return self.raw_value
            return v
        except Invalid as e:
            self.errors.append(e.args[0])
            return self.raw_value

    @reify
    def errors(self):
        return []

    def __repr__(self):
        return "<Field name={name!r} at 0x{id:x}>".format(name=self.name, id=id(self))


class FieldPropertyFactory(object):
    def __init__(self, field_factory=Field):
        self.field_factory = field_factory
        self.count = 0

    def __call__(self, name, validation, required=True, **options):
        self.count += 1
        options["validation"] = validation
        options["required"] = required
        return DisplayProperty(name, self.count, self.field_factory, options)


class WrappedParamaters(object):
    def __init__(self, params):
        self.params = params
        self.wrapping = {}

    def __getitem__(self, k):
        return self.params.get(k, null) or self.wrapping[k]

    def __setitem__(self, k, v):
        self.wrapping[k] = v


class ValidatableDisplay(object):
    def __init__(self, subject=None):
        self.subject = WrappedParamaters(subject or {})

    def __iter__(self):
        self._configure()
        for name in self._fields:
            yield getattr(self, name)

    def _configure(self):
        cls = self.__class__
        if not hasattr(cls, "_fields"):
            names = []
            for k, v in self.__class__.__dict__.items():
                if isinstance(v, DisplayProperty):
                    names.append((v.c, k))
            cls._fields = [xs[1] for xs in list(sorted(names, key=lambda xs: xs[0]))]

    def inject(self, attrname, params, default=None):
        for f in self:
            setattr(f, attrname, params.get(f.name, default))

    def validate(self):
        for f in self:
            f.validated
        return not self.errors

    def validated_data(self):
        if self.validate():
            return {f.name: f.validated for f in self}
        else:
            raise Invalid(self)

    @property
    def errors(self):
        return [e for f in self for e in f.errors]

display_property = DisplayPropertyFactory(DisplayField)
field_property = FieldPropertyFactory(Field)


def serialize_json(display):
    return _serialize_json(display, {})


def _serialize_json(display, D):
    for f in display:
        v = f.value
        if isinstance(v, (list, tuple)):
            D[f._name] = [_serialize_json(e, {}) for e in v]
        elif isinstance(v, MonitoringDisplay):
            D[f._name] = _serialize_json(v, {})
        else:
            D[f._name] = v
    return D
