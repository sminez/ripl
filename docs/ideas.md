# Propper multiline input using prompt toolkit
There seems to be an undocumented `extra_input_processors` arg for `prompt`.
It gets used like this in `create_prompt_layout`
```Python
if extra_input_processors:
    input_processors.extend(extra_input_processors)
```
- Looks like it needs to be a `prompt_toolkit.layout.processors.ConditionalProcessor`
- That takes a `Processor` (same file) and `prompt_toolkit.filters.CLIFilter`
  - If filter(cli) is true it applies the processor.

### Initial idea
```Python
class DoubleEnter(Processor):
    def apply_transformation(self, cli, document, lineno, source_to_display, tokens):
        pass

double_enter = Condition(lambda x: x.endswith('\n\n'))

extra_input_processors=ConditionalProcessor(DoubleEnter, double_enter)
```

### Alternate:
Can you do a key binding that executes differently depending on the current buffer
content?
--> Bind enter to `AcceptInput if buff.endswith('\n') else buff.append('\n')`

# Execution context as first class values
Lambda allows functions to be defined inline and LISP allows functions to be passed
around as data. RIPL is using a chained-dict as an execution environment so what if
the programmer is allowed to pass around the environment itself as data?
--> Lots of scope (lol!) for disaster but potentially kind of fun!

```Lisp
(with (context (capture (myinstance)))
  ;; Now we can use the data and methods of `myinstance`
  ;; but we wont mutate the underlying object.
  (foo (1 2 3))
  )
```

You could also use this to access the definitions of a module in local scope only?

By default, the capture will take _everything_ from its argument:
- `(capture/callables foo)` to take only callables.
- `(capture/vars foo)` to take only the non callables.
- `(capture/local/... foo)` to prevent looking back up the chain.

## Side-note
I kind of like this syntax of using `(function/option)` to either switch definitions
or to run a `cond` without passing it as a parameter.
  This could be used to define multiple related functions that take the same args
  as a one shot thing:
```Lisp
(defcond foo (arg)              (define foo/bar
  (/bar                           (lambda (arg)
    (print foo))        -->         (begin
  (/baz                               (print foo))))
    (print foo foo))            (define foo/baz
  )                               (lambda (arg)
                                    (begin
                                      (print foo foo))))
```


## Call/cc
Could you do this with context managers?


## Pipelines
`https://en.wikipedia.org/wiki/Pipeline_(Unix)`


## Typing
https://docs.python.org/3/library/typing.html
https://github.com/python/mypy
  - A static type checker

```Python
import typing
def foo(a: int, b: str) -> str:
    return ' '.join([b for n in range a])

typing.get_type_hints(foo)
>>> {'a': <class 'int'>, 'return': <class 'str'>, 'b': <class 'str'>}


def foo(a: int, b: str) -> typing.Generator[str, None, None]:
    for n in range(a):
        yield b

typing.get_type_hints(foo)
>>> {
'a': <class 'int'>,
'return': typing.Generator<+T_co, -T_contra, +V_co>[str, NoneType, NoneType],
'b': <class 'str'>
}
```

http://stackoverflow.com/questions/2220699/whats-the-difference-between-eval-exec-and-compile-in-python
