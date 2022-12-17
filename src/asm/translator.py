import sys
from isa import Opcode, write_code, Term, Register

# словарь символов, непосредственно транслируемых в машинный код
symbol2opcode = {
    'CMP': Opcode.CMP,
    'JE': Opcode.JE,
    'MOV': Opcode.MOV,
    'DIV': Opcode.DIV,
    'MUL': Opcode.MUL,
    'INC': Opcode.INC,
    'DEC': Opcode.DEC,
    'JMP': Opcode.JMP,
    'ADD': Opcode.ADD,
    'SUB': Opcode.SUB,
    'IN': Opcode.IN,
    'OUT': Opcode.OUT,
    'HLT': Opcode.HLT,
    'data': Opcode.DATA,
}

register = {
    'AC': Register.AC,
    'BR': Register.BR,
    'SR': Register.SR,
}


def translate(text):
    terms = []
    labels = {}
    data = {}
    words_counter = 0
    code = []

    for line in text.split("\n"):
        words = line.split()
        words_counter = words_counter + 1

        if len(words) == 1 and words[0][0] == ':' and words[0][len(words) - 1] == ':':
            labels[words[0]] = words_counter
            words_counter = words_counter - 1
        elif len(labels) == 1:
            data[words[0]] = [words_counter, words[1]]
            terms.append(Term(words_counter, 'data', words[0:3]))
        else:
            terms.append(Term(words_counter, words[0], words[1:3]))

    for i in range(len(terms)):
        if terms[i].operation != 'data':
            if len(terms[i].argument) == 0:     # ...
                terms[i] = Term(terms[i].line, terms[i].operation, terms[i].argument)
            elif len(terms[i].argument) == 1:
                if terms[i].argument[0] in labels.keys():   # Label
                    terms[i] = Term(terms[i].line, terms[i].operation, labels[terms[i].argument[0]])
                elif terms[i].argument[0] in data.keys() or terms[i].argument[0][1:len(terms[i].argument[0])] in data.keys():
                    if terms[i].argument[0][0] == '&':  # &DATA
                        terms[i] = Term(terms[i].line, terms[i].operation,
                                        data[terms[i].argument[0][1:len(terms[i].argument[0])]])
                    else:   # DATA
                        terms[i] = Term(terms[i].line, terms[i].operation, data[terms[i].argument[0]])
                else:
                    terms[i] = Term(terms[i].line, terms[i].operation, terms[i].argument)
            else:   # len == 2
                if (terms[i].argument[0] in data.keys() and terms[i].argument[1] in data.keys()) or \
                        (terms[i].argument[0] in data.keys() and terms[i].argument[1][1:len(terms[i].argument[1])] in data.keys()) or \
                        (terms[i].argument[0][1:len(terms[i].argument[0])] in data.keys() and terms[i].argument[1] in data.keys()) or \
                        (terms[i].argument[0][1:len(terms[i].argument[0])] in data.keys() and terms[i].argument[1][1:len(terms[i].argument[1])] in data.keys()):
                    if terms[i].argument[0][0] == '&':
                        if terms[i].argument[1][0] == '&':  # &DATA &DATA
                            terms[i] = Term(terms[i].line, terms[i].operation,
                                            [data[terms[i].argument[0][1:len(terms[i].argument[0])]],
                                             data[terms[i].argument[1][1:len(terms[i].argument[1])]]])
                        else:   # &DATA DATA
                            terms[i] = Term(terms[i].line, terms[i].operation,
                                            [data[terms[i].argument[0][1:len(terms[i].argument[0])]],
                                             data[terms[i].argument[1]]])

                    elif terms[i].argument[1][0] == '&':    # DATA &DATA
                        terms[i] = Term(terms[i].line, terms[i].operation,
                                        [data[terms[i].argument[0]],
                                         data[terms[i].argument[1][1:len(terms[i].argument[1])]]])

                    else:   # DATA DATA
                        terms[i] = Term(terms[i].line, terms[i].operation,
                                        [data[terms[i].argument[0]], data[terms[i].argument[1]]])

                elif terms[i].argument[0] in data.keys() or terms[i].argument[0][1:len(terms[i].argument[0])] in data.keys():
                    if terms[i].argument[0][0] == '&':      # &DATA NOT_DATA
                        terms[i] = Term(terms[i].line, terms[i].operation,
                                        [data[terms[i].argument[0][1:len(terms[i].argument[0])]], terms[i].argument[1]])

                    else:   # DATA NOT_DATA
                        terms[i] = Term(terms[i].line, terms[i].operation,
                                        [data[terms[i].argument[0]], terms[i].argument[1]])

                elif terms[i].argument[1] in data.keys() or terms[i].argument[1][1:len(terms[i].argument[1])] in data.keys():
                    if terms[i].argument[1][0] == '&':  # NOT_DATA &DATA
                        print(terms[i].argument[1][1:len(terms[i].argument[1])])
                        print(data['CUR'])
                        terms[i] = Term(terms[i].line, terms[i].operation, [terms[i].argument[0],
                                                                            data[data[terms[i].argument[1][1:len(terms[i].argument[1])]][1][0]]])
                    else:   # NOT_DATA DATA
                        terms[i] = Term(terms[i].line, terms[i].operation,
                                        [terms[i].argument[0], data[terms[i].argument[1]]])

                else:   # NOT_DATA NOT_DATA
                    terms[i] = Term(terms[i].line, terms[i].operation, terms[i].argument)

        code.append({'opcode': symbol2opcode[terms[i].operation], 'term': terms[i]})

    return code


def main(args):
    assert len(args) == 2, \
        "Wrong arguments: translator.py <input_file> <target_file>"
    source, target = args

    with open(source, "rt", encoding="utf-8") as f:
        source = f.read()

    code = translate(source)
    print("source LoC:", len(source.split()), "code instr:", len(code))
    write_code(target, code)


if __name__ == '__main__':
    main(sys.argv[1:])
