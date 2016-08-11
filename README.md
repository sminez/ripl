# RIPL - {RIPL Is Pythonic LISP}

RIPL started as a weekend tinkering with some of the ideas from Peter Norvig's
[Lispy scheme interpretor](http://norvig.com/lispy.html) and has grown into a
side project where I try to hack my favourite language features from other
languages into python with the goal of direct interpretation or generating a
Python source file. (OK, where I try to hack my favourite parts of Haskell
into Python...and some other stuff too.)

Other than for the fun of implementing a LISP interpretor inside of Python,
my end goal for this is to be able to quickly and easily write some data
piplining tools.

We'll see how that goes...

RIPL is still very hacky so bare with me!

- `python3 cli.py` will get you a repl (the riplrepl!)
- `python3 cli.py -s "<RIPL EXPRESSION>"` will evaluate and print as a one shot.
- `python3 cli.py -f <RIPL_FILE.ripl>` will evaluate and run a file (coming soon...)


### Syntax
The aim is to be able to import and run any valid python code into RIPL and to develop a converter that allows
RIPL code to be imported into a python file.
At the moment, the python builtins and python math standard libray are available as functions to call using standard LISP
sexp syntax:<br>
- `(print "hello, world!") --> print("hello, world!)`<br>

Nesting and evaluation works in the usual LISP way:<br>
- `(print (+ "hello," " world!")) --> print("hello," + " world!")`<br>

As you can see from the TODO below, I'm planning on adding a bunch more stuff but for now, the `+` operator is overloaded
to allow you to sum arbitrary lists of numeric types:<br>
  `(+ 1 2.14 0.00159) --> 3.14159`

- If in doubt I will be referring to [clojure](http://clojure.org/api/cheatsheet) for ideas.

### Running tests
Set up a virtual-env for dev work and then run `python3 setup.py install` to
set everything up and give you the `ripl` command.
- Use `python3 testrunner.py --with-coverage --cover-package=ripl` to run the tests.


### TODO
- [ ] Break the evaluator into smaller pieces
- [ ] A prelude of functional style functions and operators
  - fold, scan, product, filter, reverse
  - take/drop{while}
  - quick file handling
  - Currying / partial application (have by default?)
  - zipwith
  - functools / itertools / toolz(maybe?) be default
- [ ] Python control flow: for, while, if
  - [ ] Functional versions / alternatives for these
- [ ] Tail call recursion
- [ ] Classes
- [ ] Haskell style pattern matching
- [ ] A type system(! (>=3.5 only i think))
  - Look at using [typeannotations](https://github.com/ceronman/typeannotations)
- [ ] Macros
- [ ] Auto indent / formatting in the repl
  - Look [here](https://goo.gl/da5rR8) for Pygments Hy version.
- [ ] A syntax file for Vim (maybe once I have the syntax settled...)
- [ ] docs
