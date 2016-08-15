'''
Common LISPy / Haskelly functions to use inside RIPL

The aim of this is to enable crazyness like the following:
def fiblist():
   """generate an infinite list of fibonacci numbers beginning [1,2,3,5...]"""
   yield 1
   next_fibs = scanl(op.add, 2, fiblist())
   while True:
       yield from next_fibs

take(10, fiblist()) --> [1,2,3,5,8,13,21,34,55,89]


Std Lib Functional stuff
https://docs.python.org/3.4/library/itertools.html
https://docs.python.org/3.4/library/functools.html
https://docs.python.org/3.4/library/operator.html
'''
import functools
import itertools
import operator as op


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
    ''' :: f(a, a) -> a, Itr[a] -> a
    Fold a list with a given binary function from the left
    '''
    return functools.reduce(func, [c for c in cont], acc)


def foldr(func, acc, cont):
    ''' :: f(a, a) -> a, Itr|Gen[a] -> a
    Fold a list with a given binary function from the right
    '''
    return functools.reduce(func, [c for c in cont][::-1], acc)


def scanl(func, acc, cont):
    ''' :: f(a, a) -> a, Itr|Gen[a] -> Gen[a]
    Use a given accumulator value to build a list of values obtained
    by repeatedly applying acc = func(acc, next(list)) from the left.
    '''
    yield acc
    while True:
        try:
            c = next(cont)
            acc = func(acc, c)
            yield acc
        except TypeError:
            cont = iter(cont)
        except StopIteration:
            raise StopIteration


def scanr(func, acc, itr):
    ''' :: f(a, a) -> a, Itr[a] -> [a]
    Use a given accumulator value to build a list of values obtained
    by repeatedly applying acc = func(acc, next(list)) from the left.
    '''
    list_with_acc = [acc] + itr[::-1]
    return itertools.accumulate(list_with_acc, func)


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
    return [elem for elem in gen]
