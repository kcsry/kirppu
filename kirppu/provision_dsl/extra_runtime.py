# -*- coding: utf-8 -*-
from .interpreter import Error, ErrorType, Literal


def make_env():
    return {
        "assoc": _assoc,
    }


def _assoc(key: Literal, assoc_map: dict):
    if not isinstance(assoc_map, dict):
        raise Error("Invalid association map given for assoc", ErrorType.ASSOC_NOT_ASSOCIATION)
    if key not in assoc_map:
        raise Error("Key %s not defined in given association map" % key, ErrorType.ASSOC_NOT_DEFINED)
    return assoc_map[key]
