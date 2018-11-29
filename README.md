# Mister

For all your medium data needs!

When you've got data that isn't really big and so you're not quite ready to distribute the data across a gazillian machines and stuff but would still like an answer in a reasonable amount of time.

Mister attempts to make running a map/reduce job approachable.


## Example

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
