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
        raise NameError('name {} is not defined'.format(self.str))

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
