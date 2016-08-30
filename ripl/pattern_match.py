'''
An attempt at matching s-expressions in python.
If the match is successful it will return a dict
mapping the pattern variables to the values they
matched against.

So far, simple patterns work:
    (a b c d) -> (1 2 3 4)         == match
    (a b c) -> (1 2 3 4)           == failure
    (a b (c d)) -> (1 2 (3 4))     == match
    (a b c d) -> (1 2 (3 4))       == failure
    ((a b) (c d)) -> ((1 2) (3 4)) == match

*args style `and everything else` also works:
    (a *b) -> (1 2 3 4 5)          == match
    (a *b c) -> (1 2 3 4 5)        == match
    (a *b c d) -> (1 2 3)          == failure
    (a *b *c) -> (1 2 3)           == SyntaxError

Repeating subpatterns work:
    ((a b) ...) -> ((1 2) (3 4))

is a match and gives a -> [1, 3], b -> [2, 4].

This entire concept is based on extending Python Tuple
unpacking and Clojure destructuring:
    http://clojure.org/guides/destructuring
'''
import collections
import collections.abc
from itertools import zip_longest


class Symbol:
    '''
    Internal representation of symbols
    Symbols can be bound to values using (define Symbol Value)
    '''
    def __init__(self, string):
        self.str = string

    def __repr__(self):
        return self.str

    def __hash__(self):
        return hash(self.str)

    def __eq__(self, other):
        if isinstance(other, Symbol):
            return self.str == other.str


class Keyword:
    '''
    Internal representation of Keywords
    Unlike symbols, keywords can only refer to themselves
        i.e. (define :keyword "foo") is a syntax error
    Main intended use is for keys in dicts.
    '''
    def __init__(self, string):
        self.str = string

    def __repr__(self):
        return ':' + self.str

    def __hash__(self):
        return hash(':' + self.str)

    def __eq__(self, other):
        if isinstance(other, Keyword):
            return self.str == other.str
        else:
            return False

    def _keyword_comp(self, other):
        '''Used for when we store something as a keyword internally'''
        if isinstance(other, Keyword):
            return self == other
        elif isinstance(other, Symbol):
            return self.str == other.str
        else:
            return self.str == other


class RList(collections.abc.MutableSequence):
    '''Attempt at a LISP style linked list'''
    def __init__(self, *data):
        if len(data) == 1 and isinstance(data[0], collections.Container):
            # Extract a single arg of a list
            data = data[0]
        if data:
            self.data = collections.deque(data)
        else:
            self.data = collections.deque()

    def __eq__(self, other):
        if not isinstance(other, RList):
            return False
        else:
            return self.data == other.data

    def __iter__(self):
        return iter(self.data)

    def _cons(self, other):
        # Need to reverse otherwise (cons '(1 2) `(3 4)) -> (2 1 3 4)
        try:
            self.data.extendleft(iter(other))
            return self
        except:
            self.data.extendleft([other])
            return self

    def __call__(self, index):
        '''Collections are mappings to values'''
        return self[index]

    def __repr__(self):
        return '(' + ' '.join([str(x) for x in self.data]) + ')'

    def __getitem__(self, key):
        '''Hack slicing onto deques'''
        if isinstance(key, slice):
            start, stop, step = key.start, key.stop, key.step
            start = start if start else 0
            stop = stop if stop else len(self)
            step = step if step else 1
            return RList([self.data[x] for x in range(start, stop, step)])
        else:
            return self.data[key]

    def __delitem__(self, index):
        del self.data[index]

    def __setitem__(self, index, value):
        self.data[index] = value

    def insert(self, index, value):
        self.data.insert(index, value)

    def __len__(self):
        return len(self.data)

    def __add__(self, other):
        new = RList(self.data + other.data)
        return new

###############################################################################


class Unmatched:
    '''Flag for unmatched vars: may want to match against None'''
    greedy = False

    def __repr__(self):
        return '__UNMATCHED__'

    def __eq__(self, other):
        return isinstance(other, Unmatched)


