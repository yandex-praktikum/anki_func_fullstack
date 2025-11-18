import pytest
import builtins


def test_load_words(tmp_path, capsys, _main):
    # корректные/не корректные слова
    words_file = tmp_path / "words_test.txt"
    words_file.write_text(
        "cat,кот\n"
        "некорректная_строка_без_запятой\n"
        "dog,собака\n"
        "слишком,много,запятых,тут\n",
        encoding="utf-8",
    )
    result = _main.load_words(str(words_file))
    assert isinstance(result, dict), (
        "Убедитесь, что функция `load_words` возвращает словарь."
    )
    assert result == {"cat": "кот", "dog": "собака"}, (
        "Убедитесь, что `load_words` читает только корректные строки формата "
        "`слово,перевод` и игнорирует остальные."
    )

    # Пустой файл
    empty_file = tmp_path / "empty_words.txt"
    empty_file.write_text("", encoding="utf-8")
    empty_result = _main.load_words(str(empty_file))
    assert isinstance(empty_result, dict) and  empty_result == {}, (
        "Убедитесь, что при пустом файле `load_words` возвращает пустой словарь."
    )

    # Нет файла
    missing_name = tmp_path / "no_words_test.txt"
    with pytest.raises(SystemExit):
        _main.load_words(str(missing_name))

    captured = capsys.readouterr().out
    assert str(missing_name) in captured, (
        "Убедитесь, что при отсутствии файла `load_words` выводит сообщение "
        "с именем файла и завершает программу через `exit(1)`."
    )


def test_print_statistics(capsys, _main):
    _main.print_statistics(3, 8.75)
    captured = capsys.readouterr().out.strip().splitlines()
    assert captured == [
        "Ваш итоговый счет: 3",
        "Время игры: 8.75 секунд (среднее время: 2.92 сек.)",
    ], (
        "Убедитесь, что при `score=3` и `total_time=8.75` функция `print_statistics` "
        "выводит статистику точно в формате из задания."
    )

    _main.print_statistics(0, 0.0)
    captured = capsys.readouterr().out.strip().splitlines()
    assert captured == [
        "Ваш итоговый счет: 0",
        "Время игры: 0.00 секунд (среднее время: —)",
    ], (
        "Убедитесь, что при отсутствии правильных ответов (`score == 0`) "
        "среднее время выводится как прочерк (`—`) и формат строк соответствует заданию."
    )


@pytest.mark.timeout(2)
def test_ask_and_check(monkeypatch, _main):
    word = "cat"
    correct = "кот"

    calls = {"count": 0}

    def fake_input(prompt: str) -> str:
        calls["count"] += 1
        return " Стоп"

    monkeypatch.setattr("builtins.input", fake_input)

    result = _main.ask_and_check(word, correct)
    assert calls["count"] >= 1, (
        "Убедитесь, что внутри функции `ask_and_check` используется вызов `input()` "
        "для чтения ответа пользователя."
    )

    assert isinstance(result, tuple) and len(result) == 3, (
        "Убедитесь, что функция `ask_and_check` возвращает кортеж из трёх элементов."
    )
    is_stop, is_correct, answer_time = result
    assert isinstance(is_stop, bool), (
        "Убедитесь, что первый элемент кортежа, возвращаемого `ask_and_check`, "
        "имеет тип bool (флаг выхода)."
    )
    assert isinstance(is_correct, bool), (
        "Убедитесь, что второй элемент кортежа, возвращаемого `ask_and_check`, "
        "имеет тип bool (флаг правильности ответа)."
    )
    assert isinstance(answer_time, float), (
        "Убедитесь, что третий элемент кортежа, возвращаемого `ask_and_check`, "
        "имеет тип float (время ответа в секундах)."
    )
    assert is_stop is True and is_correct is False and answer_time == 0.0, (
        "Убедитесь, что при вводе завершающего слова `СТОП` (в любом регистре "
        "и с пробелами) функция `ask_and_check` возвращает `(True, False, 0.0)`."
    )

    # Корректный ответ
    monkeypatch.setattr("builtins.input", lambda _: "   КоТ   ")
    is_stop, is_correct, answer_time = _main.ask_and_check(word, correct)
    assert is_stop is False, (
        "Убедитесь, что при корректном ответе флаг `is_stop` равен False."
    )
    assert is_correct is True, (
        "Убедитесь, что сравнение ответа с правильным переводом выполняется без учёта "
        "регистра и лишних пробелов по краям (используются `strip()` и `lower()`)."
    )
    assert isinstance(answer_time, float) and answer_time >= 0.0, (
        "Убедитесь, что функция `ask_and_check` корректно считает время ответа и "
        "возвращает его в виде неотрицательного числа с типом float."
    )

    # Некорректный ответ
    for bad_answer in ["", "dog", "кот!!!"]:
        monkeypatch.setattr("builtins.input", lambda _, a=bad_answer: a)
        is_stop, is_correct, answer_time = _main.ask_and_check(word, correct)
        assert (is_stop, is_correct) == (False, False), (
            "Убедитесь, что даже при некорректных ответах функция `ask_and_check` "
            "возвращает кортеж из трёх элементов `(False, False, <время>)`."
        )


