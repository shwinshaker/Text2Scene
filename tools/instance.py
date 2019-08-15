#!./env python

from collections import defaultdict

class Node:
    def __init__(self, t, attr, count=1):
        self.t = t
        self.attr = attr
        self.count = count
        self.neighbors = defaultdict(lambda: defaultdict(Node))

    def __str__(self):
        return '%s(%s)' % (self.t, self.attr)

    def __eq__(self, other):
        """
        must implement this to support comparation between nodes
        """
        if not isinstance(other, Node):
            raise TypeError((other, type(other)))
        return self.t == other.t and self.attr == other.attr

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        return self.t < other.t or (self.t == other.t and self.attr < other.attr)

    def __hash__(self):
        """
        need to explicitly implement hash function to make it hashable if __eq__ is implemented
        seems to recommend xor.
           see. https://stackoverflow.com/questions/4005318/how-to-implement-a-good-hash-function-in-python
                https://stackoverflow.com/questions/2909106/whats-a-correct-and-good-way-to-implement-hash
        """
        return hash((self.t, self.attr))

    def __repr__(self):
        return self.__str__()


