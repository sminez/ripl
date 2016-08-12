# Propper multiline input
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


# Start of a type system
```Lisp
(typedef {:a int, :b list}
 (def n-cat (a b)
 """cat together 'a' copies of b"""
   # This builds a list-literal
   [for-in b n (range a)]
 )
)
```
`type-def` takes a dict of symbol/type pairs and a function definition. The arguments
to the function must match the symbols in the dict. It wraps the function and
optimises it if posible (c types?) while raising a type error if invalid types are
passed.
`for-in` is a pythonic for loop. enclosing it in a list literal makes a list-comp.
Enclosing it in a dict literal makes a dict comp so long as it generates pairs.
