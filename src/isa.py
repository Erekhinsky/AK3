from collections import namedtuple
from enum import Enum


class Opcode(str, Enum):
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


class Term(namedtuple('Term', 'line operation argument')):
    """Полное описание инструкции."""
