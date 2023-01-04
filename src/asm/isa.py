import json
from collections import namedtuple
from enum import Enum


class Opcode(str, Enum):
    # Коды операций, представленных на уровне языка.
    CMP = 'CMP'
    JE = 'JE'
    JMP = 'JMP'
    ST = 'ST'
    LD_VAL = 'LD_VAL'
    LD_ADDR = 'LD_ADDR'
    MOD = 'MOD'
    INC = 'INC'
    DEC = "DEC"
    ADD = 'ADD'
    SUB = 'SUB'
    IN = 'IN'
    OUT = 'OUT'
    HLT = 'HLT'
    DATA = 'data'


class Register(str, Enum):
    AC = 'AC'
    SR = 'SR'


opcode_args = {
    Opcode.CMP: 1,
    Opcode.JE: 1,
    Opcode.MOD: 1,
    Opcode.INC: 0,
    Opcode.DEC: 0,
    Opcode.JMP: 1,
    Opcode.ADD: 1,
    Opcode.HLT: 0,
    Opcode.LD_ADDR: 1,
    Opcode.LD_VAL: 1,
    Opcode.IN: 0,
    Opcode.ST: 1,
    Opcode.OUT: 0
}


class Term(namedtuple('Term', 'line operation argument')):
    """Полное описание инструкции."""


# def write_code(filename, code):
#     with open(filename, "w", encoding="utf-8") as file:
#         file.write(json.dumps(code, indent=4))

# def read_code(filename):
#     with open(filename, encoding="utf-8") as file:
#         code = json.loads(file.read())
#
#     for instr in code:
#         instr['opcode'] = Opcode(instr['opcode'])
#         if 'term' in instr:
#             instr['term'] = Term(instr['term'][0], instr['term'][1], instr['term'][2])
#
#     return code
