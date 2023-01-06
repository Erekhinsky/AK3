from translator import *
from machine import *


class Simulator:

    def __init__(self):
        self.source_file = "C:/Users/dron1/PycharmProjects/pythonProject/source.txt"
        self.code_file = "C:/Users/dron1/PycharmProjects/pythonProject/target.txt"
        self.input_file = "C:/Users/dron1/PycharmProjects/pythonProject/input.txt"

        self.data_memory_size = 200
        self.limit = 30000

        self.data_path = DataPath
        self.control_unit = ControlUnit

        self.instr_counter = 0

    def start_translator(self):
        with open(self.source_file, "rt", encoding="utf-8") as f:
            source = f.read()

        code = translate(source)
        print("source LoC:", len(source.split()), "code instr:", len(code))
        write_code(self.code_file, code)

    def start_processor(self):

        code = read_code(self.code_file)

        with open(self.input_file, encoding="utf-8") as file:
            input_text = file.read()
            input_token = []
            for char in input_text:
                input_token.append(char)

        self.data_path = DataPath(self.data_memory_size, input_token)
        self.control_unit = ControlUnit(code, self.data_path)

        # logging.debug('%s', self.control_unit)
        try:
            while True:
                assert self.limit > self.instr_counter, "too long execution, increase limit!"
                self.control_unit.decode_and_execute_instruction()
                self.instr_counter += 1
                logging.debug('%s', self.control_unit)
        except EOFError:
            logging.warning('Input buffer is empty!')
        except StopIteration:
            pass
        # logging.info('output_buffer: %s', repr(''.join(data_path.output_buffer)))
        output, instr_counter, ticks = ''.join(self.data_path.output_buffer), str(self.instr_counter), str(
            self.control_unit.current_tick())

        print("Program Complete")
        print(''.join(output))
        print("instr_counter:", str(instr_counter), "ticks:", str(ticks))


def main():
    simulator = Simulator()
    Simulator.start_translator(simulator)
    simulator.start_processor()


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    main()
