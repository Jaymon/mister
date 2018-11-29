# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import sys
import logging
import time
import math

import multiprocessing
from multiprocessing import queues


__version__ = "0.0.1"


logger = logging.getLogger(__name__)


class Count(int):
    """This wraps the process count value (how many subprocesses the job will have)
    and just makes it a bit easier to chunk up the data, an instance of this will
    be passed into reduce()
    """
    def chunksize(self, n):
        """Turns out I keep doing something like this, basically I have some value
        like 100 and I have count processes that are going to go through the data
        so I need to find out how many rows/pieces to pass to each map method, this
        is what this method does

        :param n: the total size of whatever you are dividing up between all the 
            map callbacks
        :returns: int, basically the value of n / self
        """
        length = int(math.ceil(n / self))
        return length

    def chunks(self, l):
        """If you have a list l this will divide it up into the appropriate chunks
        to pass to the map callback as *args, **kwargs

        :param l: list
        :returns: self tuples of (args, kwargs)
        """
        n = len(l)
        chunksize = self.chunksize(n)
        for i in range(0, n, chunksize):
            yield (l[i:i + chunksize],), {}

    def bounds(self, n, *args, **kwargs):
        """if you have a maximum size n this will chunk up n to self sections of
        start (offset), length (limit)

        :param n: int, the full size of your whatever your data is, this will be
            used to decide the size of the chunks
        :param *args: these will be passed through as the args part of the return
            tuple
        :param **kwargs: these will be copied and "start" and "length" will be added
            representing the start and stop (start + length) section of n
        :returns: generator of (args, kwargs) tuples ready to be passed to map()
        """
        length = self.chunksize(n)
        start = 0
        for x in range(n):
            kw = dict(kwargs)
            kw["start"] = start
            kw["length"] = length
            start += length
            yield args, kw


class BaseMister(object):
    """If you want to subclass this is the class to use, anything you pass into __init__
    will be passed to your child's prepare() method

    https://en.wikipedia.org/wiki/MapReduce
    """
    def __init__(self, *args, **kwargs):
        """create an instance

        :param *args: passed to prepare()
        :param **kwargs: passed to prepare()
        """
        if not getattr(self, "count", 0):
            count = multiprocessing.cpu_count()
            # we subtract one for the main process
            count = count - 1 if count > 1 else 1
            self.count = count

        self.args = () if not args else args
        self.kwargs = {} if not kwargs else kwargs

    def prepare(self, count, *args, **kwargs):
        """Handle chunking the data for the map() method

        :param count: how many processes will work on the data, basically this is
            how many chunks you want the data to split into
        :param *args: the values passed into __init__
        :param **kwargs: the values passed into __init__
        :returns: count iter|list of tuples, basically you want to return count
            tuples in the form of ((), {}) (ie, args, kwargs), the tuple will be
            passed to .map() as *args, **kwargs
        """
        raise NotImplementedError()

    def map(self, *args, **kwargs):
        """this method will be called once for each tuple returned from prepare

        :param *args: The first value of the tuple returned from prepare()
        :param **kwargs: The second value of the tuple returned from prepare()
        :returns: mixed, you can return anything and it will be passed to reduce
        """
        raise NotImplementedError()

    def reduce(self, output, value):
        """This method brings it all together

        :param output: this is aggregate values of everything returned from map, the
            first time this method is called output=None so you will have to initialize
            it and then add value to it however you want to do that
        :param value: mixed, the return value from a call to map()
        :return: output, usually you return output updated however you want, the value
            returned from a call to reduce will be passed into the next call to reduce
            as the output value
        """
        raise NotImplementedError()

    def run(self):
        """run the map/reduce job, this is where all the magic happens

        :returns: mixed, the final output returned from the final call to reduce()
        """
        ret = None
        queue = multiprocessing.JoinableQueue()

        processes = []
        ident = 1
        count = Count(self.count)
        for args, kwargs in self.prepare(count, *self.args, **self.kwargs):
            name = "map-{}".format(ident)

            logger.debug("{} = {}/{}".format(name, ident, count))

            t = Map(
                target=self.map,
                name=name,
                queue=queue,
                args=args,
                kwargs=kwargs
            )
            t.start()
            processes.append(t)
            ident += 1

        output = None
        while processes or not queue.empty():
            try:
                val = queue.get(True, 1.0)
                ret = self.reduce(output, val)
                if ret is not None:
                    output = ret

            except queues.Empty:
                pass

            else:
                queue.task_done()

            # faster than using any((t.is_alive() for t in mts))
            processes = [t for t in processes if t.is_alive()]

        return output


class Mister(BaseMister):
    """Similar to BaseMister but allows you to pass in prepare, map, and reduce as
    callbacks and also set the process count via __init__
    """
    def __init__(self, target_prepare, target_map, target_reduce, count=0, args=None, kwargs=None):
        """create an instance

        :param target_prepare: callback, see the .prepare method
        :param target_map: callback, see the .map method
        :param target_reduce: callback, see the .reduce method
        :param count: int, how many processes you want
        :param args: tuple, passed into target_prepare as *args
        :param kwargs: dict, passed into target_prepare as **kwargs
        """
        self.count = count
        super(Mister, self).__init__(*args, **kwargs)
        if target_prepare:
            self.prepare = target_prepare
        if target_map:
            self.map = target_map
        if target_reduce:
            self.reduce = target_reduce


class Map(multiprocessing.Process):
    """This is a package internal class that handles the actual threading of the
    map method

    https://docs.python.org/3/library/multiprocessing.html
    """
    def __init__(self, target, name, queue, args, kwargs):
        """
        :param target: the map callback
        :param name: the name assigned to this process
        :param queue: multiprocessing.JoinableQueue, the queue used for interprocess
            communication
        :param args: the *args that will be passed to target
        :param kwargs: the **kwargs that will be passed to target
        """

        def wrapper_target(target, queue, args, kwargs):

            is_logged = logger.isEnabledFor(logging.DEBUG)

            if is_logged:
                logger.debug("{} Starting".format(name))
                start = time.time()

            val = target(*args, **kwargs)
            if val is not None:
                try:
                    # queue size taps out at 32767, booooo
                    # http://stackoverflow.com/questions/5900985/multiprocessing-queue-maxsize-limit-is-32767
                    #queue.put_nowait(val)
                    queue.put(val, True, 1.0)

                except queues.Full as e:
                    logger.exception(e)
                    #queue.close()
                    # If we ever hit a full queue you lose a ton of data but if you
                    # don't call this method then the process just hangs
                    queue.cancel_join_thread()

            if is_logged:
                stop = time.time()
                elapsed = round(abs(stop - start) * 1000.0, 1)
                total = "{:.1f} ms".format(elapsed)
                logger.debug("{} finished in {}".format(name, total))

        super(Map, self).__init__(target=wrapper_target, name=name, kwargs={
            "target": target,
            "queue": queue,
            "args": args,
            "kwargs": kwargs
        })

