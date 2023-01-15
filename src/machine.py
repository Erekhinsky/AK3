#!/usr/bin/python3
# pylint: disable=missing-function-docstring  # чтобы не быть Капитаном Очевидностью
# pylint: disable=invalid-name                # сохраним традиционные наименования сигналов
# pylint: disable=consider-using-f-string     # избыточный синтаксис

import logging
import re
import sys

from isa import Opcode


def is_int(s):
    return re.match(r"[-+]?\d+(\.0*)?$", s) is not None


class DataPath:

    def __init__(self, data_memory_size, input_buffer):
        assert data_memory_size > 0, "Data_memory size should be non-zero"
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
            print("Invalid ALU command")
            sys.exit()

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
            print("Invalid Latch ACC command")
            sys.exit()

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
                    self.latch_ip(True)
                    self.tick()
                    break

        elif opcode is Opcode.OUT:
            while True:
                self.latch_sr(opcode)
                if self.sr == 2:
                    symbol = str(self.data_path.acc)
                    self.tick()
                    logging.debug('output: %s << %s', repr(''.join(self.data_path.output_buffer)), repr(symbol))
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
            sys.exit()

    def __repr__(self):
        state = "{{TICK: {}, IP: {}, ADDR: {}, DATA: {}, ACC: {}}}".format(
            self._tick,
            self.ip,
            self.data_path.addr,
            self.data_path.data_memory[self.data_path.addr],
            self.data_path.acc,
        )

        instr = self.program[self.ip]
        opcode = instr["opcode"]
        if instr["term"].argument == []:
            action = "{}".format(opcode)
        else:
            action = "{} {}".format(opcode, instr["term"].argument)

        return "{} {}".format(state, action)
