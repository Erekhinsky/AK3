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

    def __init__(self, data_memory_size, input_buffer, embedded_code):
        assert data_memory_size > len(embedded_code), "Data_memory_size should be > " + str(len(embedded_code))

        self.data_memory_size = data_memory_size
        self.data_memory = embedded_code
        self.size_embedded_code = len(embedded_code)
        for i in range(self.size_embedded_code, self.data_memory_size):
            self.data_memory.append(0)

        self.acc = 0
        self.addr = 0
        self.input_buffer = input_buffer
        self.output_buffer = []

        self.vector = {1: None, 2: None}

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
            raise AttributeError

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
            raise AttributeError

    def latch_addr(self, sel):
        if sel == self.acc:
            self.addr = self.acc
        else:
            self.addr = sel

    def load_program(self, program):
        for i in range(self.size_embedded_code, len(program)):
            j = 0
            self.data_memory[i] = program[j]
            j += 1
        return self.size_embedded_code


class ControlUnit:

    def __init__(self, program, data_path):
        self.interrupt = 0
        self.data_path = data_path
        self.ip = self.data_path.load_program(program)
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

    def decode_and_execute_instruction(self):

        instr = self.data_path.data_memory[self.ip]
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
            if instr["term"].argument:
                self.interrupt = instr["term"].argument
                self.tick()
                self.data_path.vector[self.interrupt] = [self.data_path.addr, self.ip]
                self.ip = self.data_path.data_memory[self.interrupt]
                self.tick()
            else:
                if len(self.data_path.input_buffer) == 0:
                    raise EOFError()
                symbol = self.data_path.input_buffer.pop(0)
                self.data_path.acc = symbol
                logging.debug('input: %s', repr(symbol))
                self.latch_ip(True)
                self.tick()
                if self.interrupt:
                    self.data_path.addr, self.ip = self.data_path.vector[self.interrupt]
                    self.tick()
                    self.interrupt = 0

        elif opcode is Opcode.OUT:
            if instr["term"].argument:
                self.interrupt = int(instr["term"].argument)
                self.tick()
                self.data_path.vector[self.interrupt] = [self.data_path.addr, self.data_path.acc, self.ip]
                self.ip = self.data_path.data_memory[self.interrupt]
                self.tick()
            else:
                symbol = str(self.data_path.acc)
                self.tick()
                logging.debug('output: %s << %s', repr(''.join(self.data_path.output_buffer)), repr(symbol))
                self.data_path.output_buffer.append(symbol)
                self.latch_ip(True)
                self.tick()
                if self.interrupt:
                    self.data_path.addr, self.data_path.acc, self.ip = self.data_path.vector[self.interrupt]
                    self.tick()
                    self.interrupt = 0

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
            raise AttributeError

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
