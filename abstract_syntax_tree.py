from dataclasses import dataclass
from typing import *

@dataclass
class Operation:
    op: Any

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

@dataclass
class Assignment:
    name: str
    value: str

@dataclass
class Name:
    value: str

@dataclass
class Integer:
    value: int

@dataclass
class String:
    value: str

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

@dataclass
class Program:
    operations: list[Operation]

@dataclass
class If:
    comparison: Any
    code: Program

@dataclass
class IfElse:
    comparison: Any
    code: Program
    else_: Program

@dataclass
class While:
    comparison: Any
    code: Program

@dataclass
class Func:
    name: str
    args: ParameterList
    ret:  str
    code: Program

@dataclass
class Return:
    value: Any
