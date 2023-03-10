#!/usr/bin/python3
# pylint: disable=missing-function-docstring  # чтобы не быть Капитаном Очевидностью
# pylint: disable=invalid-name                # сохраним традиционные наименования сигналов
# pylint: disable=consider-using-f-string     # избыточный синтаксис

import logging
import re

from isa import Opcode


def is_int(s):
    return re.match(r"[-+]?\d+(\.0*)?$", s) is not None


def to_term(arg):
    return {'term': ['data', arg]}


class DataPath:

    def __init__(self, data_memory_size, input_buffer, vector, embedded_code, device_file):
        assert data_memory_size > len(embedded_code), "Data_memory_size should be > " + str(len(embedded_code) + len(vector))

        self.data_memory_size = data_memory_size
        self.data_memory = vector + embedded_code
        for i in range(len(embedded_code) + len(vector), self.data_memory_size):
            self.data_memory.append(0)

        self.acc = 0
        self.addr = 0
        self.sr = 0

        self.input_buffer = input_buffer
        self.output_buffer = []
        self.device_file = device_file

        self.vector = {1: None, 2: None}

    def alu(self, sel):
        if sel == Opcode.MOD:
            self.acc = to_term(self.acc['term'][1] % self.data_memory[self.addr]['term'][1])
        elif sel == Opcode.SUB:
            self.acc = to_term(self.acc['term'][1] - self.data_memory[self.addr]['term'][1])
        elif sel == Opcode.CMP:
            if self.addr == "SR":
                self.addr = 0
                if self.acc['term'][1] == self.sr or self.sr == 3:
                    self.acc = to_term(0)
                else:
                    self.acc = to_term(1)
            else:
                if self.acc['term'][1] == self.data_memory[self.addr]['term'][1]:
                    self.acc = to_term(0)
                else:
                    self.acc = to_term(1)
        elif sel == Opcode.ADD:
            self.acc = to_term(self.acc['term'][1] + self.data_memory[self.addr]['term'][1])
        else:
            raise AttributeError

    def latch_acc(self, sel):
        if sel == Opcode.INC:
            self.acc = to_term(self.acc['term'][1] + 1)
        elif sel == Opcode.DEC:
            self.acc = to_term(self.acc['term'][1] - 1)
        elif sel == Opcode.MOD or sel == Opcode.SUB or sel == Opcode.ADD or sel == Opcode.CMP:
            self.alu(sel)
        elif sel == Opcode.LD_VAL:
            self.acc = self.data_memory[self.addr]
        elif sel == Opcode.LD_ADDR:
            self.acc = to_term(self.addr)
        else:
            raise AttributeError

    def latch_sr(self):
        with open(self.device_file, encoding="utf-8") as file:
            arg = file.read()
            if arg != '':
                self.sr = int(arg)

    def latch_addr(self, sel):
        if sel == "AC":
            self.addr = self.acc['term'][1]
        elif sel == "SR":
            self.latch_sr()
            self.addr = sel
        else:
            self.addr = sel


class ControlUnit:

    def __init__(self, start, data_path):
        self.interrupt = 0
        self.data_path = data_path
        self.ip = start
        self._tick = 0

    def tick(self):
        self._tick += 1

    def current_tick(self):
        return self._tick

    def latch_ip(self, sel):
        if sel:
            self.ip += 1
        else:
            self.ip = self.data_path.data_memory[self.ip]["term"][1]

    def decode_and_execute_instruction(self):

        instr = self.data_path.data_memory[self.ip]
        opcode = instr["term"][0]

        if is_int(str(instr["term"][1])):
            argument = int(instr["term"][1])
        else:
            argument = str(instr["term"][1])

        if opcode is Opcode.HLT:
            raise StopIteration()

        elif opcode is Opcode.JMP:
            self.latch_ip(False)
            self.tick()

        elif opcode is Opcode.JE:
            if self.data_path.acc['term'][1] == 0:
                self.latch_ip(False)
            else:
                self.latch_ip(True)
            self.tick()

        elif opcode in {Opcode.LD_ADDR, Opcode.ADD, Opcode.SUB, Opcode.MOD, Opcode.CMP, Opcode.LD_VAL}:
            self.data_path.latch_addr(argument)
            self.tick()
            self.data_path.latch_acc(opcode)
            self.latch_ip(True)
            self.tick()

        elif opcode in {Opcode.DEC, Opcode.INC}:
            self.data_path.latch_acc(opcode)
            self.latch_ip(True)
            self.tick()

        elif opcode is Opcode.ST:
            self.data_path.latch_addr(argument)
            self.tick()
            self.data_path.data_memory[self.data_path.addr] = self.data_path.acc
            self.latch_ip(True)
            self.tick()

        elif opcode is Opcode.IN:
            if argument == 0:
                self.interrupt = 0
                self.data_path.vector[self.interrupt] = [self.data_path.addr, self.ip]
                self.tick()
                self.ip = self.data_path.data_memory[self.interrupt]
                self.tick()
            else:
                if len(self.data_path.input_buffer) == 0:
                    raise EOFError()
                symbol = self.data_path.input_buffer.pop(0)
                logging.debug('input: %s', repr(symbol))
                self.data_path.acc = to_term(symbol)
                if self.interrupt == 0:
                    self.data_path.addr, self.ip = self.data_path.vector[self.interrupt]
                    self.tick()
                    self.latch_ip(True)
                    self.interrupt = -1
                    self.tick()
                else:
                    self.latch_ip(True)
                    self.tick()

        elif opcode is Opcode.OUT:
            if argument == 1:
                self.interrupt = 1
                self.tick()
                self.data_path.vector[self.interrupt] = [self.data_path.addr, self.data_path.acc, self.ip]
                self.ip = self.data_path.data_memory[self.interrupt]
                self.tick()
            else:
                symbol = str(self.data_path.acc["term"][1])
                logging.debug('output: %s << %s', repr(''.join(self.data_path.output_buffer)), repr(symbol))
                self.data_path.output_buffer.append(symbol)
                if self.interrupt:
                    self.data_path.addr, self.data_path.acc, self.ip = self.data_path.vector[self.interrupt]
                    self.tick()
                    self.latch_ip(True)
                    self.interrupt = -1
                    self.tick()
                else:
                    self.latch_ip(True)
                    self.tick()

        # elif opcode is Opcode.DATA:
        #     self.data_path.addr = self.ip
        #     self.tick()
        #     # if is_int(argument):
        #     #     self.data_path.data_memory[self.data_path.addr] = int(argument)
        #     # else:
        #     self.data_path.data_memory[self.data_path.addr] = argument
        #     self.latch_ip(True)
        #     self.tick()

        else:
            raise AttributeError

    def __repr__(self):
        state = "{{TICK: {}, IP: {}, ADDR: {}, DATA: {}, ACC: {}, SR: {}}}".format(
            self._tick,
            self.ip,
            self.data_path.addr,
            self.data_path.data_memory[self.data_path.addr],
            self.data_path.acc,
            self.data_path.sr,
        )

        instr = self.data_path.data_memory[self.ip]
        opcode = instr["term"][0]
        argument = instr["term"][1]

        if argument == []:
            action = "{}".format(opcode)
        else:
            action = "{} {}".format(opcode, argument)

        return "{} {}".format(state, action)
