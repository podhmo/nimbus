# -*- coding:utf-8 -*-
import logging
logger = logging.getLogger(__name__)
import weakref
from collections import namedtuple

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


class reify(object):
    def __init__(self, wrapped):
        self.wrapped = wrapped
        try:
            self.__doc__ = wrapped.__doc__
        except:  # pragma: no cover
            pass

    def __get__(self, inst, objtype=None):
        if inst is None:
            return self
        val = self.wrapped(inst)
        setattr(inst, self.wrapped.__name__, val)
        return val


marker = object()
compute = namedtuple("compute", "fn")


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
        try:
            return self.refs[subject]
        except KeyError:
            v = self.refs[subject] = self.field_factory(subject, self.name, self.options.copy())
            return v


display_property = DisplayPropertyFactory(DisplayField)


class Display(object):
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


###
class Person(object):
    def __init__(self, name, age, gender):
        self.name = name
        self.age = age
        self.gender = gender


def humanize(v):
    return "Female"  # xxx:


@as_display(Person)
class PersonDisplay(Display):
    name = display_property("name", label="Name",
                            href=compute(lambda name: "http://example.com/person/{}".format(name)))
    age = display_property("age", label="Age")
    gender = display_property("gender", label="Gender", mapping=humanize)  # xxx:


class Pair(object):
    def __init__(self, left, right):
        self.left = left
        self.right = right


@as_display(Pair)
class PairDisplay(Display):
    left = display_property("left", label="Left", mapping=get_display_class(Person))
    right = display_property("right", label="Right", mapping=get_display_class(Person))


class Team(object):
    def __init__(self, members):
        self.members = members


@as_display(Team)
class TeamDisplay(Display):
    children = display_property("members", label="Members", mapping=lambda v: [PersonDisplay(p) for p in v])


person = Person("foo", 20, "F")
pd = get_display(person)

assert id(pd.name) == id(pd.name)
assert pd.name.label == "Name"
assert pd.name.raw_value == "foo"
assert pd.age.value == 20
assert pd.name.href == "http://example.com/person/foo"

for f in pd:
    print(f.value)


pd.inject("error", {"name": "booo"})
print(pd.name.error)

print("---")

pair = Pair(person, person)
paird = get_display(pair)
print(paird.left.label)
print(paird.left.value.name.value)


print("---")

team = Team([person, person, person])
teamd = get_display(team)
for p in teamd.children.value:
    print(p)


def serialize_json(display):
    return _serialize_json(display, {})


def _serialize_json(display, D):
    for f in display:
        v = f.value
        if isinstance(v, (list, tuple)):
            D[f._name] = [_serialize_json(e, {}) for e in v]
        elif isinstance(v, Display):
            D[f._name] = _serialize_json(v, {})
        else:
            D[f._name] = v
    return D

print(serialize_json(teamd))
print(serialize_json(paird))
