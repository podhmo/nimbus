# -*- coding:utf-8 -*-
import logging
logger = logging.getLogger(__name__)
from nimbus import (
    get_display_class,
    get_display,
    as_display,
    MonitoringDisplay,
    display_property,
    compute,
    list_display,
    serialize_json
)


class Person(object):
    def __init__(self, name, age, gender):
        self.name = name
        self.age = age
        self.gender = gender


def humanize(v):
    return "Female"  # xxx:


@as_display(Person)
class PersonDisplay(MonitoringDisplay):
    name = display_property("name", label="Name",
                            href=compute(lambda name: "http://example.com/person/{}".format(name)))
    age = display_property("age", label="Age")
    gender = display_property("gender", label="Gender", mapping=humanize)  # xxx:


class Pair(object):
    def __init__(self, left, right):
        self.left = left
        self.right = right


@as_display(Pair)
class PairDisplay(MonitoringDisplay):
    left = display_property("left", label="Left", mapping=get_display_class(Person))
    right = display_property("right", label="Right", mapping=get_display_class(Person))


class Team(object):
    def __init__(self, members):
        self.members = members


@as_display(Team)
class TeamDisplay(MonitoringDisplay):
    member = display_property("members", label="Members", mapping=list_display(PersonDisplay))


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
for p in teamd.member.value:
    print(p)


print(serialize_json(teamd))
print(serialize_json(paird))


class Foo(object):
    def __init__(self, name, boo):
        self.name = name
        self.boo = boo


class Boo(object):
    def __init__(self, name):
        self.name = name


class FooDisplay(MonitoringDisplay):
    foo_name = display_property("name", label="FooName")
    boo_name = display_property("boo.name", label="BooName")

foo = Foo("foo", Boo("boo"))
foo_display = FooDisplay(foo)
print("Label={} name={}".format(foo_display.foo_name.label,
                                foo_display.foo_name.value))  # => Label=FooName name=foo
print("Label={} name={}".format(foo_display.boo_name.label,
                                foo_display.boo_name.value))  # => Label=BooName name=boo
