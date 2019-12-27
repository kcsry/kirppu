# -*- coding: utf-8 -*-
import decimal
import typing
from django.db import models

from .interpreter import Error, ErrorType, Literal, LiteralList


def make_env():
    return {
        ".count": _count,
        ".filter": _filter,
        ".sumBy": _sum_by,
        ".aggregate": _aggregate,
    }


_FILTER_MAP = {
    "<": "lt",
    ">": "gt",
    "<=": "lte",
    ">=": "gte",
}
_FILTER_FIELDS = {
    "kirppu.models.Item": {"price", }
}


def _validate_filter_field(source: models.QuerySet, field: str, func: str = ".filter") -> str:
    model_fields = _FILTER_FIELDS.get(source.model.__module__ + "." + source.model.__name__)
    if model_fields is None:
        raise Error("Invalid model given for %s" % func, ErrorType.FILTER_MODEL)
    if field not in model_fields:
        raise Error("Invalid field %s given for %s" % (field, func), ErrorType.FILTER_FIELD)
    return field


def _make_filter_dict(op: str, lhs: str, rhs) -> typing.Tuple[typing.Dict[str, typing.Any], bool]:
    op_name = _FILTER_MAP.get(op)
    if op_name is not None:
        return {lhs + "__" + op_name: rhs}, True
    if op == "=":
        return {lhs: rhs}, True
    if op == "!":  # XXX: Nonstandard operator.
        return {lhs: rhs}, False
    raise Error("Unexpected filter operator: %s" % type(op), ErrorType.FILTER_OP)


def _filter(source, condition: LiteralList) -> models.QuerySet:
    if not isinstance(source, models.QuerySet):
        raise Error("Expected a query for first .filter argument, got %s" % type(source), ErrorType.FILTER_QUERY)
    if not isinstance(condition, LiteralList):
        raise Error("Expected a literal filter expression for second .filter argument, got %s" % type(condition),
                    ErrorType.FILTER_EXPR)
    op, lhs, rhs = condition
    lhs = _validate_filter_field(source, lhs)

    if not isinstance(rhs, decimal.Decimal):
        # TODO: This might be a dereference of a variable, when unquote is implemented.
        raise Error("Expected a literal value for third position in .filter condition argument, got %s" % type(rhs),
                    ErrorType.FILTER_OP)

    filter_dict, is_filter = _make_filter_dict(op, lhs, rhs)
    if is_filter:
        return source.filter(**filter_dict)
    else:
        return source.exclude(**filter_dict)


def _sum_by(aggregate: Literal, source) -> typing.Union[decimal.Decimal, int]:
    if not isinstance(aggregate, Literal):
        raise Error("Expected a literal for first .sumBy argument, got %s" % type(aggregate), ErrorType.SUM_BY_LITERAL)
    if not isinstance(source, models.QuerySet):
        raise Error("Expected a query for second .sumBy argument, got %s" % type(source), ErrorType.SUM_BY_QUERY)

    return source.aggregate(result=models.Sum(aggregate))["result"] or 0


def _count(source) -> int:
    if not isinstance(source, models.QuerySet):
        raise Error("Expected a query for first .count argument, got %s" % type(source), ErrorType.COUNT_QUERY)
    return source.count()


def _aggregate(source, mapping: LiteralList) -> dict:
    if not isinstance(source, models.QuerySet):
        raise Error("Expected a query for first .aggregate argument, got %s" % type(source), ErrorType.AGGREGATE_QUERY)

    aggregate_results = {}
    for index, a_mapping in enumerate(mapping, start=1):
        if len(a_mapping) < 3:
            raise Error("Too short association definition for .aggregate in index %d" % index,
                        ErrorType.AGGREGATE_DEFINITION)
        name, function, rest = a_mapping

        if function == "count":
            if len(rest) == 0:
                aggregate_results[name] = models.Count('id')
            else:
                if len(rest) != 3:
                    raise Error("Too %s arguments given for aggregation filter in index %d" % (
                        "few" if len(rest) < 3 else "many", index), ErrorType.AGGREGATE_DEFINITION)
                field = _validate_filter_field(source, rest[1], func=".aggregate")
                fdict, positive = _make_filter_dict(rest[0], field, rest[2])
                f = models.Q(**fdict)
                aggregate_results[name] = models.Count('id', filter=f if positive else ~f)
        else:
            raise Error("Invalid aggregate function %s for %s" % (function, name), ErrorType.AGGREGATE_DEFINITION)
    if aggregate_results:
        return source.aggregate(**aggregate_results)
    else:
        return {}