@pytest.mark.timeout(2)
def test_start_game(monkeypatch, capsys, _main):
    """Проверяем поведение функции start_game по чек-листу."""

    # Пустой словарь
    result_empty = _main.start_game({})
    out_empty = capsys.readouterr().out.lower()

    assert result_empty is None, (
        "Убедитесь, что функция `start_game` ничего не возвращает при пустом словаре"
    )
    assert out_empty, (
        "Убедитесь, что при пустом словаре `start_game` выводит сообщение "
        "о том, что слов для игры нет."
    )

    # Не пустой словарь
    words = {"cat": "кот", "dog": "собака"}
    responses = [
        (False, True, 1.5),
        (False, False, 2.0),
        (True, False, 0.0),
    ]
    state = {"index": 0}
    calls_log = []

    def fake_ask_and_check(word, correct):
        calls_log.append((word, correct))
        idx = state["index"]
        assert idx < len(responses), (
            "Убедитесь, что игровой цикл `start_game` завершается после ввода слова `CTOП`"
        )
        is_stop, is_correct, answer_time = responses[idx]
        state["index"] += 1
        return is_stop, is_correct, answer_time

    monkeypatch.setattr(_main, "ask_and_check", fake_ask_and_check)

    stats = {}

    def fake_print_statistics(score, total_time):
        stats["score"] = score
        stats["total_time"] = total_time

    monkeypatch.setattr(_main, "print_statistics", fake_print_statistics)

    _main.start_game(words)
    assert len(calls_log) == 3, (
        "Убедитесь, что `start_game` завершает игру только после ввода завершающего слова."
    )
    assert stats, (
        "Убедитесь, что после завершения игры функция `start_game` вызывает "
        "`print_statistics` для вывода итоговой статистики."
    )
    assert stats.get("score") == 1, (
        "Убедитесь, что функция `start_game` корректно считает количество "
        "правильных ответов и передаёт его в `print_statistics`."
    )
    assert "total_time" in stats and pytest.approx(stats["total_time"]) == 3.5, (
        "Убедитесь, что функция `start_game` накапливает общее время игры "
        "и передаёт его в `print_statistics`."
    )


