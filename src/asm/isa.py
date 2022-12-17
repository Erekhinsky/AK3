import json
from collections import namedtuple
from enum import Enum
from sys import argv


class Opcode(str, Enum):
    # Коды операций, представленных на уровне языка.
    CMP = 'CMP'
    JE = 'JE'
    MOV = 'MOV'
    DIV = 'DIV'
    MUL = 'MUL'
    INC = 'INC'
    DEC = "DEC"
    JMP = 'JMP'
    ADD = 'ADD'
    SUB = 'SUB'
    IN = 'IN'
    OUT = 'OUT'
    HLT = 'HLT'
    DATA = 'data'


class Register(str, Enum):
    AC = 'AC'
    BR = 'BR'
    SR = 'SR'


opcode_args = {
    Opcode.CMP: 2,
    Opcode.JE: 1,
    Opcode.MOV: 2,
    Opcode.DIV: 2,
    Opcode.INC: 0,
    Opcode.DEC: 0,
    Opcode.JMP: 1,
    Opcode.ADD: 2,
    Opcode.HLT: 0,
    Opcode.IN: 1,
    Opcode.OUT: 1
}


class Term(namedtuple('Term', 'line operation argument')):
    """Полное описание инструкции."""


def write_code(filename, code):
    with open(filename, "w", encoding="utf-8") as file:
        file.write(json.dumps(code, indent=4))


def read_code(filename):
    with open(filename, encoding="utf-8") as file:
        code = json.loads(file.read())

    for instr in code:
        instr['opcode'] = Opcode(instr['opcode'])
        if 'term' in instr:
            instr['term'] = Term(instr['term'][0], instr['term'][1], instr['term'][2])

    return code

