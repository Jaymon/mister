# Mister

For all your medium data needs!

Mister attempts to make running a map/reduce job approachable.

When you've got data that isn't really big and so you're not quite ready to distribute the data across a gazillian machines and stuff but would still like an answer in a reasonable amount of time.

## 5 minute getting started

Mister needs you to define three methods: `prepare` (get the data ready to be run across multiple processes), `map` (actually do something with the chunks of data from `prepare`), and `reduce` (mash all the values returned from `map` together).


### The `reduce` method

```python
prepare(self, count, *args, **kwargs)
```

The `count` is the number of processes the job will be run across, and `*args` and `**kwargs` is whatever is passed into your child class's `__init__` method. The `prepare` method returns __count__ rows containing a tuple `((), {})` of the arguments that will be passed to each `map` process.


### The `map` method

```python
map(self, *args, **kwargs)
```

The `*args` and `**kwargs` are whatever was returned from `prepare`. The `map` method returns whatever you want `reduce` to use to merge all the data together.


### The `reduce` method

```python
reduce(self, output, value)
```

The `output` is the global aggregation of all the `value` arguments the `reduce` method has seen. Basically, whatever you return from one `reduce` call will be passed back into the next `reduce` call as `output`. The `value` argument is whatever the recently finished `map` call returned.

### Bringing it all together

So let's bring it all together in our `MrHelloWorld` job, first let's get the skeleton in place:

```python
from mister import BaseMister


class MrHelloWorld(BaseMister):
	def prepare(self, count, *args, **kwargs): pass
	def map(self, *args, **kwargs): pass
	def reduce(self, output, value): pass
```

Now let's flesh out the `prepare` method:

```python
def prepare(self, count, name):
	# we're just going to return the number and the name we pass in 
	for x in range(count):
	    yield ([x, name], {})
```

And our `map` method:

```python
def map(self, x, name):
	return "Process {} says 'hello {}'".format(x, name)
```

Finally, our `reduce` method:

```python
def reduce(self, output, value):
	if output is None:
		output = []
	output.append(value)
	return output
```

Running our job:

```python
mr = MrHelloWorld("Alice")
output = mr.run()
print(output)
```

will result in:

```
[
	"Process 1 says 'hello Alice'",
	"Process 0 says 'hello Alice'",
	"Process 2 says 'hello Alice'",
	"Process 3 says 'hello Alice'",
	"Process 4 says 'hello Alice'",
	"Process 5 says 'hello Alice'",
	"Process 6 says 'hello Alice'",
	"Process 7 says 'hello Alice'",
	"Process 8 says 'hello Alice'",
	"Process 9 says 'hello Alice'",
	"Process 10 says 'hello Alice'"
]
```

Congrats, you just ran a map/reduce job, you are now an AI and a ML engineer, remember me when you're famous!


## Another Example

I think word counting is the traditional map/reduce example? So here it is:

```python
import os
import re
improt math
from collections import Counter

from mister import BaseMister


class MrWordCount(BaseMister):
    def prepare(self, count, path):
        """prepare segments the data for the map() method"""
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
        """all the magic happens right here"""
        output = Counter()
        with open(path) as fp:
            fp.seek(start, 0)
            words = fp.read(length)

        # I don't compensate for word boundaries because example
        for word in re.split(r"\s+", words):
            output[word] += 1
        return output

    def reduce(self, output, count):
        """take all the return values from map() and aggregate them to the final value"""
        if not output:
            output = Counter()
        output.update(count)
        return output
        
# let's count the bible
path = "./testdata/bible-kjv.txt"
mr = MrWordCount(path)
wordcounts = mr.run()
print(wordcounts.most_common(10))
```

On my computer, the asynchronous code above runs about 3x faster than its syncronous equivalent below:

```python
import re
from collections import Counter

path = "./testdata/bible-kjv.txt"

output = Counter()
with open(path) as fp:
    words = fp.read()

for word in re.split(r"\s+", words):
    output[word] += 1

print(wordcounts.most_common(10))
```

## Installation

To install, use Pip:

	$ pip install mister
	
Or, to grab the latest and greatest:

	$ pip install --upgrade git+https://github.com/Jaymon/mister#egg=mister

