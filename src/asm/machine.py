#!/usr/bin/python3
# pylint: disable=missing-function-docstring  # чтобы не быть Капитаном Очевидностью
# pylint: disable=invalid-name                # сохраним традиционные наименования сигналов
# pylint: disable=consider-using-f-string     # избыточный синтаксис

import logging
import sys

from isa import Opcode, read_code


class DataPath:

    """Тракт данных (пассивный), включая: ввод/вывод, память и арифметику.

                     +--------------+  addr   +--------+
               +---->| data_address |---+---->|  data  |
               |     +--------------+   |     | memory |
           +-------+                    |     |        |
    sel -->|  MUX  |         +----------+     |        |
           +-------+         |                |        |
            ^     ^          |                |        |
            |     |          |        data_in |        | data_out
            |     +---(+1)---+          +---->|        |-----+
            |                |          |     |        |     |
            +---------(-1)---+          |  oe |        |     |
                                        | --->|        |     |
                                        |     |        |     |
                                        |  wr |        |     |
                                        | --->|        |     |
                                        |     +--------+     |
                                        |                    v
                                    +--------+     latch  +-----+
                          sel ----> |  MUX   |    ------->| acc |
                                    +--------+            +-----+
                                     ^   ^  ^                |
                                     |   |  |                +---(==0)---> zero
                                     |   |  |                |
                                     |   |  +---(+1)---------+
                                     |   |                   |
                                     |   +------(-1)---------+
                                     |                       |
            input -------------------+                       +---------> output


    - data_memory -- однопортовая, поэтому либо читаем, либо пишем.
    - input/output -- токенизированная логика ввода-вывода. Не детализируется.
    - input -- может вызвать остановку процесса моделирования,
      если буфер входных значений закончился.

    Реализованные методы соответствуют группам активированных сигналов.
    Сигнал "исполняется" за один такт. Корректность использования сигналов за
    один такт -- задача ControlUnit.
    """

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

    def output(self):
        """oe от Output Enable. Вывести слово на порт ввода/вывода.

        Вывод:

        - производится через ASCII-символы по спецификации;
        - вывод осуществляется просто в буфер.
        """
        symbol = chr(self.acc)
        logging.debug('output: %s << %s', repr(
            ''.join(self.output_buffer)), repr(symbol))
        self.output_buffer.append(symbol)

    def wr(self, sel):
        """wr (от WRite), сохранить в память."""
        assert sel in {Opcode.INC.value, Opcode.DEC.value, Opcode.INPUT.value}, \
            "internal error, incorrect selector: {}".format(sel)

        if sel == Opcode.INC.value:
            self.data_memory[self.data_address] = self.acc + 1
            if self.data_memory[self.data_address] == 128:
                self.data_memory[self.data_address] = -128
        elif sel == Opcode.DEC.value:
            self.data_memory[self.data_address] = self.acc - 1
            if self.data_memory[self.data_address] == -129:
                self.data_memory[self.data_address] = 127
        elif sel == Opcode.INPUT.value:
            if len(self.input_buffer) == 0:
                raise EOFError()
            symbol = self.input_buffer.pop(0)
            symbol_code = ord(symbol)
            assert -128 <= symbol_code <= 127, \
                "input token is out of bound: {}".format(symbol_code)
            self.data_memory[self.data_address] = symbol_code
            logging.debug('input: %s', repr(symbol))

    def zero(self):
        return self.acc == 0


class ControlUnit:

    def __init__(self, program, data_path):
        self.program = program
        self.ip = 1
        self.data_path = data_path
        self._tick = 0

    def tick(self):
        """Счётчик тактов процессора. Вызывается при переходе на следующий такт."""
        self._tick += 1

    def current_tick(self):
        return self._tick

    def latch_ip(self, sel_next):
        if sel_next:
            self.ip += 1
        else:
            instr = self.program[self.ip]
            assert 'arg' in instr, "internal error"
            self.ip = instr["arg"]

    """def latch_addr(self, sel):
        if sel:
            self.data_path.addr = instr["arg"]
        else:
            self.data_path.addr = self.data_path.acc
    """

    def decode_and_execute_instruction(self):

        instr = self.program[self.ip]
        opcode = instr["opcode"]

        if opcode is Opcode.HLT:
            raise StopIteration()

        elif opcode is Opcode.JMP:
            self.ip = instr["arg"]
            self.tick()

        elif opcode is Opcode.JE:
            if self.data_path.zero == 0:
                self.ip = instr["arg"]
                self.latch_ip(False)
                self.tick()
            else:
                self.latch_ip(True)

        elif opcode is Opcode.CMP:
            self.data_path.addr = instr["arg"]
            self.tick()
            self.data_path.latch_acc(opcode)
            self.latch_ip(True)
            self.tick()

        elif opcode is Opcode.DEC:
            self.data_path.latch_acc(opcode)
            self.latch_ip(True)
            self.tick()

        elif opcode is Opcode.INC:
            self.data_path.latch_acc(opcode)
            self.latch_ip(True)
            self.tick()

        elif opcode is Opcode.LD_VAL:

            if instr["arg"] == "AC":
                self.data_path.addr = self.data_path.acc
            else:
                self.data_path.addr = instr["arg"]

            self.tick()
            self.data_path.latch_acc(opcode)
            self.latch_ip(True)
            self.tick()

        elif opcode is Opcode.LD_ADDR:
            self.data_path.addr = instr["arg"]
            self.tick()
            self.data_path.latch_acc(opcode)
            self.latch_ip(True)
            self.tick()

        elif opcode is Opcode.ADD:
            self.data_path.addr = instr["arg"]
            self.tick()
            self.data_path.latch_acc(opcode)
            self.latch_ip(True)
            self.tick()

        elif opcode is Opcode.SUB:
            self.data_path.addr = instr["arg"]
            self.tick()
            self.data_path.latch_acc(opcode)
            self.latch_ip(True)
            self.tick()

        elif opcode is Opcode.ST:
            self.data_path.addr = instr["arg"]
            self.tick()
            self.data_path.data_memory[self.data_path.addr] = self.data_path.acc
            self.latch_ip(True)
            self.tick()

        elif opcode is Opcode.MOD:
            self.data_path.addr = instr["arg"]
            self.tick()
            self.data_path.latch_acc(opcode)
            self.latch_ip(True)
            self.tick()

        elif opcode is Opcode.IN:
            print("IN")

        elif opcode is Opcode.OUT:
            print("OUT")

        else:
            print("Err")

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

    def __repr__(self):
        state = "{{TICK: {}, IP: {}, ADDR: {}, OUT: {}, ACC: {}}}".format(
            self._tick,
            self.ip,
            self.data_path.addr,
            self.data_path.data_memory[self.data_path.addr],
            self.data_path.acc,
        )

        instr = self.program[self.ip]
        opcode = instr["opcode"]
        arg = instr.get("arg", "")
        term = instr["term"]
        action = "{} {} ('{}' @ {}:{})".format(opcode, arg, term.symbol, term.line, term.pos)

        return "{} {}".format(state, action)


def simulation(code, input_tokens, data_memory_size, limit):
    """Запуск симуляции процессора.

    Длительность моделирования ограничена количеством выполненных инструкций.
    """
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

    output, instr_counter, ticks = simulation(code, input_tokens=input_token, data_memory_size=100, limit=1000)

    print(''.join(output))
    print("instr_counter: ", instr_counter, "ticks:", ticks)


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    main(sys.argv[1:])