@pytest.mark.timeout(2)
def test_train_until_mistake(monkeypatch, capsys, _main):

    words = {"cat": "кот", "dog": "собака"}
    responses = [
        (False, True, 1.0),
        (False, False, 2.0),
    ]
    state = {"index": 0}
    calls_log = []

    def fake_ask_and_check(word, correct):
        calls_log.append((word, correct))
        idx = state["index"]
        assert idx < len(responses), (
            "Убедитесь, что при неправильном ответе игра прерывается."
        )
        is_stop, is_correct, answer_time = responses[idx]
        state["index"] += 1
        return is_stop, is_correct, answer_time

    monkeypatch.setattr(_main, "ask_and_check", fake_ask_and_check)

    stats = {}

    def fake_print_statistics(score, total_time):
        stats["score"] = score
        stats["total_time"] = total_time

    monkeypatch.setattr(_main, "print_statistics", fake_print_statistics)
    result = _main.train_until_mistake(words)
    output = capsys.readouterr().out.lower()

    assert result is None, (
        "Убедитесь, что функция `train_until_mistake` ничего не возвращает "
    )

    check_msg = "Режим: Игра до первой ошибки! Чтобы выйти вручную, введите СТОП"
    assert check_msg.lower() in output, (
        "Убедитесь, что в начале функции `train_until_mistake` выводится сообщение "
        f"о запуске режима: `{check_msg}`."
    )

    check_msg = 'Ошибка! Неверно. Правильный ответ:'
    assert any(check_msg.lower() in line for line in output.splitlines()), (
        "Убедитесь, что при первом неправильном ответе функция `train_until_mistake` "
        f"выводит сообщение об ошибке: `{check_msg} <здесь правильный ответ>`"
    )

    assert len(calls_log) == 2, (
        "Убедитесь, что в режиме 'до первой ошибки' после первого неверного ответа "
        "игра завершается и больше не задаёт вопросы."
    )

    assert stats, (
        "Убедитесь, что после завершения игры `train_until_mistake` вызывает "
        "функцию `print_statistics`."
    )

    assert stats.get("score") == 1, (
        "Убедитесь, что функция `train_until_mistake` корректно увеличивает счёт "
        "за каждый правильный ответ и передаёт это значение в `print_statistics`."
    )

    assert pytest.approx(stats.get("total_time", -1)) == 3.0, (
        "Убедитесь, что функция `train_until_mistake` суммирует время всех ответов "
        "и передаёт его в `print_statistics`."
    )

    # Выход по СТОП
    state["index"] = 0
    calls_log.clear()
    stats.clear()
    responses = [
        (False, True, 0.5),
        (True, False, 0.0),
    ]

    result = _main.train_until_mistake(words)
    output = capsys.readouterr().out.lower()

    check_msg = 'Выход из режима по запросу пользователя.'
    assert check_msg.lower() in output, (
        "Убедитесь, что при вводе завершающего слова `СТОП` функция "
        f"`train_until_mistake` выводит сообщение: `{check_msg}`."
    )

    assert len(calls_log) == 2, (
        "Убедитесь, что при завершении по слову `СТОП` игра не продолжает задавать вопросы."
    )

    assert stats.get("score") == 1, (
        "Убедитесь, что при завершении по слову `СТОП` счётчик правильных ответов "
        "корректно передаётся в `print_statistics`."
    )

    assert pytest.approx(stats.get("total_time", -1)) == 0.5, (
        "Убедитесь, что при завершении по слову `СТОП` в `print_statistics` "
        "передаётся сумма времени только за реальные ответы пользователя."
    )


