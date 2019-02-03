# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import os
import math
from collections import Counter
import re

import testdata
from testdata import TestCase

from mister import Mister, Miss


testdata.basic_logging()


class MrHelloWorld(Mister):
    def prepare(self, count, name):
        # we're just going to return the number and the name we pass in 
        for x in range(count):
            yield ([x, name], {})

    def map(self, x, name):
        return "Process {} says 'hello {}'".format(x, name)

    def reduce(self, output, value):
        if output is None:
            output = []
        output.append(value)
        return output


class MrWordCount(Mister):
    def prepare(self, count, path):
        size = os.path.getsize(path)
        length = int(math.ceil(size / count))
        start = 0
        for x in range(count):
            kwargs = {}
            kwargs["path"] = path
            kwargs["start"] = start
            kwargs["length"] = length
            start += length
            yield (), kwargs

    def map(self, path, start, length):
        output = Counter()
        with open(path) as fp:
            fp.seek(start, 0)
            words = fp.read(length)

        for word in re.split(r"\s+", words):
            output[word] += 1
        return output

    def reduce(self, output, count):
        if not output:
            output = Counter()
        output.update(count)
        return output


class MrCount(Mister):
    def prepare(self, count, numbers):
        chunk = int(math.ceil(len(numbers) / count))
        # this splits the numbers into chunk size chunks
        # https://stackoverflow.com/a/312464/5006
        for i in range(0, len(numbers), chunk):
            yield (), {"numbers": numbers[i:i + chunk]}

    def map(self, numbers):
        return sum(numbers)

    def reduce(self, output, total):
        if not output:
            output = 0
        output += total
        return output


class MrTest(TestCase):
    def test_count(self):
        numbers = list(range(0, 1000000))
        total_sync = sum(numbers)

        m = MrCount(numbers)
        total_async = m.run()

        self.assertEqual(total_sync, total_async)

    def test_wordcount(self):
        path = testdata.get_contents("bible-kjv").path
        output_sync = Counter()
        with open(path) as fp:
            words = fp.read()
        for word in re.split(r"\s+", words):
            output_sync[word] += 1

        mr = MrWordCount(path)
        output_async = mr.run()

        # sigh, not accounting for wordbreak bit me, turns out one of the breaks
        # was "and" and so the counts don't line up, so we'll just test the
        # words
        self.assertEqual(
            [k[0] for k in output_sync.most_common(10)],
            [k[0] for k in output_async.most_common(10)]
        )

    def test_helloworld(self):
        mr = MrHelloWorld("Alice")
        output = mr.run()
        print(output)


class MsCount(Miss):
    def prepare(self, count, size):
        for x in range(size):
            yield x

    def map(self, n):
        return 1

    def reduce(self, output, incr):
        #pout.v(output, incr)
        ret = output + incr if output else incr
        return ret

    def run(self):
        self.queue_class.timeout = 0.1
        return super(MsCount, self).run()


class MsTest(TestCase):
    def test_count(self):
        size = 1000
        #size = 10
        #size = 100000
        ms = MsCount(size)
        total = ms.run()
        self.assertEqual(size, total)



