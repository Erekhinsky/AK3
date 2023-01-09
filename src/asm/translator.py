import json
from isa import Opcode, Term, Register

# словарь символов, непосредственно транслируемых в машинный код
symbol2opcode = {
    'CMP': Opcode.CMP,
    'JE': Opcode.JE,
    'ST': Opcode.ST,
    'MOD': Opcode.MOD,
    'INC': Opcode.INC,
    'DEC': Opcode.DEC,
    'JMP': Opcode.JMP,
    'ADD': Opcode.ADD,
    'SUB': Opcode.SUB,
    'IN': Opcode.IN,
    'OUT': Opcode.OUT,
    'HLT': Opcode.HLT,
    'LD_VAL': Opcode.LD_VAL,
    'LD_ADDR': Opcode.LD_ADDR,
    'data': Opcode.DATA,
}

register = {
    'AC': Register.AC,
}


def translate(text):
    terms = []
    labels = {}
    data = {}
    words_counter = -1
    code = []

    for line in text.split("\n"):
        words = line.split()
        words_counter = words_counter + 1

        if len(words) == 1 and words[0][0] == ':' and words[0][len(words) - 1] == ':':
            labels[words[0]] = words_counter
            words_counter = words_counter - 1
        elif len(labels) == 1:
            data[words[0]] = words_counter
            if words[1][0] == '\'' or words[1][0] == '\"':
                words[1] = words[1][1:len(words[1]) - 1]
                if words[1] == '':
                    terms.append((Term(words_counter, 'data', " ")))
                    continue
            terms.append(Term(words_counter, 'data', words[1]))
        else:
            terms.append(Term(words_counter, words[0], words[1:3]))

    for i in range(len(terms)):
        if terms[i].operation != 'data':
            if len(terms[i].argument) == 0:
                terms[i] = Term(terms[i].line, terms[i].operation, terms[i].argument)
            elif len(terms[i].argument) == 1:
                if terms[i].argument[0] in labels.keys():  # Label
                    terms[i] = Term(terms[i].line, terms[i].operation, labels[terms[i].argument[0]])
                elif terms[i].argument[0] in data.keys():  # Data
                    terms[i] = Term(terms[i].line, terms[i].operation, data[terms[i].argument[0]])
                elif terms[i].argument[0] in register.keys():  # REG
                    terms[i] = Term(terms[i].line, terms[i].operation, terms[i].argument[0])
                else:  # Err please
                    terms[i] = Term(terms[i].line, terms[i].operation, terms[i].argument[0])

        code.append({'opcode': symbol2opcode[terms[i].operation], 'term': terms[i]})

    return code


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
