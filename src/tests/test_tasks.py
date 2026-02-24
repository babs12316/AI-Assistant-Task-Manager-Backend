import pytest

from src.agent import (
    add_task,
    list_tasks,
    complete_task,
    edit_task,
    delete_task,
    tasks,
)


@pytest.fixture(autouse=True)
def clear_tasks():
    """Clear global tasks before each test"""
    tasks.clear()
    yield
    tasks.clear()


def test_add_task():
    response = add_task.invoke(
        {"title": "Buy milk", "due_date": "2026-02-21"}
    )

    assert len(tasks) == 1
    assert tasks[0].title == "Buy milk"
    assert tasks[0].due_date == "2026-02-21"
    assert "added task Buy milk" in response


def test_list_tasks_all():
    add_task.invoke({"title": "Task 1"})
    add_task.invoke({"title": "Task 2"})

    result = list_tasks.invoke({})

    assert len(result) == 2


def test_list_tasks_by_day():
    add_task.invoke({"title": "Gym", "due_date": "2026-02-21"})
    add_task.invoke({"title": "Call Mom", "due_date": "2026-02-22"})

    result = list_tasks.invoke({"day": "2026-02-21"})

    assert len(result) == 1
    assert result[0].title == "Gym"


def test_complete_task():
    add_task.invoke({"title": "Read Book"})
    task_id = tasks[0].id

    response = complete_task.invoke({"task_id": task_id})

    assert tasks[0].completed is True
    assert any(word in response for word in ["Awesome", "Nice", "Crushed", "Great"])


def test_complete_task_not_found():
    response = complete_task.invoke({"task_id": "invalid"})

    assert "not found" in response.lower()


def test_edit_task():
    add_task.invoke({"title": "Old Title"})
    task_id = tasks[0].id

    response = edit_task.invoke({
        "task_id": task_id,
        "updated_title": "New Title",
        "updated_due_date": "2026-03-01",
    })

    assert tasks[0].title == "New Title"
    assert tasks[0].due_date == "2026-03-01"
    assert task_id in response


def test_delete_task():
    add_task.invoke({"title": "Delete Me"})
    task_id = tasks[0].id

    response = delete_task.invoke({"task_id": task_id})

    assert len(tasks) == 0
    assert "deleted" in response.lower()


def test_delete_task_not_found():
    response = delete_task.invoke({"task_id": "abc123"})

    assert "not found" in response.lower()