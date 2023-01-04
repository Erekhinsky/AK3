"""
Здесь пользователь "записывает код" и запускает машину, а также меняет регистр sr
"""
from src.asm.machine import ControlUnit


def main():

    control_unit = ControlUnit

    print("Это регистр внешнего устройства, вы решаете, когда происходит ввод/вывод!")

    while True:
        sr = input("\nВведите 1 для ввода, 2 для вывода, 0 в ином случае, 3 чтобы выйти")
        if sr == 3:
            break
        control_unit.latch_sr(control_unit, sr)


if __name__ == '__main__':
    main()
