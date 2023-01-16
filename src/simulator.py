import logging
import sys

from src.machine import DataPath, ControlUnit
from src.translator import translate, write_code, read_code


class Simulator:

    def __init__(self, source_file, code_file, input_file, debug_file):
        # self.source_file = "C:/Users/dron1/PycharmProjects/pythonProject/src/asm_code/cat.txt"
        # self.source_file = "C:/Users/dron1/PycharmProjects/pythonProject/src/asm_code/prob1.txt"
        self.in_file = "C:/Users/dron1/PycharmProjects/pythonProject/src/embedded_code/in.txt"
        self.out_file = "C:/Users/dron1/PycharmProjects/pythonProject/src/embedded_code/out.txt"
        self.source_file = source_file
        self.code_file = code_file
        self.input_file = input_file
        self.debug_file = debug_file

        self.data_memory_size = 200
        self.limit = 30000

        self.data_path = DataPath
        self.control_unit = ControlUnit

        self.instr_counter = 0

    def start_translator(self):
        with open(self.source_file, "rt", encoding="utf-8") as f:
            source = f.read()
        try:
            code = translate(source)
            print("source LoC:", len(source.split()), "code instr:", len(code))
            write_code(self.code_file, code)
        except AttributeError:
            logging.debug('Unknown command')
        except EOFError:
            logging.debug('Empty Line')

    def translate_embedded_code(self):
        embedded_code = [3, 10]

        with open(self.in_file, "rt", encoding="utf-8") as f:
            source = f.read()
        try:
            embedded_code += translate(source)[1:]
        except AttributeError:
            logging.debug('Unknown command')
        except EOFError:
            logging.debug('Empty Line')

        with open(self.out_file, "rt", encoding="utf-8") as f:
            source = f.read()
        try:
            embedded_code += translate(source)[1:]
        except AttributeError:
            logging.debug('Unknown command')
        except EOFError:
            logging.debug('Empty Line')

        return embedded_code

    def start_processor(self):

        open(self.debug_file, 'w').close()

        code = read_code(self.code_file)

        with open(self.input_file, encoding="utf-8") as file:
            input_text = file.read()
            input_token = []
            for char in input_text:
                input_token.append(char)

        embedded_code = self.translate_embedded_code()
        self.data_path = DataPath(self.data_memory_size, input_token, embedded_code + code)
        self.control_unit = ControlUnit(len(embedded_code), self.data_path)

        logging.debug("%s", self.control_unit)
        try:
            while True:
                assert self.limit > self.instr_counter, "too long execution, increase limit!"
                self.control_unit.decode_and_execute_instruction()
                self.instr_counter += 1
                logging.debug("%s", self.control_unit)
        except EOFError:
            logging.debug('Input buffer is empty!')
        except AttributeError:
            logging.debug('Unknown command')
        except StopIteration:
            pass
        logging.info('output_buffer: %s', repr(''.join(self.data_path.output_buffer)))
        output, instr_counter, ticks = ''.join(self.data_path.output_buffer), str(self.instr_counter), str(
            self.control_unit.current_tick())

        print("Program Complete")
        print(''.join(output))
        print("instr_counter:", str(instr_counter), "ticks:", str(ticks))


def main(args):
    source_file, code_file, input_file, debug_file = args
    simulator = Simulator(source_file, code_file, input_file, debug_file)
    Simulator.start_translator(simulator)
    simulator.start_processor()


if __name__ == '__main__':
    logging.basicConfig(filename="C:/Users/dron1/PycharmProjects/pythonProject/src/files/debug.txt", level=logging.DEBUG)
    # logging.getLogger().setLevel(logging.DEBUG)
    main(sys.argv[1:])
