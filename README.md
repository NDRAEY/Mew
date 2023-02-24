# Mew

Mew (named after Pokémon) is a programming language created for programming in self-written OS kernels and popular systems

It uses [PLY](https://github.com/dabeaz/ply) as lexer and parser.

# Development

Yes, it's another programming language I writing 4th time

# Dependcies

Mew depends on 2 functions at the moment:

- `malloc()`
- `free()`

# Platforms

Mew uses target system that can be extended by adding `targetname` folder in the `mew_pl/` folder and putting files into it:

For example (Linux: `targets/linux`) should contain files:

- `defs.h` - type definitons
- `alloc.h` - allocation functions

For any other platform, your `targetname` folder should contain these files too to reach compatibility.

# Installation

Run
```
pip install https://github.com/NDRAEY/Mew/archive/main.zip
```
to install latest commit from GitHub repo.

# Roadmap

- [ ] Standard types
	- [x] Numerals (u8, u16, u32, ...)
	- [x] Float / Double
	- [ ] String
		- [ ] Store in variables
	- [x] Booleans
	- [ ] Generics
		- [ ] Generic structs
		- [ ] Generic classes
	- [ ] Lists
		- [ ] Push
		- [ ] Pop
		- [ ] Insert
		- [ ] Remove
		- [ ] Remove by index
	- [x] Own types creation
		- [x] Structs
- [x] Variables
	- [x] Assign
	- [x] Reassign
- [ ] Functions
	- [x] Simple
	- [ ] Value-Returnable
		- [x] Return variables
		- [x] Return binary operations
		- [ ] Return any value
	- [x] Lambdas
	- [x] Function overloading
	- [ ] Store functions in variables
- [x] Control flow
	- [x] if
	- [x] else
	- [x] else if
- [ ] Loops
	- [x] while
	- [ ] for
	- [x] loop
	- [x] break / continue
- [ ] Arrays
	- [x] Single-type
	- [ ] Use in functions
	- [ ] Multi-dimensional arrays
	- [x] Indexing
	- [x] Indexing and assigning
	- [ ] Slicing
- [ ] Dictionaries (Maps)
- [ ] Pointers
- [ ] Memory safety
	- [x] Auto-free
	- [ ] Value move
	- [ ] Force freeing
- [x] FFI
	- [x] Minimal (Done using `extern`)
- [ ] Cross-platform
	- [ ] Windows
	- [x] Linux (Partial)
	- [ ] MacOS
	- [ ] *BSD
	- [ ] Other known operating systems
		- [ ] SayoriOS
		- [ ] SynapseOS
		- [ ] KolibriOS
		- [ ] SerenityOS
		- [ ] ToaruOS
		- [ ] Haiku
- [ ] Classes
	- [ ] Public fields
	- [ ] Private fields
	- [ ] Operator overloading
	- [ ] Association with built-in types
- [ ] No system libraries (no dependcies, like Golang)
- [ ] Module support (like `import` in Python / `#include` in C)
	- [ ] From local files
	- [ ] Global
- [ ] Builtins
	- [ ] StdIO
		- [ ] Input
			- [ ] Streams
			- [ ] Keyboard
			- [ ] File
		- [ ] Output
			- [ ] Streams
			- [ ] Screen / TTY
				- [ ] Common output
				- [ ] Formatted output
			- [ ] File
	- [ ] Operations with string
		- [ ] Concatenation
		- [ ] Trimming
		- [ ] Splitting
		- [ ] Lowercase/Uppercase/Normal conversion
	- [ ] Time
		- [ ] Monotonic (UNIX)
		- [ ] Human-readable (hrs, mins, secs)
		- [ ] Formatting to string fmt
	- [ ] Math
		- [ ] sin()
		- [ ] cos()
		- [ ] tg()
		- [ ] ctg()
		- [ ] log()
		- [ ] exp()
		- [ ] pow()
		- [ ] ln()

# Contributing

## How to contribute?

1. Fork this repository.
2. Make your changes in separate branch
3. Submit a PR (Pull Request).
4. Wait for your PR to be reviewed, approved & merged by an admin/owner.
5. If there are issues with your PR, please revise them in accordance to the comments made by the admins.
