# -*- coding:utf-8 -*-
import re
from . import Invalid
from . import logger


class Validation(object):
    def __init__(self, fn, message="invalid", exception=Exception):
        self.fn = fn
        self.msg = message
        self.exc = exception

    def message(self, message):
        return self.__class__(self.fn, message)

    def __call__(self, v):
        try:
            return self.fn(v)
        except self.exc as e:
            logger.debug(e)
            msg = self.msg
            if callable(msg):
                msg = msg(v)
            raise Invalid(msg)


class And(Validation):
    def __call__(self, v):
        fns = self.fn
        for fn in fns:
            v = fn(v)
        return v


class Or(Validation):
    def __call__(self, v):
        fns = self.fn
        excs = []
        for fn in fns:
            try:
                v = fn(v)
                return v
            except Invalid as e:
                excs.append(e)
        if excs:
            raise excs[0]
        return v


def Regex(rx):
    rx = re.compile(rx)

    def match(x):
        if rx.search(x):
            return x
        raise Exception("")
    return Validation(match)


def Condition(fn):
    def match(x):
        if not fn(x):
            raise Invalid("failure")
        return x
    return Validation(match)


def OneOf(candidates):
    cached = [None]

    def match(x):
        if cached[0] is None:
            if callable(candidates):
                cached[0] = candidates()
            else:
                cached[0] = candidates

        assert x in cached[0]
        return x
    return Validation(match)


def AnyOf(candidates):
    cached = [None]

    def match(xs):
        if cached[0] is None:
            if callable(candidates):
                cached[0] = candidates()
            else:
                cached[0] = candidates
        assert any(e in cached[0] for e in xs)
        return xs
    return Validation(match)


def AllOf(candidates):
    cached = [None]

    def match(xs):
        if cached[0] is None:
            if callable(candidates):
                cached[0] = candidates()
            else:
                cached[0] = candidates
        assert all(e in cached[0] for e in xs)
        return xs
    return Validation(match)

Min = Condition(lambda limit: lambda v: limit >= v)
Max = Condition(lambda limit: lambda v: limit <= v)
Length = Condition(lambda left, right: lambda v: left <= v <= right)
