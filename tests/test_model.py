import pytest

from src import model as m


def setup_function():
    """Очистить модель перед каждым тестом."""
    m.reset()


def test_create_participant():
    """Создание участника возвращает кортеж."""
    p = m.create_participant(1, 1000, "ru_RU", "windows")
    assert p == (1, 1000, "ru_RU", "windows")
    assert m.get_participants() == [
        (1, 1000, "ru_RU", "windows")
    ]


def test_create_participant_duplicate():
    """Повторный identifier вызывает ошибку."""
    m.create_participant(1, 1000, "ru_RU", "windows")
    with pytest.raises(ValueError):
        m.create_participant(1, 1000, "ru_RU", "windows")


def test_get_participant_not_found():
    """Несуществующий identifier — ошибка."""
    with pytest.raises(ValueError):
        m.get_participant(999)


def test_edit_participant():
    """Редактирование меняет поле locale."""
    m.create_participant(1, 1000, "ru_RU", "windows")
    p = m.edit_participant(1, locale="en_US")
    assert p == (1, 1000, "en_US", "windows")


def test_create_assignment_requires_participant():
    """Нельзя создать задание без участника."""
    with pytest.raises(ValueError):
        m.create_assignment(
            10, 1000, "input", 999, "tag", "new"
        )


def test_create_result_requires_assignment():
    """Нельзя создать результат без задания."""
    with pytest.raises(ValueError):
        m.create_result(
            100, 1000, "ok", "done", "", 999, 1
        )


def test_recent_selection_inside_window():
    """Запись в окне 5 минут попадает в выборку."""
    m.create_participant(1, 1000, "ru_RU", "windows")
    m.create_assignment(
        10, 1000, "task_input", 1, "tag1", "new"
    )
    m.create_result(
        100, 1000, "ok", "done", "", 10, 1
    )

    result = m.recent_input_platform_cache_hit(1100)
    assert result == [("task_input", "windows", 1)]


def test_recent_selection_outside_window():
    """Запись старше 5 минут не попадает в выборку."""
    m.create_participant(1, 1000, "ru_RU", "windows")
    m.create_assignment(
        10, 1000, "task_input", 1, "tag1", "new"
    )
    m.create_result(
        100, 1000, "ok", "done", "", 10, 1
    )

    result = m.recent_input_platform_cache_hit(2000)
    assert result == []
