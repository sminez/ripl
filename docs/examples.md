# Definitions
```Lisp
(defn foo (arg1 arg2)
  ;#(do things with arg1 arg2)
  )


(foo 1 2)
--> ;; things that got done
```
A function is defined using the `defn` macro which internally gets
de-sugared by the lexer to:
```Lisp
(define foo
  (lambda (arg1 arg2)
    ;#(do things with arg1 arg2)
    ))
```
Both forms are valid and equivalent, defn is purely to shorten the body
of the definition and improve readability.

```Lisp
(class MyClass {:class properties :bound here}
  (method init (arg1 args2)
    ;#(Do some stuff here)
  )
  ;; Self is implicitly added as the first argument
  ;; so that methods are easy to pull out and drop on
  ;; something else.
  ;; i.e. replace `method` with `defn` and it will work.
  (method mymethod! (arg1 arg2)
    (begin
      (print (self arg1) arg2)
      (set! (self arg1) (self arg2))
      (set! (self arg2) (arg1)))
  )
)

(define myinstance
  (MyClass (1 2)))

(. myinstance (mymethod! ("a" "b")))
--> 1 "b"
(. myinstance (mymethod! ("a" "b")))
--> 2 "b"
```
This example uses the Scheme convention of ending a function/procedure
name with `!` if it mutates a previous state. This is to warn users that
repeated calls with the same args are not guaranteed to provide the same
output. `(enforce this?)`

The `.` operator forces context lookup on the object passed as the first parameter.
(This will need to have a differenti but equivalent behaviour for imported
Python code...)

# Optional Types
```Lisp
(:: {:n int, :lst list}
 (defn n-palindromes? (n lst)
  """Return true if there are n palindromes in lst"""

 )
)
```
`type-def` takes a dict of symbol/type pairs and a function definition. The arguments
to the function must match the symbols in the dict. It wraps the function and
optimises it if posible (c types?) while raising a type error if invalid types are
passed.
`for-in` is a pythonic for loop. enclosing it in a list literal makes a list-comp.
Enclosing it in a dict literal makes a dict comp so long as it generates pairs.

```Lisp
;; Haskell style pattern matching
(defn zipwith (f a b)
  (match (a b)
  (('() _) '())
  ((_ '()) '())
  (((: x xs) (: y ys)) (: (f x y) (zipwith f xs ys)))))

;; Pythonic for loop that retains generator behaviour
(defn zipwith2 (f a b)
  (for-each pair (zip a b)
  (yield (f *pair))))

;; LISPy cons/car/cdr with explicit bool testing
(defn zipwith3 (f a b)
  (if (or (== a '()) (== b '()))
  '()
  (cons (f (car a) (car b)) (zipwith3 (cdr a) (cdr b)))))
```
