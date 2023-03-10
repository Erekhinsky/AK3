#!/usr/bin/python3
# pylint: disable=missing-function-docstring  # чтобы не быть Капитаном Очевидностью
# pylint: disable=invalid-name                # сохраним традиционные наименования сигналов
# pylint: disable=consider-using-f-string     # избыточный синтаксис

import json
import re
import sys

from isa import Opcode, Term, Register

symbol2opcode = {
    'CMP': Opcode.CMP,
    'JE': Opcode.JE,
    'JMP': Opcode.JMP,
    'ST': Opcode.ST,
    'LD_VAL': Opcode.LD_VAL,
    'LD_ADDR': Opcode.LD_ADDR,
    'INC': Opcode.INC,
    'DEC': Opcode.DEC,
    'ADD': Opcode.ADD,
    'SUB': Opcode.SUB,
    'MOD': Opcode.MOD,
    'IN': Opcode.IN,
    'OUT': Opcode.OUT,
    'HLT': Opcode.HLT,
    'data': Opcode.DATA,
}

register = {
    'AC': Register.AC,
    'SR': Register.SR,
}


def is_int(s):
    return re.match(r"[-+]?\d+(\.0*)?$", s) is not None


def translate(text):
    terms = []
    labels = {}
    data = {}
    words_counter = -1
    code = []

    for line in text.split("\n"):
        words = line.split()
        words_counter = words_counter + 1

        if not words:
            raise EOFError

        if len(words) == 1 and words[0][0] == ':' and words[0][len(words) - 1] == ':':
            labels[words[0]] = words_counter
            words_counter = words_counter - 1
        elif len(labels) == 1 and ':data:' in labels.keys():
            data[words[0]] = words_counter
            if words[1][0] == '\'' or words[1][0] == '\"':  # Char
                words[1] = words[1][1:len(words[1]) - 1]
                if words[1] == '':  # Space
                    terms.append((Term('data', " ")))
                    continue
            terms.append(Term('data', words[1]))
        elif words[0] in symbol2opcode.keys():
            terms.append(Term(words[0], words[1:3]))
        else:
            raise AttributeError

    for i in range(len(terms)):
        if terms[i].operation != 'data':
            if len(terms[i].argument) == 0:
                terms[i] = Term(terms[i].operation, terms[i].argument)
            elif len(terms[i].argument) == 1:
                if terms[i].argument[0] in labels.keys():  # Label
                    terms[i] = Term(terms[i].operation, labels[terms[i].argument[0]])
                elif terms[i].argument[0] in data.keys():  # Data
                    terms[i] = Term(terms[i].operation, data[terms[i].argument[0]])
                elif terms[i].argument[0] in register.keys():  # Register
                    terms[i] = Term(terms[i].operation, terms[i].argument[0])
                elif terms[i].operation == Opcode.OUT or terms[i].operation == Opcode.IN:
                    terms[i] = Term(terms[i].operation, terms[i].argument[0])
                else:
                    print("Invalid arguments:", terms[i])
                    sys.exit()
            else:
                raise AttributeError

        code.append({'term': terms[i]})

    return code


def write_code(filename, code):
    with open(filename, "w", encoding="utf-8") as file:
        file.write(json.dumps(code, indent=4))


def read_code(filename, offset):
    start = offset

    with open(filename, encoding="utf-8") as file:
        code = json.loads(file.read())

    for instr in code:

        if instr['term'][0] == Opcode.DATA:
            if is_int(instr['term'][1]):
                instr['term'][1] = int(instr['term'][1])
            start += 1

        elif instr['term'][0] == Opcode.OUT or instr['term'][0] == Opcode.IN:
            if instr['term'][1]:
                instr['term'][1] = int(instr['term'][1])

        elif is_int(str(instr['term'][1])):
            instr['term'][1] = int(instr['term'][1])
            instr['term'][1] += offset

        instr['term'][0] = Opcode(instr['term'][0])

    offset += len(code)

    return code, start, offset
