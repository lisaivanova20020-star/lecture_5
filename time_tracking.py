
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Callable, Dict, Optional

from task_system import TaskManager, Priority


@dataclass
class TimeEntry:
    """Один промежуток времени, затраченный на задачу."""

    task_id: int
    user_id: int
    start: datetime
    end: Optional[datetime] = None


class TimeTracker:
    """Класс для учета времени выполнения задач."""

    def __init__(self, clock: Callable = datetime.now):
        self.clock = clock
        self.entries = []
        self.running_timers: Dict[int, TimeEntry] = {}

    def start_timer(
        self,
        task_id: int,
        user_id: int,
        tasks: dict,
        users: dict
    ):
        """Запускает таймер для задачи."""

        if task_id not in tasks:
            raise ValueError("Задача не найдена")

        if user_id not in users:
            raise ValueError("Пользователь не найден")

        if task_id in self.running_timers:
            raise ValueError("Таймер для этой задачи уже запущен")

        entry = TimeEntry(
            task_id=task_id,
            user_id=user_id,
            start=self.clock()
        )

        self.running_timers[task_id] = entry
        self.entries.append(entry)

        return entry

    def stop_timer(self, task_id: int):
        """Останавливает таймер задачи."""

        if task_id not in self.running_timers:
            raise ValueError("Таймер для этой задачи не запущен")

        entry = self.running_timers[task_id]
        entry.end = self.clock()

        del self.running_timers[task_id]

        return entry

    def _duration(self, entry: TimeEntry) -> timedelta:
        """Возвращает продолжительность одного промежутка."""

        end_time = (
            entry.end
            if entry.end is not None
            else self.clock()
        )

        return end_time - entry.start

    def get_task_time(self, task_id: int) -> timedelta:
        """Считает все время, затраченное на задачу."""

        total = timedelta()

        for entry in self.entries:
            if entry.task_id == task_id:
                total += self._duration(entry)

        return total

    def generate_report(self, tasks: dict, users: dict) -> dict:
        """Формирует общий отчет по затраченному времени."""

        total_time = timedelta()
        by_task = {}
        by_user = {}

        for entry in self.entries:
            duration = self._duration(entry)
            total_time += duration

            task = tasks.get(entry.task_id)
            user = users.get(entry.user_id)

            if task is not None:
                task_name = task.title

                by_task[task_name] = (
                    by_task.get(task_name, timedelta()) + duration
                )

            if user is not None:
                user_name = user.name

                by_user[user_name] = (
                    by_user.get(user_name, timedelta()) + duration
                )

        return {
            "total": format_duration(total_time),

            "by_task": {
                name: format_duration(duration)
                for name, duration in by_task.items()
            },

            "by_user": {
                name: format_duration(duration)
                for name, duration in by_user.items()
            }
        }


def format_duration(duration: timedelta) -> str:
    """Преобразует время в формат ЧЧ:ММ:СС."""

    total_seconds = int(duration.total_seconds())

    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


class TimeTrackedTaskManager(TaskManager):
    """Менеджер задач с дополнительным учетом времени."""

    def __init__(self, clock: Callable = datetime.now):
        super().__init__()
        self.tracker = TimeTracker(clock)

    def start_timer(self, task_id: int, user_id: int):
        """Запускает учет времени по задаче."""

        return self.tracker.start_timer(
            task_id,
            user_id,
            self.tasks,
            self.users
        )

    def stop_timer(self, task_id: int):
        """Останавливает учет времени по задаче."""

        return self.tracker.stop_timer(task_id)

    def get_task_time(self, task_id: int) -> timedelta:
        """Возвращает общее время по задаче."""

        return self.tracker.get_task_time(task_id)

    def get_time_report(self) -> dict:
        """Возвращает отчет по затраченному времени."""

        return self.tracker.generate_report(
            self.tasks,
            self.users
        )


# Демонстрация работы программы

if __name__ == "__main__":

    class FakeClock:
        """Имитация системного времени."""

        def __init__(self):
            self.now = datetime(2025, 1, 1, 9, 0, 0)

        def __call__(self):
            return self.now

        def advance(self, **kwargs):
            self.now += timedelta(**kwargs)

    clock = FakeClock()

    manager = TimeTrackedTaskManager(clock)

    user = manager.create_user(
        "Алексей",
        "alexey@company.com"
    )

    task = manager.create_task(
        "REST API",
        "Описание задачи",
        Priority.HIGH,
        clock.now + timedelta(days=7)
    )

    manager.start_timer(
        task.task_id,
        user.user_id
    )

    clock.advance(minutes=45)

    manager.stop_timer(task.task_id)

    print(manager.get_time_report())
