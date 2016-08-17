'''
Common LISPy / Haskelly functions to use inside RIPL

The aim of this is to enable crazyness like the following:
    def fiblist():
       """
       Generate an infinite list of fibonacci numbers beginning [1,2,3,5...]
       """
       yield 1
       next_fibs = scanl(op.add, 2, fiblist())
       while True:
           yield from next_fibs

    take(10, fiblist()) --> [1,2,3,5,8,13,21,34,55,89]
    NOTE: This seems to bottom out at take(1976, fiblist()) on my machine...!


Std Lib Functional stuff:
https://docs.python.org/3.4/library/itertools.html
https://docs.python.org/3.4/library/functools.html
https://docs.python.org/3.4/library/operator.html

Some info on what haskell does:
https://wiki.haskell.org/Fold
http://learnyouahaskell.com/higher-order-functions

Clojure's core reference:
https://clojuredocs.org/clojure.core
https://clojuredocs.org/quickref
'''
import functools
import itertools
import operator as op
from collections import Generator

from .bases import RList


def reverse(itr):
    ''' :: Itr[*T] -> Itr[*T]
    Reverse an iterable
    '''
    return itr[::-1]


def product(cont):
    ''' :: Itr|Gen[a] -> a
    Find the product of an iterable. Contents of the iterable must
    implement __mul__
    '''
    return functools.reduce(op.mul, cont)


def foldl(func, acc, cont):
    ''' :: f(a, a) -> a, Itr|Gen[a] -> a
    Fold a list with a given binary function from the left
    '''
    for val in cont:
        acc = func(acc, val)
    return acc


def foldr(func, acc, cont):
    ''' :: f(a, a) -> a, Itr|Gen[a] -> a
    Fold a list with a given binary function from the right

    WARNING: Right folds and scans will blow up for
             infinite generators!
    '''
    if isinstance(cont, Generator):
        # Convert to iterator to pass to reduce
        cont = [c for c in cont]

    for val in cont[::-1]:
        acc = func(val, acc)
    return acc


def scanl(func, acc, cont):
    ''' :: f(a, a) -> a, Itr|Gen[a] -> List[a]
    Use a given accumulator value to build a list of values obtained
    by repeatedly applying acc = func(acc, next(list)) from the left.
    '''
    # yield acc
    # for val in cont:
    #     acc = func(acc, val)
    #     yield acc
    lst = [acc]
    for val in cont:
        acc = func(acc, val)
        lst.append(acc)
    return lst


def scanr(func, acc, cont):
    ''' :: f(a, a) -> a, Itr|Gen[a] -> List[a]
    Use a given accumulator value to build a list of values obtained
    by repeatedly applying acc = func(next(list), acc) from the right.

    WARNING: Right folds and scans will blow up for
             infinite generators!
    '''
    if isinstance(cont, Generator):
        # Convert to iterator to pass to reduce
        cont = [c for c in cont]

    # yield acc
    # for val in cont:
    #     acc = func(val, acc)
    #     yield acc
    lst = [acc]
    for val in cont[::-1]:
        acc = func(val, acc)
        lst.append(acc)
    return lst


def take(num, cont):
    ''' :: Int, Itr|Gen[*T] -> List[*T]
    Return up to the first `num` elements of an iterable or generator.
    '''
    try:
        return cont[:num]
    except TypeError:
        # Taking from a generator
        num_items = []
        for n in range(num):
            num_items.append(next(cont))
        return num_items


def drop(num, cont):
    ''' :: Int, Itr|Gen[*T] -> List[*T]
    Return everything but the first `num` elements of itr
    '''
    try:
        items = cont[num:]
    except TypeError:
        items = []
        for n in range(num):
            # Fetch and drop the initial elements
            try:
                items.append(next(cont))
            except StopIteration:
                break
    return items


def dropWhile(predicate, container):
    ''' :: Int, Itr|Gen[*T] -> Gen[*T]
    The predicate needs to take a single argument and return a bool.
    (dropWhile ~(< 3) '(1 2 3 4 5)) -> '(3 4 5)
    '''
    return itertools.dropwhile(predicate, container)


def takeWhile(predicate, container):
    ''' :: Int, Itr|Gen[*T] -> Gen[*T]
    The predicate needs to take a single argument and return a bool.
    (takeWhile ~(< 3) '(1 2 3 4 5)) -> '(1 2)
    '''
    return itertools.takewhile(predicate, container)


def flatten(lst):
    ''' :: Itr|Gen[*T] -> List[*T]
    Flatten an arbitrarily nested list of lists down to a single list
    '''
    _list = ([x] if not isinstance(x, list) else flatten(x) for x in lst)
    return sum(_list, [])


def drain(gen):
    ''' :: Gen[*T] -> List[*T]
    Given a generator, convert it to a list.
    '''
    return RList([elem for elem in gen])
