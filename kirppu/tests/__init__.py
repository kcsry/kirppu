# -*- coding: utf-8 -*-
__author__ = 'codez'


def color(c: int, s: str) -> str:
    return "\x1b[" + str(c) + "m" + str(s) + "\x1b[0m"


class ResultMixin(object):
    # noinspection PyPep8Naming
    def assertSuccess(self, ret):
        self.assertResult(ret, 200)
        return ret

    # noinspection PyPep8Naming
    def assertResult(self, ret, expect=200):
        # noinspection PyUnresolvedReferences
        self.assertEqual(expect, ret.status_code, "Expected {}, got {} / {}".format(
            expect, ret.status_code, ret.content.decode("utf-8")))
        return ret
