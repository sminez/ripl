'''
Internal types
'''


class RiplObject:
    '''Base class for all RiplClasses'''
    pass


class RiplSymbol(RiplObject):
    '''Internal representation of symbols'''
    def __init__(self, string):
        self.str = string

    def __repr__(self):
        # NOTE: not sure if this is a good idea...
        # raise NameError('name {} is not defined'.format(self.str))
        return self.str

    def __hash__(self):
        return hash(self.str)

    def __eq__(self, other):
        try:
            return self.str == other.str
        except AttributeError:
            # comp to raw string
            return self.str == other


class RiplString(RiplObject, str):
    def __new__(cls, string, *args, **kwargs):
        return super(RiplString, cls).__new__(cls, string)


class RiplList(RiplObject, list):
    def __repr__(self):
        return '(' + ' '.join(self) + ')'

    def __hash__(self):
        return hash(self)


class RiplTuple(RiplObject, tuple):
    def __repr__(self):
        s = [str(elem) for elem in self]
        return '(, ' + ' '.join(s) + ')'

    def __hash__(self):
        return hash(self)


class RiplDict(RiplObject, dict):
    def __init__(self, lst):
        if len(lst) % 2 != 0:
            raise SyntaxError("unmatched key/value in dict literal")
        else:
            super().__init__()
            pairs = [lst[i:i+2] for i in range(0, len(lst), 2)]
            d = {k: v for k, v in pairs}
        super().__init__(d)

    def __repr__(self):
        tmp = [':{} {}'.format(k, v) for k, v in self.items()]
        return '{' + ' '.join(tmp) + '}'

    def __hash__(self):
        return hash(self)


class RiplNumeric(RiplObject):
    '''Base class for numerics'''
    pass


class RiplInt(RiplNumeric, int):
    def __new__(cls, num, *args, **kwargs):
        if isinstance(num, str):
            try:
                # Default to base 10
                _num = int(num, base=10)
            except ValueError:
                # Try to find the base
                base_prefixes = {"0b": 2, "0o": 8, "0x": 16}
                _num = None
                for prefix, base in base_prefixes.items():
                    if num.startswith(prefix):
                        _num = int(num, base=base)
                        break
                if not _num:
                    # We couldn't find a base that worked
                    raise ValueError
        return super(RiplInt, cls).__new__(cls, _num)


class RiplFloat(RiplNumeric, float):
    def __new__(cls, number, *args, **kwargs):
        number = float(number)
        return super(RiplFloat, cls).__new__(cls, number)
