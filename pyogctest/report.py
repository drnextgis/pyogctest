# -*- coding: utf-8 -*-
import xml.etree.ElementTree as ET

from .logger import Logger


class Test(object):

    def __init__(self):
        self.name = ""
        self.assertion = ""
        self.result = ""
        self.exception = ""

class Report(object):

    def __init__(self, xml, duration):
        self.xml = xml
        self.duration = duration
        self._parse()

    def dump(self, mode=""):
        n = len(self.tree)
        Logger.log("collected {} items".format(n), bold=True)
        Logger.log("")

        others = []
        data_independent = []
        basic = []
        queryable = []
        recommendations = []
        data_preconditions = []

        for t in self.tree:
            names = []
            for e in t:
                name, prefix, path, result, assertion, exception = self._info(e)
                names.append(name)

            name, prefix, path, result, assertion, exception = self._info(t[0])
            names.reverse()

            test = Test()
            test.assertion = assertion
            test.result = result
            test.exception = exception

            if "data-independent" in names:
                test.name = '.'.join(names[1:])
                data_independent.append(test)
            elif "basic" in names:
                test.name = '.'.join(names[1:])
                basic.append(test)
            elif "queryable" in names:
                test.name = '.'.join(names[1:])
                queryable.append(test)

            elif "recommendations" in names:
                test.name = '.'.join(names[1:])
                recommendations.append(test)
            elif "data-preconditions" in names:
                test.name = '.'.join(names[1:])
                data_preconditions.append(test)
            else:
                test.name = '.'.join(names)
                others.append(test)

        failures = []
        failures += self._dump(data_preconditions, "data-preconditions")
        failures += self._dump(data_independent, "data-independent")
        failures += self._dump(basic, "basic")
        failures += self._dump(recommendations, "recommendations")
        failures += self._dump(queryable, "queryable")

        if others:
            failures += self._dump(others, "main")

        Logger.log("")
        if not failures:
            msg = " {} passed in {} seconds ".format(n, self.duration)
            Logger.log(msg, color=Logger.Symbol.OK, center=True, symbol="=")
        else:
            Logger.log(" FAILURES ", center=True, symbol="=")

            for failure in failures:
                name = " {} ".format(failure.name)
                Logger.log(name, color=Logger.Symbol.FAIL, center=True, symbol='_')
                Logger.log("")

                Logger.log("Assertion: {}".format(failure.assertion))
                Logger.log("")

                Logger.log("Error: {}".format(failure.exception))
                Logger.log("")

    def _dump(self, tests, name):
        failures = []
        results = ""
        for test in tests:
            if test.result == "1":
                results = results + Logger.Symbol.OK + "." + Logger.Symbol.ENDC
            else:
                results = results + Logger.Symbol.FAIL + "F" + Logger.Symbol.ENDC
                failures.append(test)
        print("{} {}".format(name, results))

        return failures

    def _parse(self):

        root = ET.fromstring(self.xml)

        tree = []
        for child in root:
            if not self._has_child(child):
                tree.append(self._fathers(root, child, [child]))

        self.tree = tree

    def _fathers(self, root, node, fathers):
        father = self._father(root, node)

        if father:
            fathers.append(father)
            fathers = self._fathers(root, father, fathers)

        return fathers

    def _path(self, node):
        path = None
        for child in node:
            if child.tag == "starttest":
                path = child.attrib["path"]
        return path

    def _father(self, root, node):
        path = self._father_path(node)
        for child in root:
            if self._path(child) == path:
                return child
        return None

    def _father_path(self, node):
        path = self._path(node)
        if path:
            return '/'.join(path.split("/")[:-1])
        return None

    def _has_child(self, node):
        for child in node:
            if child.tag == "testcall":
                return True
        return False

    def _info(self, node):
        name = ""
        prefix = ""
        path = ""
        result = ""
        exception = ""

        for child in node:
            if child.tag == "starttest":
                name = child.attrib["local-name"]
                prefix = child.attrib["prefix"]
                path = child.attrib["path"]

                for cc in child:
                    if cc.tag == "assertion":
                        assertion = cc.text

            if child.tag == "endtest":
                result = child.attrib["result"]

            if child.tag == "exception":
                exception = child.text
            if child.tag == "message":
                exception = child.text.replace("Error: ", "")

        return name, prefix, path, result, assertion, exception
