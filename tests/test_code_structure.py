import inspect
from pathlib import Path


def _param_names(func):
    return list(inspect.signature(func).parameters.keys())


def test_words_file():
    base_dir = Path(__file__).resolve(strict=True).parent.parent
    words_file = base_dir / "words.txt"

    assert words_file.exists() and  words_file.is_file(),(
        "Убедитесь, что в корне проекта лежит файл `words.txt`"
    )


def test_stop_word_constant(_main):
    assert hasattr(_main, "STOP_WORD"), (
        "Убедитесь, что в модуле `main` определена константа `STOP_WORD`"
    )
    assert _main.STOP_WORD == 'СТОП', (
        "Убедитесь, что в модуле `main` константа `STOP_WORD` равна строке `'СТОП'`"
    )


def test_functions_and_signatures(_main):
    expected_signatures = {
        "load_words": ["filename"],
        "print_statistics": ["score", "total_time"],
        "ask_and_check": ["word", "correct"],
        "start_game": ["words"],
        "train_until_mistake": ["words"],
        "add_words": ["words"],
        "show_all_words": ["words"],
        "save_words": ["words", "filename"],
        "main": [],
    }

    for func_name, expected_params in expected_signatures.items():
        assert hasattr(_main, func_name) and callable(getattr(_main, func_name)), (
              f"Убедитесь, что в модуле `main` определёна функция с именем `{func_name}`"
        )

        func = getattr(_main, func_name)
        current_params = _param_names(func)
        assert current_params == expected_params, (
            f"Неверная сигнатура функции `{func_name}`. \n"
            f"Ожидались параметры: `{expected_params}`, \n"
            f"сейчас: `{current_params}`"
        )
