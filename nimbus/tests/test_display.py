# -*- coding:utf-8 -*-
import pytest


class Person(object):
    def __init__(self, name, age, gender):
        self.name = name
        self.age = age
        self.gender = gender


def _getTarget():
    from nimbus import MonitoringDisplay
    return MonitoringDisplay


def _makeOne(ob):
    TargetClass = _getTarget()
    from nimbus import display_property, compute

    class PersonDisplay(TargetClass):
        name = display_property("name", label="Name",
                                href=compute(lambda name: "http://example.com/person/{}".format(name)))
        age = display_property("age", label="Age")
        gender = display_property("gender", label="Gender", mapping=humanize)  # xxx:
    return PersonDisplay(ob)


def humanize(v):
    return "Female"  # xxx:


def test_property_is_cached():
    person = Person("foo", 20, "F")
    target = _makeOne(person)

    assert target.name == target.name


def test_property_has_label():
    person = Person("foo", 20, "F")
    target = _makeOne(person)

    assert target.name.label == "Name"


def test_property_has_raw_value():
    person = Person("foo", 20, "F")
    target = _makeOne(person)

    assert target.gender.raw_value == "F"


def test_property_has_mapped_value():
    # mapping F => Female
    person = Person("foo", 20, "F")
    target = _makeOne(person)

    assert target.gender.value == "Female"


def test_property_can_have_lazy_caluculate_value():
    # compute href=compute(lambda name: "http://example.com/person/{}".format(name)))
    person = Person("foo", 20, "F")
    target = _makeOne(person)
    assert target.name.href == "http://example.com/person/foo"


def test_display_can__inject_data__after_initialized():
    person = Person("foo", 20, "F")
    target = _makeOne(person)

    with pytest.raises(AttributeError):
        target.name.error

    target.inject("error", {"name": "booo"})
    assert target.name.error == "booo"


#  parent-child relation

def test_parent_child_relation():
    from nimbus import display_property

    person = Person("foo", 20, "F")
    target = _makeOne(person)

    PersonDisplay = target.__class__

    class Pair(object):
        def __init__(self, left, right):
            self.left = left
            self.right = right

    class PairDisplay(_getTarget()):
        left = display_property("left", label="Left", mapping=PersonDisplay)
        right = display_property("right", label="Right", mapping=PersonDisplay)

    pair_display = PairDisplay(Pair(person, person))
    assert pair_display.left.value.name.value == target.name.value
    assert pair_display.left.value.name.label == target.name.label


#  parent-children relation


def test_parent_children_relation():
    from nimbus import display_property, list_display

    person = Person("foo", 20, "F")
    target = _makeOne(person)

    PersonDisplay = target.__class__

    class Team(object):
        def __init__(self, members):
            self.members = members

    class TeamDisplay(_getTarget()):
        members = display_property("members", label="Members", mapping=list_display(PersonDisplay))

    team_display = TeamDisplay(Team([person, person]))
    assert team_display.members.value[1] != team_display.members.value[0]
    assert team_display.members.value[0].name.value == target.name.value
    assert team_display.members.value[1].name.value == target.name.value