class FailedMatch(Exception):
    pass


class Pvar:
    repeating = False
    '''A pattern variable'''
    def __init__(self, symbol):
        self.symbol = symbol
        self.greedy = True if symbol.str.startswith('*') else False
        if self.greedy:
            self.symbol.str = self.symbol.str.lstrip('*')
        self.value = Unmatched()

    def __repr__(self):
        return str('{} -> {}'.format(self.symbol, self.value))

    def _propagate_match(self, attempt):
        '''make sure repeated vars are the same'''
        existing = attempt.get(self.symbol)
        if existing:
            if isinstance(existing, Unmatched):
                self.symbol = existing
            else:
                if self.value != existing:
                    raise FailedMatch(
                        'Pattern variable already bound: {} != {}'.format(
                            self.value, existing))
        else:
            attempt[self.symbol.str] = self.value

    def __eq__(self, other):
        if isinstance(other, collections.Container):
            # TODO: find a  better way of distinguishing strings
            #       form other container types.
            if not type(other) == str:
                return False

        if type(self.value) == Unmatched:
            if self.greedy:
                self.value = [other]
            else:
                self.value = other
            return True
        else:
            if self.greedy:
                self.value.append(other)
                return True
            else:
                if self.value == other:
                    return True
                else:
                    return False


# class Tvar(Pvar):
#     '''A pvar that also type checks on the value passed'''
#     def __init__(self, symbol, _type):
#         self.symbol = symbol
#         self._type = _type
#         self.value = Unmatched()
        

#     def __eq__(self, other):
#         if eval('isinstance({}, {})'.format(other, self._type)):
#             if type(self.value) == Unmatched:
#                 if self.greedy:
#                     self.value = [other]
#                 else:
#                     self.value = other
#                 return True
#             else: 
#                 if self.greedy:
#                     self.value.append(other)
#                     return True
#                 else:
#                     return False
#         else:
#             return False


class Underscore(Pvar):
    '''Wildcard that matches anything'''
    def __init__(self, greedy=False):
        self.symbol = Symbol('_')
        self.greedy = greedy
        self.value = Unmatched()

    def __eq__(self, other):
        self.value = other
        return True

    def _propagate_match(self, attempt):
        '''discard the match'''
        pass


