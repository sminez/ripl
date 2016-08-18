[![Build Status](https://travis-ci.org/sminez/ripl.svg?branch=master)](https://travis-ci.org/sminez/ripl)
[![Coverage Status](https://coveralls.io/repos/github/sminez/ripl/badge.svg?branch=master)](https://coveralls.io/github/sminez/ripl?branch=master)

# RIPL - {RIPL Is Pythonic LISP}

RIPL started as a weekend tinkering with some of the ideas from Peter Norvig's
[lis.py scheme interpretor](http://norvig.com/lispy.html) and has grown into a
side project where I try to hack my favourite language features from other
languages into python with the goal of direct interpretation or generating a
Python source file. (OK, where I try to hack my favourite parts of Haskell
into Python...and some other stuff too.)

Other than for the fun of implementing a LISP interpretor inside of Python,
my end goal for this is to be able to quickly and easily write some data
piplining tools.

We'll see how that goes...

RIPL is still very hacky so bare with me!

After running `setup.py install`:
- `ripl` will get you a repl (the riplrepl!)
- `ripl -s "(print (: "Hello, " "world" "!")` will evaluate and print as a one shot.
- `ripl my_awsome_file.rpl` will evaluate and run a file (coming soon...)


RIPL will only run on Python3 as it makes use of many Python3 only features.
If you don't currently have Python3, you _can_ install it alongside an existing
Python2 installation.

Go on.

You know you want to...

## A note on Hy
Before you look at this and shout:<br>
`"Hey! Have you heard of Hy? There's already a LISP that runs on Python!"`<br>
Yes, I have heard of [Hy](https://github.com/hylang/hy).<br>
It's awesome!<br>
I'm actually cribbing from the Hy [builtins](http://docs.hylang.org/en/stable/language/api.html?#built-ins) 
docs and the equivalent for 
[Clojure](https://github.com/clojure/clojure/blob/clojure-1.7.0/src/clj/clojure/core.clj#L1564) in doing this.

My only issue with Hy is that I didn't write it! The main goal of RIPL is for me 
to have fun implementing things and as such I'm trying to start from scratch (ish...).
Who knows, once I understand how all of this works I may end up contributing to Hy in the future.


### Syntax
The aim is to be able to import and run any valid python code into RIPL and to develop
a converter that allows RIPL code to be imported into a python file.
At the moment, the python builtins and python math standard libray are available as 
functions to call using standard LISP sexp syntax:<br>
- `(print "hello, world!") --> print("hello, world!)`<br>

Nesting and evaluation works in the usual LISP way:<br>
- `(print (+ "hello," " world!")) --> print("hello," + " world!")`<br>

As you can see from the TODO below, I'm planning on adding a bunch more stuff but for now,
the `+` operator is overloaded to allow you to sum arbitrary lists of numeric types:<br>
  `(+ 1 2.14 0.00159) --> 3.14159`

- If in doubt I will be referring to [Clojure](http://clojure.org/api/cheatsheet) for ideas.

### Running tests
Set up a virtual-env for dev work and then run `python3 setup.py install` to
set everything up and give you the `ripl` command.
- Use `python3 testrunner.py --with-coverage --cover-package=ripl` to run the tests.


### TODO
- [ ] A prelude of functional style functions and operators
  -  [x] fold, scan, product, filter, reverse
  - [x] take/drop{while}
  - [ ] quick file handling
  - [x] Currying / partial application (planning on having `~(sexp)` as syntax for this)
  - [ ] zipwith
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
- [ ] Docs...lots of docs!
