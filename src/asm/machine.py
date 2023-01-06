#!/usr/bin/python3
# pylint: disable=missing-function-docstring  # чтобы не быть Капитаном Очевидностью
# pylint: disable=invalid-name                # сохраним традиционные наименования сигналов
# pylint: disable=consider-using-f-string     # избыточный синтаксис

import logging
import re

from isa import Opcode


def is_int(s):
    return re.match(r"[-+]?\d+(\.0*)?$", s) is not None


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
            self.acc = self.acc % self.data_memory[self.addr]
        elif sel == Opcode.SUB:
            self.acc = self.acc - self.data_memory[self.addr]
        elif sel == Opcode.CMP:
            if self.acc == self.data_memory[self.addr]:
                self.acc = 0
            else:
                self.acc = 1
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


class ControlUnit:

    def __init__(self, program, data_path):
        self.ip = 0
        self.sr = 0
        self.data_path = data_path
        self.program = program
        self._tick = 0

    def tick(self):
        self._tick += 1

    def current_tick(self):
        return self._tick

    def latch_ip(self, sel):
        if sel:
            self.ip += 1
        else:
            self.ip = self.program[self.ip]["term"].argument

    def latch_sr(self, sel):
        if sel == Opcode.OUT:
            sr = int(input("Ожидается вывод, вы готовы? (2 - если да)\n"))
            self.sr = sr
        elif sel == Opcode.IN:
            sr = int(input("Ожидается ввод, вы готовы? (1 - если да)\n"))
            self.sr = sr

    def decode_and_execute_instruction(self):

        instr = self.program[self.ip]
        print(instr)
        opcode = instr["opcode"]

        if opcode is Opcode.HLT:
            raise StopIteration()

        elif opcode is Opcode.JMP:
            self.latch_ip(False)
            self.tick()

        elif opcode is Opcode.JE:
            if self.data_path.acc == 0:
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

        elif opcode is Opcode.ST:
            self.data_path.addr = instr["term"].argument
            self.tick()
            self.data_path.data_memory[self.data_path.addr] = self.data_path.acc
            self.latch_ip(True)
            self.tick()

        elif opcode is Opcode.IN:
            while True:
                self.latch_sr(opcode)
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
                self.latch_sr(opcode)
                if self.sr == 2:
                    symbol = str(self.data_path.acc)
                    self.tick()
                    # logging.debug('output: %s << %s', repr(
                    #     ''.join(self.data_path.output_buffer)), repr(symbol))
                    self.data_path.output_buffer.append(symbol)
                    self.latch_ip(True)
                    self.tick()
                    break

        elif opcode is Opcode.DATA:
            self.data_path.addr = self.ip
            self.tick()
            if is_int(instr["term"].argument):
                self.data_path.data_memory[self.data_path.addr] = int(instr["term"].argument)
            else:
                self.data_path.data_memory[self.data_path.addr] = instr["term"].argument
            self.latch_ip(True)
            self.tick()

        else:
            print("Operation decode Err: ", opcode)


# def simulation(code, input_tokens, data_memory_size, limit):
#     data_path = DataPath(data_memory_size, input_tokens)
#     control_unit = ControlUnit(code, data_path)
#     instr_counter = 0
#
#     logging.debug('%s', control_unit)
#     try:
#         while True:
#             assert limit > instr_counter, "too long execution, increase limit!"
#             control_unit.decode_and_execute_instruction()
#             instr_counter += 1
#             logging.debug('%s', control_unit)
#     except EOFError:
#         logging.warning('Input buffer is empty!')
#     except StopIteration:
#         pass
#     # logging.info('output_buffer: %s', repr(''.join(data_path.output_buffer)))
#     return ''.join(data_path.output_buffer), str(instr_counter), str(control_unit.current_tick())


# def latch_sr(control_unit, sel):
#     control_unit.latch_sr(sel)

# def main(args):
#     assert len(args) == 2, "Wrong arguments: machine.py <code_file> <input_file>"
#     code_file, input_file = args
#
#     code_file = "C:/Users/dron1/PycharmProjects/pythonProject/target.txt"
#     input_file = "C:/Users/dron1/PycharmProjects/pythonProject/input.txt"
#
#     code = read_code(code_file)
#
#     with open(input_file, encoding="utf-8") as file:
#         input_text = file.read()
#         input_token = []
#         for char in input_text:
#             input_token.append(char)
#
#     output, instr_counter, ticks = simulation(code, input_tokens=input_token, data_memory_size=200, limit=30000)
#
#     print("Program Complete")
#     print(''.join(output))
#     print("instr_counter:", str(instr_counter), "ticks:", str(ticks))
#
#
# if __name__ == '__main__':
#     logging.getLogger().setLevel(logging.DEBUG)
#     main(sys.argv[1:])
