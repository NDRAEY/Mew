from dataclasses import dataclass
from typing import *

@dataclass
class Operation:
    op: Any
    lineno: int

@dataclass
class Definition:
    type: str
    name: str
    value: Any

@dataclass
class BinOp:
    left: str
    op: str
    right: str
    lineno: int

@dataclass
class Assignment:
    name: str
    value: str
    lineno: int

@dataclass
class Name:
    value: str
    lineno: int
    pos: int

@dataclass
class Integer:
    value: int
    lineno: int
    pos: int

@dataclass
class String:
    value: str
    lineno: int
    pos: int

@dataclass
class ParameterList:
    value: list

@dataclass
class FunctionDefinition:
    return_type: str
    name: str
    arguments: ParameterList
    body: Any

@dataclass
class FunctionCall:
    name: str
    arguments: ParameterList
    lineno: int

@dataclass
class Program:
    operations: list[Operation]

@dataclass
class IfElse:
    comparison: Any
    code: Program
    else_: Program
    lineno: int

@dataclass
class While:
    comparison: Any
    code: Program
    lineno: int

@dataclass
class Func:
    name: str
    args: ParameterList
    ret:  str
    code: Program
    lineno: int
    need_dealloc: bool
    
@dataclass
class Return:
    value: Any
    lineno: int

@dataclass
class TypedVarDefinition:
    type: str
    var: Any
    lineno: int

@dataclass
class New:
    obj: FunctionCall
    lineno: int

@dataclass
class StructFieldArray:
    value: list

@dataclass
class Struct:
    name: str
    value: StructFieldArray
    lineno: int

@dataclass
class Path:
    elements: str
    lineno: int

@dataclass
class Warning:
    message: str
    refer: Any
    lineno: int

@dataclass
class ExternC:
    code: str
    lineno: int

@dataclass
class Loop:
    code: Program
    lineno: int

@dataclass
class Break:
    lineno: int

@dataclass
class Continue:
    lineno: int

@dataclass
class Float:
    value: float
    lineno: int
    pos: int

@dataclass
class Bool:
    value: bool
    lineno: int
    pos: int

@dataclass
class Use:
    path: Path
    as_name: str
    lineno: int

@dataclass
class End:
    char: str
    lineno: int
