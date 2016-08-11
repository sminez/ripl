'''
Common LISPy / Haskelly functions to use inside RIPL

Look at using https://github.com/pytoolz/toolz to help with this!

Std Lib Functional stufffd
https://docs.python.org/3.4/library/itertools.html
https://docs.python.org/3.4/library/functools.html
https://docs.python.org/3.4/library/operator.html
'''
import functools
import itertools
import operator as op


def reverse(itr):
    '''Reverse an iterable'''
    return itr[::-1]


def product(*itr):
    '''Find the product of an iterable'''
    return functools.reduce(op.mul, itr)


def foldl(func, acc, lst):
    '''Fold a list with a given binary function from the left'''
    return functools.reduce(func, lst, acc)


def foldr(func, acc, lst):
    '''Fold a list with a given binary function from the right'''
    return functools.reduce(func, lst[::-1], acc)


def scanl(func, acc, lst):
    '''
    Use a given accumulator value to build a list of values obtained
    by repeatedly applying acc = func(acc, next(list)) from the left.
    '''
    list_with_acc = [acc] + lst
    return itertools.accumulate(list_with_acc, func)


def scanr(func, acc, lst):
    '''
    Use a given accumulator value to build a list of values obtained
    by repeatedly applying acc = func(acc, next(list)) from the left.
    '''
    list_with_acc = [acc] + lst[::-1]
    return itertools.accumulate(list_with_acc, func)


def dropWhile(predicate, lst):
    '''
    The predicate needs to take a single argument and return a bool.
    (dropWhile ~(< 3) '(1 2 3 4 5)) -> '(3 4 5)
    '''
    return itertools.dropwhile(predicate, lst)


def takeWhile(predicate, lst):
    '''
    The predicate needs to take a single argument and return a bool.
    (takeWhile ~(< 3) '(1 2 3 4 5)) -> '(1 2)
    '''
    return itertools.takewhile(predicate, lst)
