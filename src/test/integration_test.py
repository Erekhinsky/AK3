# pylint: disable=missing-class-docstring     # чтобы не быть Капитаном Очевидностью
# pylint: disable=missing-function-docstring  # чтобы не быть Капитаном Очевидностью
# pylint: disable=line-too-long               # строки с ожидаемым выводом

"""Интеграционные тесты транслятора и машины"""

import contextlib
import io
import logging
import os
import tempfile

import pytest as pytest

from src import simulator

# class TestTranslator(unittest.TestCase):
#
#     def test_hello(self):
#         # Создаём временную папку для скомпилированного файла. Удаляется автоматически.
#         with tempfile.TemporaryDirectory() as tmpdirname:
#             # source = "src/asm_code/helloworld.txt"
#             # target = os.path.join(tmpdirname, "machine_code.out")
#             # input_stream = "examples/input.txt"
#
#             source_file = "/src/asm_code/helloworld.txt"
#             target = os.path.join(tmpdirname, "machine_code.out")
#             input_file = "/src/files/input.txt"
#             debug_file = "/src/files/debug.txt"
#
#             # Собираем весь стандартный вывод в переменную stdout.
#             with contextlib.redirect_stdout(io.StringIO()) as stdout:
#                 # translator.main([source, target])
#                 # machine.main([target, input_stream])
#                 simulator.main([source_file, target, input_file])
#
#             # Проверяем, что было напечатано то, что мы ожидали.
#             self.assertEqual(stdout.getvalue(),
#                              'source LoC: 57 code instr: 27\nHello World!\ninstr_counter: 197 ticks: 345\n')
#
#     def test_cat(self):
#         with tempfile.TemporaryDirectory() as tmpdirname:
#             source_file = "/src/asm_code/helloworld.txt"
#             target = os.path.join(tmpdirname, "machine_code.out")
#             input_file = "/src/files/input.txt"
#
#             with contextlib.redirect_stdout(io.StringIO()) as stdout:
#                 # Собираем журнал событий по уровню INFO в переменную logs.
#                 with self.assertLogs('', level='INFO') as logs:
#                     simulator.main([source_file, target, input_file])
#
#             self.assertEqual(stdout.getvalue(),
#                              'source LoC: 22 code instr: 10\nfoo\ninstr_counter: 55 ticks: 97\n')
#
#             self.assertEqual(logs.output,
#                              ['WARNING:root:Input buffer is empty!',
#                               "INFO:root:output_buffer: 'Hello World from input!\\n'"])
#
#     def test_cat_trace(self):
#         with tempfile.TemporaryDirectory() as tmpdirname:
#             source_file = "/src/asm_code/helloworld.txt"
#             target = os.path.join(tmpdirname, "machine_code.out")
#             input_file = "/src/files/input.txt"
#
#             with contextlib.redirect_stdout(io.StringIO()) as stdout:
#                 with self.assertLogs('', level='DEBUG') as logs:
#                     simulator.main([source_file, target, input_file])
#
#             self.assertEqual(stdout.getvalue(),
#                              'source LoC: 1 code instr: 6\nfoo\n\ninstr_counter:  15 ticks: 28\n')
#
#             expect_log = [
#                 "DEBUG:root:{TICK: 0, PC: 0, ADDR: 0, OUT: 0, ACC: 0} input  (',' @ 1:1)",
#                 "DEBUG:root:input: 'f'",
#                 "DEBUG:root:{TICK: 2, PC: 1, ADDR: 0, OUT: 102, ACC: 0} jz 5 ('[' @ 1:2)",
#                 "DEBUG:root:{TICK: 4, PC: 2, ADDR: 0, OUT: 102, ACC: 102} print  ('.' @ 1:3)",
#                 "DEBUG:root:output: '' << 'f'",
#                 "DEBUG:root:{TICK: 6, PC: 3, ADDR: 0, OUT: 102, ACC: 102} input  (',' @ 1:4)",
#                 "DEBUG:root:input: 'o'",
#                 "DEBUG:root:{TICK: 8, PC: 4, ADDR: 0, OUT: 111, ACC: 102} jmp 1 (']' @ 1:5)",
#                 "DEBUG:root:{TICK: 9, PC: 1, ADDR: 0, OUT: 111, ACC: 102} jz 5 ('[' @ 1:2)",
#                 "DEBUG:root:{TICK: 11, PC: 2, ADDR: 0, OUT: 111, ACC: 111} print  ('.' @ 1:3)",
#                 "DEBUG:root:output: 'f' << 'o'",
#                 "DEBUG:root:{TICK: 13, PC: 3, ADDR: 0, OUT: 111, ACC: 111} input  (',' @ 1:4)",
#                 "DEBUG:root:input: 'o'",
#                 "DEBUG:root:{TICK: 15, PC: 4, ADDR: 0, OUT: 111, ACC: 111} jmp 1 (']' @ 1:5)",
#                 "DEBUG:root:{TICK: 16, PC: 1, ADDR: 0, OUT: 111, ACC: 111} jz 5 ('[' @ 1:2)",
#                 "DEBUG:root:{TICK: 18, PC: 2, ADDR: 0, OUT: 111, ACC: 111} print  ('.' @ 1:3)",
#                 "DEBUG:root:output: 'fo' << 'o'",
#                 "DEBUG:root:{TICK: 20, PC: 3, ADDR: 0, OUT: 111, ACC: 111} input  (',' @ 1:4)",
#                 "DEBUG:root:input: '\\n'",
#                 "DEBUG:root:{TICK: 22, PC: 4, ADDR: 0, OUT: 10, ACC: 111} jmp 1 (']' @ 1:5)",
#                 "DEBUG:root:{TICK: 23, PC: 1, ADDR: 0, OUT: 10, ACC: 111} jz 5 ('[' @ 1:2)",
#                 "DEBUG:root:{TICK: 25, PC: 2, ADDR: 0, OUT: 10, ACC: 10} print  ('.' @ 1:3)",
#                 "DEBUG:root:output: 'foo' << '\\n'",
#                 "DEBUG:root:{TICK: 27, PC: 3, ADDR: 0, OUT: 10, ACC: 10} input  (',' @ 1:4)",
#                 'WARNING:root:Input buffer is empty!',
#                 "INFO:root:output_buffer: 'foo\\n'"]
#             self.assertEqual(logs.output, expect_log)


@pytest.mark.golden_test("golden/*.yml")
def test_whole_by_golden(golden, caplog):
    # Установим уровень отладочного вывода на DEBUG
    caplog.set_level(logging.DEBUG)

    # Создаём временную папку для тестирования приложения.
    with tempfile.TemporaryDirectory() as tmpdirname:
        # Готовим имена файлов для входных и выходных данных.
        source_file = os.path.join(tmpdirname, "/src/asm_code/helloworld.txt")
        target = os.path.join(tmpdirname, "machine_code.out")
        input_file = os.path.join(tmpdirname, "/src/files/input.txt")

        # Записываем входные данные в файлы. Данные берутся из теста.
        with open(source_file, "w", encoding="utf-8") as file:
            file.write(golden["source"])
        with open(input_file, "w", encoding="utf-8") as file:
            file.write(golden["input"])

        # Запускаем транслятор и собираем весь стандартный вывод в переменную stdout
        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            simulator.main([source_file, target, input_file])

        # Выходные данные также считываем в переменные.
        with open(target, encoding="utf-8") as file:
            code = file.read()

        # Проверяем, что ожидания соответствуют реальности.
        assert code == golden.out["code"]
        assert stdout.getvalue() == golden.out["output"]
        assert caplog.text == golden.out["log"]
