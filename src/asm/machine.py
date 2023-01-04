#!/usr/bin/python3
# pylint: disable=missing-function-docstring  # чтобы не быть Капитаном Очевидностью
# pylint: disable=invalid-name                # сохраним традиционные наименования сигналов
# pylint: disable=consider-using-f-string     # избыточный синтаксис
import json
import logging
import sys

from isa import Opcode, Term
from src.asm.translator import read_code


class DataPath:

    def __init__(self, data_memory_size, input_buffer):
        # assert data_memory_size > 0, "Data_memory size should be non-zero"
        self.data_memory_size = data_memory_size
        self.data_memory = [0] * data_memory_size

        self.acc = 0
        self.addr = 0
        self.input_buffer = input_buffer
        self.output_buffer = []

    def alu(self, sel):
        if sel == Opcode.MOD:
            self.acc = self.acc / self.data_memory[self.addr]
        elif sel == Opcode.CMP or sel == Opcode.SUB:
            self.acc = self.acc - self.data_memory[self.addr]
        elif sel == Opcode.ADD:
            self.acc = self.acc + self.data_memory[self.addr]
        else:
            print("ALU Err")

    def latch_acc(self, sel):
        if sel == Opcode.INC:
            self.acc = self.acc + 1
        elif sel == Opcode.DEC:
            self.acc = self.acc - 1
        elif sel == Opcode.MOD or sel == Opcode.SUB or sel == Opcode.ADD or sel == Opcode.CMP:
            self.alu(sel)
        elif sel == Opcode.LD_VAL:
            self.acc = self.data_memory[self.addr]
        elif sel == Opcode.LD_ADDR:
            self.acc = self.addr
        else:
            print("Latch ACC Err")

    def latch_addr(self, sel):
        if sel == self.acc:
            self.addr = self.acc
        else:
            self.addr = sel

    def zero(self):
        return self.acc == 0

    # def output(self):
    #
    #     symbol = chr(self.acc)
    #     logging.debug('output: %s << %s', repr(
    #         ''.join(self.output_buffer)), repr(symbol))
    #     self.output_buffer.append(symbol)
    #
    # def input(self):
    #
    #     if self.sr == 1:
    #
    #     if len(self.input_buffer) == 0:
    #         raise EOFError()
    #     symbol = self.input_buffer.pop(0)
    #     symbol_code = ord(symbol)
    #     assert -128 <= symbol_code <= 127, \
    #         "input token is out of bound: {}".format(symbol_code)
    #     self.data_memory[self.data_address] = symbol_code
    #     logging.debug('input: %s', repr(symbol))


class ControlUnit:

    def __init__(self, program, data_path):
        self.ip = 0
        self.sr = 2
        self.data_path = data_path
        self.program = program
        self._tick = 0

    def tick(self):
        """Счётчик тактов процессора. Вызывается при переходе на следующий такт."""
        self._tick += 1

    def current_tick(self):
        return self._tick

    def latch_ip(self, sel):
        if sel:
            self.ip += 1
        else:
            self.ip = self.program[self.ip]["term"].argument

    def latch_sr(self, sel):
        self.sr = sel

    def decode_and_execute_instruction(self):

        instr = self.program[self.ip]
        print(instr)
        opcode = instr["opcode"]

        if opcode is Opcode.HLT:
            print("HLT!!!")
            raise StopIteration()

        elif opcode is Opcode.JMP:
            self.latch_ip(False)
            self.tick()

        elif opcode is Opcode.JE:
            if self.data_path.zero == 0:
                self.latch_ip(False)
            else:
                self.latch_ip(True)
            self.tick()

        elif opcode in {Opcode.CMP, Opcode.LD_ADDR, Opcode.ADD, Opcode.SUB, Opcode.MOD}:
            self.data_path.addr = instr["term"].argument
            self.tick()
            self.data_path.latch_acc(opcode)
            self.latch_ip(True)
            self.tick()

        elif opcode in {Opcode.DEC, Opcode.INC}:
            self.data_path.latch_acc(opcode)
            self.latch_ip(True)
            self.tick()

        elif opcode is Opcode.LD_VAL:

            if instr["term"].argument == "AC":
                self.data_path.addr = self.data_path.acc
            else:
                self.data_path.addr = instr["term"].argument

            self.tick()
            self.data_path.latch_acc(opcode)
            self.latch_ip(True)
            self.tick()

            print("ACC: ", self.data_path.acc)

        elif opcode is Opcode.ST:
            self.data_path.addr = instr["term"].argument
            self.tick()
            self.data_path.data_memory[self.data_path.addr] = self.data_path.acc
            self.latch_ip(True)
            self.tick()

        elif opcode is Opcode.IN:
            while True:
                if self.sr == 1:
                    if len(self.data_path.input_buffer) == 0:
                        raise EOFError()
                    symbol = self.data_path.input_buffer.pop(0)
                    self.tick()
                    self.data_path.acc = symbol
                    logging.debug('input: %s', repr(symbol))
                    self.sr = 0
                    self.tick()
                    break

        elif opcode is Opcode.OUT:
            while True:
                if self.sr == 2:
                    symbol = self.data_path.acc
                    self.tick()
                    # logging.debug('output: %s << %s', repr(
                    #     ''.join(self.data_path.output_buffer)), repr(symbol))
                    self.data_path.output_buffer.append(symbol)
                    self.latch_ip(True)
                    self.tick()
                    print("OUT OK")
                    break

        elif opcode is Opcode.DATA:
            self.latch_ip(True)

        else:
            print("Operation decode Err: ", opcode)

        """ if opcode is Opcode.JMP:
            addr = instr["arg"]
            self.program_counter = addr
            self.tick()

        elif opcode is Opcode.JZ:
            addr = instr["arg"]

            self.data_path.latch_acc()
            self.tick()

            if self.data_path.zero():
                self.latch_program_counter(sel_next=False)
            else:
                self.latch_program_counter(sel_next=True)
            self.tick()
        else:
            if opcode in {Opcode.RIGHT, Opcode.LEFT}:
                self.data_path.latch_data_addr(opcode.value)
                self.latch_program_counter(sel_next=True)
                self.tick()

            elif opcode in {Opcode.INC, Opcode.DEC, Opcode.INPUT}:
                self.data_path.latch_acc()
                self.tick()

                self.data_path.wr(opcode.value)
                self.latch_program_counter(sel_next=True)
                self.tick()

            elif opcode is Opcode.PRINT:
                self.data_path.latch_acc()
                self.tick()

                self.data_path.output()
                self.latch_program_counter(sel_next=True)
                self.tick()
        """

    # def output(self):
    #     while True:
    #         if self.sr == 2:
    #             symbol = self.data_path.acc
    #             logging.debug('output: %s << %s', repr(
    #                 ''.join(self.data_path.output_buffer)), repr(symbol))
    #             self.data_path.output_buffer.append(symbol)
    #             self.sr = 0
    #             break

        # symbol = chr(self.acc)
        # logging.debug('output: %s << %s', repr(
        #     ''.join(self.output_buffer)), repr(symbol))
        # self.output_buffer.append(symbol)

    # def input(self):
    #     while True:
    #         if self.sr == 1:
    #             if len(self.data_path.input_buffer) == 0:
    #                 raise EOFError()
    #             symbol = self.data_path.input_buffer.pop(0)
    #             self.data_path.acc = symbol
    #             logging.debug('input: %s', repr(symbol))
    #             self.sr = 0
    #             break

        # if len(self.input_buffer) == 0:
        #     raise EOFError()
        # symbol = self.input_buffer.pop(0)
        # symbol_code = ord(symbol)
        # assert -128 <= symbol_code <= 127, \
        #     "input token is out of bound: {}".format(symbol_code)
        # self.data_memory[self.data_address] = symbol_code
        # logging.debug('input: %s', repr(symbol))

    # def __repr__(self):
    #     state = "{{TICK: {}, IP: {}, ADDR: {}, OUT: {}, ACC: {}}}".format(
    #         self._tick,
    #         self.ip,
    #         self.data_path.addr,
    #         self.data_path.data_memory[self.data_path.addr],
    #         self.data_path.acc,
    #     )
    #
    #     instr = self.program[self.ip]
    #     opcode = instr["opcode"]
    #     arg = instr.get("arg", "")
    #     term = instr["term"]
    #     action = "{} {} ('{}' @ {}:{})".format(opcode, arg, term.symbol, term.line, term.pos)
    #
    #     return "{} {}".format(state, action)