@pytest.mark.timeout(2)
def test_add_words(monkeypatch, _main):
    words = {}
    answers_0 = ["   Стоп"]
    state_0 = {"index": 0}

    def fake_input_0(prompt: str) -> str:
        idx = state_0["index"]
        assert idx < len(answers_0), (
            "Убедитесь, что при вводе `СТОП` функция `add_words` завершает работу ."
        )
        value = answers_0[idx]
        state_0["index"] += 1
        return value

    monkeypatch.setattr("builtins.input", fake_input_0)
    result = _main.add_words(words)

    assert result is None, (
        "Убедитесь, что функция `add_words` ничего не возвращает "
    )
    assert words == {}, (
        "Убедитесь, что если сразу вводится завершающее слово `СТОП`, "
        "словарь не изменяется."
    )

    words = {}
    answers_1 = ["cat", "кот", "dog", "собака", "  Стоп",]
    state_1 = {"index": 0}

    def fake_input_1(prompt: str) -> str:
        idx = state_1["index"]
        assert idx < len(answers_1), (
            "Убедитесь, что при вводе `СТОП` функция `add_words` завершает работу ."
        )
        value = answers_1[idx]
        state_1["index"] += 1
        return value

    monkeypatch.setattr("builtins.input", fake_input_1)
    result = _main.add_words(words)

    assert result is None, (
        "Убедитесь, что функция `add_words` ничего не возвращает "
    )
    assert words == {"cat": "кот", "dog": "собака"}, (
        "Убедитесь, что после работы функции `add_words` в словарь добавляются "
        "новые пары `слово: перевод`."
    )

    answers_2 = ["elephant", "   Стоп"]
    state_2 = {"index": 0}

    def fake_input_2(prompt: str) -> str:
        idx = state_2["index"]
        assert idx < len(answers_2), (
            "Убедитесь, что при вводе `СТОП` функция `add_words` завершает работу ."
        )
        value = answers_2[idx]
        state_2["index"] += 1
        return value

    monkeypatch.setattr("builtins.input", fake_input_2)
    result = _main.add_words(words)

    assert "elephant" not in words, (
        "Убедитесь, что если пользователь вводит завершающее слово `СТОП` вместо "
        "перевода, пара не добавляется в словарь."
    )

    answers_3 = ["cat", "кошка", "стоп"]
    state_3 = {"index": 0}

    def fake_input_3(prompt: str) -> str:
        idx = state_3["index"]
        assert idx < len(answers_3), (
            "Убедитесь, что при вводе `СТОП` функция `add_words` завершает работу ."
        )
        value = answers_3[idx]
        state_3["index"] += 1
        return value

    monkeypatch.setattr("builtins.input", fake_input_3)
    old_len = len(words)
    result = _main.add_words(words)

    assert len(words) == old_len, (
        "Убедитесь, что при добавлении слова, которое уже есть в словаре, "
        "функция `add_words` обновляет перевод, а не добавляет дубликат."
    )
    assert words["cat"] == "кошка", (
        "Убедитесь, что при повторном вводе того же слова перевод обновляется в словаре."
    )


def test_show_all_words(capsys, _main):
    words = {"cat": "кот", "dog": "собака", "tree": "дерево"}

    result = _main.show_all_words(words)
    assert result is None, (
        "Убедитесь, что функция `show_all_words` ничего не возвращает."
    )
    out = capsys.readouterr().out.strip()
    assert out == "cat - кот; dog - собака; tree - дерево", (
        "Убедитесь, что функция `show_all_words` выводит все пары в одну строку "
        "в формате `слово - перевод; ...`, как в примере."
    )

    # Пустой словарь
    _main.show_all_words({})
    out_empty = capsys.readouterr().out

    assert out_empty == "" or out_empty.strip() == "", (
        "Убедитесь, что при пустом словаре функция `show_all_words` выводит пустую строку"
    )


def test_save_words(tmp_path, capsys, _main):
    words = {"cat": "кот", "dog": "собака",}

    filename = tmp_path / "out_words.txt"
    result = _main.save_words(words, str(filename))

    assert result is None, (
        "Убедитесь, что функция `add_words` ничего не возвращает "
    )

    assert filename.exists() and filename.is_file(), (
        "Убедитесь, что функция `save_words` создаёт файл по переданному пути."
    )

    content = filename.read_text(encoding="utf-8").strip().splitlines()
    assert len(content) == len(words), (
        "Убедитесь, что в файл записывается ровно столько строк, "
        "сколько пар `слово: перевод` в словаре."
    )

    restored: dict[str, str] = {}
    for line in content:
        assert "," in line, (
            "Убедитесь, что каждая пара `слово — перевод` сохраняется в формате "
            "`слово, перевод` (через запятую)."
        )
        parts = line.split(",")
        assert len(parts) == 2, (
            "Убедитесь, что в каждой строке файла только одна запятая: "
            "`слово,перевод`."
        )
        word = parts[0].strip()
        translation = parts[1].strip()
        restored[word] = translation

    assert restored == words, (
        "Убедитесь, что функция `save_words` корректно сохраняет все пары "
        "`слово,перевод` так, чтобы их можно было восстановить в исходный словарь."
    )

    out = capsys.readouterr().out.strip()
    assert "Было сохранено" in out and str(len(words)) in out and filename.name in out, (
        "Убедитесь, что после сохранения функция `save_words` выводит сообщение в формате: "
        "`Было сохранено <кол-во> слов в файл <имя файла>`."
    )


