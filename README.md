# PyDayuri

A compiler for Dayuri language implemented in Python

## Dayuri

Dayuri is the name of the functional language I'm aim to design.
It's main purpose is to be used as my new non work main language, but
right now is in design stage, so it would be **incredible unstable**.


### RoadMap

- Grammar design
- Type checking
- Python code generation/interpreter
- Add a light weight type inference
- Target wasm or llvm or rust
- Write a editor or wayland compositor
- Bootstrap


### Intended features

- Fast to compile.
    This is why type inference is leave as just *light weight*,
    i believe type annotations tend to be useful rater than
    annoying.

- Pure, functional, strong typed, static typed, strict.
    I want to learn as much as i can of programming languages
    theory, this means I'm focusing in functional ones right now.
    In the future i will try to add mutability.

- Formally verifiable but still made to program in it.
    A main purpose I want to reach in my life (or get close to)
    is to close the breach between *pure theorist* and 
    *practice oriented* programmers.
    So I want a programming language that could be used in
    both ways with ease.

- Multiplatform 
    This is why I'm using Python rather than Haskell as I did before.
    Python is incredible simple to install and widely available. It 
    could be slow, but for the time before bootstrap we just need 
    it to be portable and *reliable*. 
    Additionally  I'm quite comfortable with (lark)[https://github.com/lark-parser/]
    a parser generator that allows to experiment with ease with error reporting
    and other things (as the custom indenter shows). For the bootstrap
    I will partially port lark to Dayuri or at least provide bindings.


- Good error reporting
    I have spend much of my time learning about parsing rather than language optimization stuff,
    so I'm a fan of experiments with syntax.
    I tried to use other language almost like Haskell but improved with the new things
    we know after all this time, that language is quite good but... I struggle a lot with 
    the syntax errors, most of the time they won't help find my error while learning.
    So I consider good error reporting a main thing a language must have.

- Tooling, Language server protocol
    Compiler is designed with the intention to be modular so that it could be easy to just
    write a "documentation extraction", "literate programming", "formatter", "linter" tools, and
    even make incremental parsing and type driven design a thing. 
    In fact I want to experiment programming with voice by exploiting type driven design.
    I don't know if i will implement a server since it could be pretty complex and time 
    consuming.




### A little view

    -- | A middle way between Haskell and Coq syntax for algebraic data types
    data Nat =
      Z : Nat
      S : Nat ->Nat
    
    -- Constructors and types can start with lower letter 
    -- I have allways wondered how one programn in Haskell
    -- if insist on use natural laguage without upper case letters.
    data bool = 
      True: Nat
      false: Nat

    -- | This is a reference to @arg:n and @arg:m args in @name
    -- | intended to be filled by documentation extraction
    add : n@Nat-> m@Nat -> Nat
    add Z w = @m
    -- This is as weird as it can to ilustrate things
    -- In fact we could just write (S k) r = S (add k r)
    -- But we could refer to parameters by name by using @
    add S k, r = S $ add k @m


    eq : Nat-> Nat -> Nat
    eq n m =
      match n with
        Z -> 
          match m with
            Z ->  True
            _ -> false
        S n -> match m with
            Z -> false
            _ -> True


          



