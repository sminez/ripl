'''
An attempt at matching s-expressions in python.
If the match is successful it will return a dict
mapping the pattern variables to the values they
matched against.

Simple patterns work (an underscore discards the value):
    (a b c d) -> (1 2 3 4)         == a:1, b:2, c:3, d:4
    (_ _ a _) -> (1 2 3 4)         == a:3
    (a b (c d)) -> (1 2 (3 4))     == a:1, b:2, c:3, d:4
    ((a b) (_ d)) -> ((1 2) (3 4)) == a:1, b:2, d:4
    (a b c) -> (1 2 3 4)           == failure
    (a b c d) -> (1 2 (3 4))       == failure

*args style `and everything else` also works:
    (a *b) -> (1 2 3 4 5)          == a:1, b:[2,3,4,5]
    (a *b c) -> (1 2 3 4 5)        == a:1, b:[2,3,4], c:5
    (a *b c d) -> (1 2 3)          == failure
    (a *b *c) -> (1 2 3)           == SyntaxError

Repeating subpatterns work:
    ((a b) ...) -> ((1 2) (3 4))   == a:[1, 3], b:[2, 4]
    (x y (a b) ...)
            -> (5 6 (1 2) (3 4))   == x:5, y:6, a:[1, 3], b:[2, 4]

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
        if isinstance(other, Keyword, Symbol):
            return self.str == other.str
        else:
            return self.str == other


###############################################################################


def non_string_collection(x):
    '''Allow distinguishing between string types and containers'''
    if isinstance(x, collections.Container):
        if not isinstance(x, (str, bytes)):
            return True
    return False


class FailedMatch(Exception):
    __slots__ = []


class Pvar:
    '''A pattern variable'''
    __slots__ = 'greedy symbol value'.split()
    repeating = False

    def __init__(self, symbol):
        self.symbol = symbol
        self.greedy = True if symbol.str.startswith('*') else False
        if self.greedy:
            self.symbol.str = self.symbol.str.lstrip('*')
        self.value = None

    def __repr__(self):
        r = str('{} -> {}'.format(self.symbol, self.value))
        if self.greedy:
            return '*' + r
        else:
            return r

    def _propagate_match(self, attempt):
        '''make sure repeated vars are the same'''
        existing = attempt.get(self.symbol)
        if existing:
            if not existing:
                self.symbol = existing
            else:
                if self.value != existing:
                    raise FailedMatch(
                        'Pattern variable already bound: {} != {}'.format(
                            self.value, existing))
        else:
            attempt[self.symbol.str] = self.value

    def __eq__(self, other):
        if non_string_collection(other):
            return False
        if not self.value:
            # We currently don't have a match so take it
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


class Underscore:
    '''Wildcard that matches anything'''
    __slots__ = 'greedy symbol value'.split()
    repeating = False

    def __init__(self, greedy=False):
        self.symbol = Symbol('_')
        self.greedy = greedy
        self.value = None

    def __eq__(self, other):
        self.value = 'Matched'
        return True

    def __repr__(self):
        return "_"

    def _propagate_match(self, attempt):
        '''discard the match'''
        pass

class Rvar:
    '''A raw value that must be exactly equal for a match to occur'''
    __slots__ = 'value'.split()
    greedy =  False
    repeating = False

    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        return self.value == other

    def __repr__(self):
        return self.value

    def _propagate_match(self, attempt):
        pass


class Template:
    '''A list of pattern variables'''
    __slots__ = 'repeating pvars value has_star has_ellipsis map'.split()
    greedy = False

    def __init__(self, *data):
        if len(data) == 1 and isinstance(data[0], collections.Container):
            # Allow a single arg of a list to be passed
            data = data[0]

        self.pvars = []
        has_star = False
        has_ellipsis = False

        for element in data:
            if non_string_collection(element):
                # Add a sub-template
                self.pvars.append(Template(element))
            elif isinstance(element, Symbol):
                # Handle special pattern variables:
                #   Underscores match anything but get discarded
                if element.str == '_':
                    self.pvars.append(Underscore())
                elif element.str == '*_':
                    # Underscores can be greedy
                    if has_star:
                        raise SyntaxError(
                            'Can only have a maximum of one * per template')
                    else:
                        has_star = True
                    self.pvars.append(Underscore(greedy=True))
                elif element.str == '...':
                    # Ellipsis makes the previous sub-template greedy
                    if not isinstance(self.pvars[-1], Template):
                        raise SyntaxError(
                            '... can only be used on a repeating sub template')
                    if has_ellipsis:
                        raise SyntaxError(
                            'Can only have a maximum of one ... per template')
                    else:
                        has_ellipsis = True
                        self.pvars[-1].repeating = True
                else:
                    # Handle all other pattern variables
                    if element.str.startswith('*'):
                        # Greedy match like Python's tuple unpacking
                        if has_star:
                            raise SyntaxError(
                                'Can only have a max of one * per template')
                        else:
                            has_star = True
                    self.pvars.append(Pvar(element))
            else:
                # TODO: It should be possible to specify values rather than
                #       symbols. They should only match themselves.
                # raise ValueError(element, type(element), ' should be a Symbol')
                self.pvars.append(Rvar(element))

            if has_star and has_ellipsis:
                raise SyntaxError('Invaild match template')

        self.map = dict()
        self.repeating = False

    def __repr__(self):
        # Display current pvars and their bindings
        return str(self.pvars)

    def __eq__(self, other):
        if not non_string_collection(other):
            raise SyntaxError(
                    "Attempted match against something that isn't a container")
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
                    for k in values_so_far:
                        if k in self.map:
                            raise FailedMatch(
                                ('A repeating template has redeclared a previous'
                                 ' pattern variable'))
                    for _, next_target in pairs:
                        # reset so we can match again
                        for p in pvar.pvars:
                            p.value = None
                        pvar == next_target
                        # update the map
                        for p in pvar.pvars:
                            values_so_far[p.symbol.str].append(p.value)
                    # We've now drained pairs so we are done
                    self.map.update(values_so_far)
                    break
                    

            # if all([not isinstance(v.value, Unmatched) for v in self.pvars]):
            if all([v.value for v in self.pvars]):
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
        ([Symbol(x) for x in 'a *b c d'.split()],
         (1,2,3,4,5,6,7)),
        ([Symbol(x) for x in 'a *b _ d'.split()],
         (1,2,3,4,5,6,7)),
        ([Symbol(x) for x in 'a *b c *d'.split()],
         (1,2,3,4,5,6,7)),
        ([Symbol(x) for x in 'a b c'.split()],
         (1,2,3,4,5,6,7)),
        ([Symbol(x) for x in 'a b c'.split()],
         ('A', 'B', 'C')),
        ([Symbol(x) for x in 'a _ c'.split()],
         ('A', 'B', 'C')),
        ((Symbol('a'), Symbol('b'), (Symbol('c'), Symbol('d'))),
         (1, 2, (3,4))),
        ([Symbol(x) for x in 'a *b c'.split()],
          (1, 2, (3,4))),
        ([Symbol(x) for x in 'a b *c d'.split()],
          (1,2,3,4,5,6,7)),
        (((Symbol('a'), Symbol('b')), Symbol('...')),
         ((1,2), (3,4), (5,6))),
        ((Symbol('x'), Symbol('y'), (Symbol('a'), Symbol('b')), Symbol('...')),
         ('a', 'b', (1,2), (3,4), (5,6))),
        ((Symbol('a'), Symbol('b'), (Symbol('a'), Symbol('b')), Symbol('...')),
         ('a', 'b', (1,2), (3,4), (5,6))),
        ((1,2,3,4,5,6, Symbol('this')),
         (1,2,3,4,5,6,7)),
        ]

    for tmp, tar in tests:
        print('Template: ', tmp)
        print('Target: ', tar)
        try:
            T = Template(tmp)
            T == tar
            print('Match:', T.map, '\n')
        except FailedMatch as f:
            print('** MATCH FAILED:', f, '**\n')
        except SyntaxError as s:
            print('** INVALID TEMPLATE:', s, '**\n')