# class Machine:
#
#     def __init__(self, input_tokens, data_memory_size, limit):
#         self.sr = 0
#         self.input_tokens = input_tokens
#         self.data_memory_size = data_memory_size
#         self.limit = limit
#
#     def latch_sr(self, sel):
#         if sel == 1:
#             self.sr = 1
#         elif sel == 2:
#             self.sr = 2
#
#     def read_code(self, filename):
#         with open(filename, encoding="utf-8") as file:
#             code = json.loads(file.read())
#
#         for instr in code:
#             instr['opcode'] = Opcode(instr['opcode'])
#             if 'term' in instr:
#                 instr['term'] = Term(instr['term'][0], instr['term'][1], instr['term'][2])
#
#         return code
#
#     def simulation(self, code):
#         data_path = DataPath(self.data_memory_size, self.input_tokens)
#         control_unit = ControlUnit(code, data_path)
#         instr_counter = 0
#
#         logging.debug('%s', control_unit)
#         try:
#             while True:
#                 assert self.limit > instr_counter, "too long execution, increase limit!"
#                 control_unit.decode_and_execute_instruction()
#                 instr_counter += 1
#                 logging.debug('%s', control_unit)
#         except EOFError:
#             logging.warning('Input buffer is empty!')
#         except StopIteration:
#             pass
#         logging.info('output_buffer: %s', repr(''.join(data_path.output_buffer)))
#         return ''.join(data_path.output_buffer), instr_counter, control_unit.current_tick()


def simulation(code, input_tokens, data_memory_size, limit):

    data_path = DataPath(data_memory_size, input_tokens)
    control_unit = ControlUnit(code, data_path)
    instr_counter = 0

    logging.debug('%s', control_unit)
    try:
        while True:
            assert limit > instr_counter, "too long execution, increase limit!"
            control_unit.decode_and_execute_instruction()
            instr_counter += 1
            logging.debug('%s', control_unit)
    except EOFError:
        logging.warning('Input buffer is empty!')
    except StopIteration:
        pass
    logging.info('output_buffer: %s', repr(''.join(data_path.output_buffer)))
    return ''.join(data_path.output_buffer), instr_counter, control_unit.current_tick()


def main(args):
    assert len(args) == 2, "Wrong arguments: machine.py <code_file> <input_file>"
    code_file, input_file = args

    code = read_code(code_file)
    with open(input_file, encoding="utf-8") as file:
        input_text = file.read()
        input_token = []
        for char in input_text:
            input_token.append(char)

    output, instr_counter, ticks = simulation(code, input_tokens=input_token, data_memory_size=200, limit=3000)

    print("OK")
    print(''.join(output))
    print("instr_counter: ", instr_counter, "ticks:", ticks)


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    main(sys.argv[1:])