class Template:
    '''a list of pattern vars'''
    greedy = False

    def __init__(self, *data):
        if len(data) == 1 and isinstance(data[0], collections.Container):
            # Allow a single arg of a list to be passed
            data = data[0]

        pvars = []
        has_star = False
        has_ellipsis = False

        for element in data:
            if isinstance(element, RList):
                # Add a sub-template
                pvars.append(Template(element))
            elif isinstance(element, Symbol):
                # Handle special pattern variables:
                #   Underscores match anything but get discarded
                if element.str == '_':
                    pvars.append(Underscore())
                elif element.str == '*_':
                    # Underscores can be greedy
                    if has_star:
                        raise SyntaxError(
                            'Can only have a maximum of one * per template')
                    else:
                        has_star = True
                    pvars.append(Underscore(greedy=True))
                elif element.str == '...':
                    # Ellipsis makes the previous sub-template greedy
                    if not isinstance(pvars[-1], Template):
                        raise SyntaxError(
                            '... can only be used on a repeating sub template')
                    if has_ellipsis:
                        raise SyntaxError(
                            'Can only have a maximum of one ... per template')
                    else:
                        has_ellipsis = True
                        pvars[-1].repeating = True
                else:
                    # Handle all other pattern variables
                    if element.str.startswith('*'):
                        # Greedy match like Python's tuple unpacking
                        if has_star:
                            raise SyntaxError(
                                'Can only have a max of one * per template')
                        else:
                            has_star = True
                    pvars.append(Pvar(element))
            else:
                # TODO: It should be possible to specify values rather than
                #       symbols. They should only match themselves.
                raise ValueError(element, type(element), ' should be a Symbol')

            if has_star and has_ellipsis:
                raise SyntaxError('Invaild match template')

        # Convert to internal representation and build an empty map to start.
        self.pvars = RList(pvars)
        self.map = dict()
        self.repeating = False

    def __repr__(self):
        # Display current pvars and their bindings
        return str(self.pvars)

    def __eq__(self, other):
        if not isinstance(other, RList):
            raise SyntaxError(
                    "Attempted match against something that isn't a list")
        else:
            pairs = list(zip_longest(self.pvars, other, fillvalue=None))
            for _ in range(len(pairs)):
                pvar, target = pairs.pop(0)
                # Always check regardless of modifiers
                self.check_match(pvar, target)
                
                if pvar.greedy:
                    cached = []
                    next_pvar, next_target = pairs.pop(0)
                    while next_pvar:
                        cached.append(next_pvar)
                        self.check_match(pvar, next_target)
                        next_pvar, next_target = pairs.pop(0)
                    # Everything else is unmatched:
                    # --> match the last one from the while loop first
                    pvar == next_target
                    diff = len(pairs) - len(cached)
                    left_over_pvars = diff * [pvar] + cached
                    left_over_targets = [r[1] for r in pairs]
                    for p, t in zip(left_over_pvars, left_over_targets):
                        self.check_match(p, t)
                    # We've now drained pairs so we are done
                    break
                elif pvar.repeating:
                    # Consume till the end of the list and combine the results
                    values_so_far = {k: [v] for k, v in pvar.map.items()}
                    for _, next_target in pairs:
                        # reset so we can match again
                        for p in pvar.pvars:
                            p.value = Unmatched()
                        pvar == next_target
                        # update the map
                        for p in pvar.pvars:
                            values_so_far[p.symbol.str].append(p.value)
                    # We've now drained pairs so we are done
                    self.map = values_so_far
                    break
                    

            if all([not isinstance(v.value, Unmatched) for v in self.pvars]):
                # horrible hack to get nested templates to work
                self.value = self.pvars
                return self.map
            else:
                raise FailedMatch(self.pvars)

    def check_match(self, pvar, target):
        '''Check for a match and update the current mapping'''
        if pvar == target:
            if isinstance(pvar, Template):
                if pvar.repeating:
                    # Handled in __eq__
                    pass
                else:
                    self.map.update(pvar.map)
            else:
                pvar._propagate_match(self.map)
        else:
            raise FailedMatch(pvar, target)


if __name__ == '__main__':
    # See if all of this works!
    tests = [
        (RList([Symbol(x) for x in 'a *b c d'.split()]),
         RList(1,2,3,4,5,6,7)),
        (RList([Symbol(x) for x in 'a *b _ d'.split()]),
         RList(1,2,3,4,5,6,7)),
        (RList([Symbol(x) for x in 'a *b c *d'.split()]),
         RList(1,2,3,4,5,6,7)),
        (RList([Symbol(x) for x in 'a b c'.split()]),
         RList(1,2,3,4,5,6,7)),
        (RList([Symbol(x) for x in 'a b c'.split()]),
         RList('A', 'B', 'C')),
        (RList([Symbol(x) for x in 'a _ c'.split()]),
         RList('A', 'B', 'C')),
        (RList(Symbol('a'), Symbol('b'), RList(Symbol('c'), Symbol('d'))),
         RList(1, 2, RList(3,4))),
        (RList([Symbol(x) for x in 'a *b c'.split()]),
         RList(1, 2, RList(3,4))),
        (RList([Symbol(x) for x in 'a b *c d'.split()]),
         RList(1,2,3,4,5,6,7)),
        (RList(RList(Symbol('a'), Symbol('b')), Symbol('...')),
         RList(RList(1,2), RList(3,4), RList(5,6)))
        ]

    for tmp, tar in tests:
        print('template: ', tmp)
        print('target: ', tar)
        try:
            T = Template(tmp)
            T == tar
            print('match:', T.map, '\n')
        except FailedMatch as f:
            print('** MATCH FAILED:', f, '**\n')
        except SyntaxError as s:
            print('** INVALID TEMPLATE:', s, '**\n')