@pytest.mark.timeout(2)
def test_main_menu(monkeypatch, capsys, _main):
    words_data = {"cat": "кот", "dog": "собака"}
    load_state = {"count": 0}

    def fake_load_words():
        load_state["count"] += 1
        return dict(words_data)

    monkeypatch.setattr(_main, "load_words", fake_load_words)
    calls = {"start": 0, "add": 0, "train": 0, "show": 0, "save": 0}

    def fake_start_game(words):
        calls["start"] += 1
        assert isinstance(words, dict), (
            "Убедитесь, что в функцию `start_game` передаётся словарь слов."
        )

    def fake_add_words(words):
        calls["add"] += 1
        assert isinstance(words, dict), (
            "Убедитесь, что в функцию `add_words` передаётся словарь слов."
        )

    def fake_train_until_mistake(words):
        calls["train"] += 1
        assert isinstance(words, dict), (
            "Убедитесь, что в функцию `train_until_mistake` передаётся словарь слов."
        )

    def fake_show_all_words(words):
        calls["show"] += 1
        assert isinstance(words, dict), (
            "Убедитесь, что в функцию `show_all_words` передаётся словарь слов."
        )

    def fake_save_words(words, filename="words.txt"):
        calls["save"] += 1
        assert isinstance(words, dict), (
            "Убедитесь, что в функцию `save_words` передаётся словарь слов."
        )

    monkeypatch.setattr(_main, "start_game", fake_start_game)
    monkeypatch.setattr(_main, "add_words", fake_add_words)
    monkeypatch.setattr(_main, "train_until_mistake", fake_train_until_mistake)
    monkeypatch.setattr(_main, "show_all_words", fake_show_all_words)
    monkeypatch.setattr(_main, "save_words", fake_save_words)

    menu_inputs = ["1", "2", "3", "4", "9", "5"]
    state = {"index": 0}

    def fake_input(prompt: str) -> str:
        idx = state["index"]
        if idx >= len(menu_inputs):
            pytest.fail(
                "Убедитесь, что после выбора пункта 5 - 'Выход' функция `main` завершает работу"
            )
        value = menu_inputs[idx]
        state["index"] += 1
        return value

    monkeypatch.setattr("builtins.input", fake_input)

    try:
        result = _main.main()
    except SystemExit:
        result = None

    assert result is None, (
        "Убедитесь, что функция `main` ничего не возвращает "
    )

    assert load_state["count"] == 1, (
        "Убедитесь, что при запуске программы функция `load_words` вызывается "
        "ровно один раз для загрузки словаря."
    )

    assert calls["start"] == 1, (
        "Убедитесь, что при выборе пункта 1 - 'Начать игру'"
        "вызывается функция `start_game`."
    )
    assert calls["add"] == 1, (
        "Убедитесь, что при выборе пункта 2 - 'Добавить слова'"
        "вызывается функция `add_words`."
    )
    assert calls["train"] == 1, (
        "Убедитесь, что при выборе пункта 3 - 'Тренировка до первой ошибки' "
        "вызывается функция `train_until_mistake`."
    )
    assert calls["show"] == 1, (
        "Убедитесь, что при выборе пункта 4 - 'Вывод всех слов'"
        "вызывается функция `show_all_words`."
    )
    assert calls["save"] == 1, (
        "Убедитесь, что при выборе пункта 'Выход' перед завершением работы "
        "вызывается функция `save_words`."
    )

    out = capsys.readouterr().out

    assert "Было загружено" in out and "2" in out and "words.txt" in out, (
        "Убедитесь, что после загрузки слов функция `main` выводит сообщение "
        "в формате `Было загружено <кол-во> слов из файла words.txt`."
    )
    assert "Неизвестный пункт меню" in out, (
        "Убедитесь, что при вводе неверного номера пункта меню выводится сообщение "
        "'Неизвестный пункт меню'."
    )
