import os
import sys
from multiprocessing import Process
from pathlib import Path

import pytest
import pytest_timeout


BASE_DIR = Path(__file__).resolve(strict=True).parent.parent
sys.path.append(str(BASE_DIR))


TIMEOUT_ASSERT_MSG = (
    'Проект работает некорректно, проверка прервана.\n'
    'Вероятные причины ошибки:\n'
    '1. Исполняемый код (например, вызов функции `main()`) оказался в '
    'глобальной зоне видимости. Как исправить: вызов функции `main` поместите '
    'внутрь конструкции `if __name__ == "__main__":`.\n'
    '2. Возможно в вашем коде определен бесконечный цикл'
)


def import_main():
    import main  # noqa


@pytest.fixture(scope='session')
def main_import_test():
    check_import_process = Process(target=import_main)
    check_import_process.start()
    pid = check_import_process.pid
    check_import_process.join(timeout=1)
    if check_import_process.is_alive():
        os.kill(pid, 9)
        raise AssertionError(TIMEOUT_ASSERT_MSG)
    if check_import_process.exitcode not in (0, None):
        raise AssertionError(TIMEOUT_ASSERT_MSG)


@pytest.fixture(scope='session')
def _main(main_import_test):
    try:
        import main
    except ImportError as error:
        raise AssertionError(
            'При импорте модуль `main` произошла ошибка:\n'
            f'{type(error).__name__}: {error}'
        )
    return main


def write_timeout_reasons(text, stream=None):
    """Write possible reasons of tests timeout to stream.

    The function to replace pytest_timeout traceback output with possible
    reasons of tests timeout.
    Appears only when `thread` method is used.
    """
    if stream is None:
        stream = sys.stderr
    text = TIMEOUT_ASSERT_MSG
    stream.write(text)


pytest_timeout.write = write_timeout_reasons
