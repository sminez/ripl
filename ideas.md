# Imports
Full disclosure: this is probably a terrible way to do this...
```Python
def pyimport(module, env, _as=None, _from=None):
    if _as and _from:
        raise SyntaxError

    if _as:
        exec('import {} as {}'.format(module, _as))
        defs = {RiplSymbol(k): v for k, v in vars(globals()[_as]).items()}
        env.update(defs)
    elif _from:
        exec('from {} import {}'.format(module, ', '.join(_from))
        for f in _from:
            defs = {RiplSymbol(k): v for k, v in vars(globals()[f]).items()}
            env.update(defs)
    else:
        exec('import {}'.format(module))
        defs = {RiplSymbol(k): v for k, v in vars(globals()[module]).items()}
        env.update(defs)

    return env
```
