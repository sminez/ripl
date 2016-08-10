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


## May be useful for this: traceback from Nose failing to import a module
```
Traceback (most recent call last):
  File "/usr/local/lib/python3.4/dist-packages/nose-1.3.7-py3.4.egg/nose/failure.py", line 39, in runTest
    raise self.exc_val.with_traceback(self.tb)
  File "/usr/local/lib/python3.4/dist-packages/nose-1.3.7-py3.4.egg/nose/loader.py", line 418, in loadTestsFromName
    addr.filename, addr.module)
  File "/usr/local/lib/python3.4/dist-packages/nose-1.3.7-py3.4.egg/nose/importer.py", line 47, in importFromPath
    return self.importFromDir(dir_path, fqname)
  File "/usr/local/lib/python3.4/dist-packages/nose-1.3.7-py3.4.egg/nose/importer.py", line 94, in importFromDir
    mod = load_module(part_fqname, fh, filename, desc)
  File "/usr/lib/python3.4/imp.py", line 235, in load_module
    return load_source(name, filename, file)
  File "/usr/lib/python3.4/imp.py", line 171, in load_source
    module = methods.load()
  File "<frozen importlib._bootstrap>", line 1220, in load
  File "<frozen importlib._bootstrap>", line 1200, in _load_unlocked
  File "<frozen importlib._bootstrap>", line 1129, in _exec
  File "<frozen importlib._bootstrap>", line 1471, in exec_module
  File "<frozen importlib._bootstrap>", line 321, in _call_with_frames_removed
```
