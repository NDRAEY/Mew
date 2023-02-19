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

!!!: Every `targetname` folder should contain empty `__init__.py` file to force pip to add it to package.

# Installation

Run ```pip install https://github.com/NDRAEY/Mew/archive/main.zip``` to install latest commit from GitHub repo.

# Roadmap

- [x] Standard types
	- [x] Numerals (u8, u16, u32, ...)
	- [ ] String
		- [ ] Store in variables
		- [ ] Operations with string
			- [ ] Concatenation
			- [ ] Trimming
			- [ ] Splitting
			- [ ] Lowercase/Uppercase/Normal conversion
	- [x] Own types creation
		- [x] Structs
- [x] Variables
	- [x] Assign
	- [x] Reassign
- [x] Functions
	- [x] Simple
	- [ ] Value-Returnable
		- [x] Return from variables
		- [ ] Return any value
	- [ ] Lambdas
	- [ ] Store functions in variables
- [x] Control flow
	- [x] if
	- [x] else
	- [ ] else if
- [ ] Loops
	- [x] while
	- [ ] for
	- [ ] endless
	- [ ] break / continue
- [ ] Arrays
	- [x] Single-type
	- [x] Multi-dimensional arrays
	- [ ] Indexing
	- [ ] Indexing and assigning
	- [ ] Slicing
	- [ ] Multi-type
- [ ] Dictionaries
- [ ] Overflow prevention
- [ ] Pointers
- [ ] Memory safety
	- [x] Auto-free
	- [ ] Value move
	- [ ] Force freeing
- [ ] FFI
	- [ ] Minimal
- [ ] Cross-platform
	- [ ] Windows
	- [x] Linux (Partial)
	- [ ] MacOS
	- [ ] *BSD
	- [ ] Other known kernels
		- [ ] SayoriOS
		- [ ] SynapseOS
		- [ ] KolibriOS
		- [ ] SerenityOS
		- [ ] ToaruOS
- [ ] No system libraries (no dependcies, like Golang)

# Contributing

## How to contribute?

1. Fork this repository.
2. Make your changes in separate branch
3. Submit a PR (Pull Request).
4. Wait for your PR to be reviewed, approved & merged by an admin/owner.
5. If there are issues with your PR, please revise them in accordance to the comments made by the admins.
