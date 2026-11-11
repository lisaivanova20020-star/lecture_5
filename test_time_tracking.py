
# test_time_tracking.py
"""Тесты модуля учета времени.
Запуск: python3 -m unittest -v
"""

import unittest
from datetime import datetime, timedelta

from task_system import Priority
from time_tracking import TimeTrackedTaskManager, format_duration


class FakeClock:
    """Имитация времени для тестирования."""

    def __init__(self):
        self.now = datetime(2025, 1, 1, 9, 0, 0)

    def __call__(self):
        return self.now

    def advance(self, **kwargs):
        self.now += timedelta(**kwargs)


class TestTimeTracking(unittest.TestCase):

    @classmethod
    def tearDownClass(cls):
        """Выводит демонстрационный отчет после всех тестов."""

        super().tearDownClass()

        print("\n")
        print("=" * 50)
        print("ДЕМОНСТРАЦИЯ РАБОТЫ УЧЕТА ВРЕМЕНИ")
        print("=" * 50)

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

        # Запускаем таймер
        manager.start_timer(task.task_id, user.user_id)

        # Имитируем 45 минут работы
        clock.advance(minutes=45)

        # Останавливаем таймер
        manager.stop_timer(task.task_id)

        # Выводим отчет
        print("\nИтоговый отчет:")
        print(manager.get_time_report())

        print("=" * 50)

    def setUp(self):
        """Создает тестовые данные перед каждым тестом."""

        self.clock = FakeClock()
        self.manager = TimeTrackedTaskManager(self.clock)

        self.user = self.manager.create_user(
            "Иван",
            "ivan@test.com"
        )

        self.user2 = self.manager.create_user(
            "Мария",
            "maria@test.com"
        )

        due = self.clock.now + timedelta(days=5)

        self.task = self.manager.create_task(
            "Задача 1",
            "d",
            Priority.HIGH,
            due
        )

        self.task2 = self.manager.create_task(
            "Задача 2",
            "d",
            Priority.LOW,
            due
        )

    # --- 1. Запуск и остановка таймера ---

    def test_start_and_stop(self):
        entry = self.manager.start_timer(
            self.task.task_id,
            self.user.user_id
        )

        self.assertIsNone(entry.end)

        self.clock.advance(minutes=30)

        entry = self.manager.stop_timer(self.task.task_id)

        self.assertEqual(
            entry.end - entry.start,
            timedelta(minutes=30)
        )

    def test_double_start_raises(self):
        self.manager.start_timer(
            self.task.task_id,
            self.user.user_id
        )

        with self.assertRaises(ValueError):
            self.manager.start_timer(
                self.task.task_id,
                self.user.user_id
            )

    def test_stop_without_start_raises(self):
        with self.assertRaises(ValueError):
            self.manager.stop_timer(self.task.task_id)

    def test_unknown_task_or_user_raises(self):
        with self.assertRaises(ValueError):
            self.manager.start_timer(
                999,
                self.user.user_id
            )

        with self.assertRaises(ValueError):
            self.manager.start_timer(
                self.task.task_id,
                999
            )

    # --- 2. Подсчет общего времени ---

    def test_total_time_sums_intervals(self):
        for minutes in (10, 20):
            self.manager.start_timer(
                self.task.task_id,
                self.user.user_id
            )

            self.clock.advance(minutes=minutes)

            self.manager.stop_timer(self.task.task_id)

            # Перерыв не учитывается
            self.clock.advance(minutes=5)

        self.assertEqual(
            self.manager.tracker.get_task_time(self.task.task_id),
            timedelta(minutes=30)
        )

    def test_total_time_counts_running_timer(self):
        self.manager.start_timer(
            self.task.task_id,
            self.user.user_id
        )

        self.clock.advance(minutes=7)

        self.assertEqual(
            self.manager.tracker.get_task_time(self.task.task_id),
            timedelta(minutes=7)
        )

    def test_no_entries_is_zero(self):
        self.assertEqual(
            self.manager.tracker.get_task_time(self.task.task_id),
            timedelta()
        )

    # --- 3. Формирование отчетов ---

    def test_report(self):
        self.manager.start_timer(
            self.task.task_id,
            self.user.user_id
        )

        self.clock.advance(hours=2)

        self.manager.stop_timer(self.task.task_id)

        self.manager.start_timer(
            self.task2.task_id,
            self.user2.user_id
        )

        self.clock.advance(minutes=30)

        self.manager.stop_timer(self.task2.task_id)

        report = self.manager.get_time_report()

        self.assertEqual(
            report["total"],
            "02:30:00"
        )

        self.assertEqual(
            report["by_task"],
            {
                "Задача 1": "02:00:00",
                "Задача 2": "00:30:00"
            }
        )

        self.assertEqual(
            report["by_user"],
            {
                "Иван": "02:00:00",
                "Мария": "00:30:00"
            }
        )

    def test_empty_report(self):
        self.assertEqual(
            self.manager.get_time_report(),
            {
                "total": "00:00:00",
                "by_task": {},
                "by_user": {}
            }
        )

    def test_format_duration(self):
        self.assertEqual(
            format_duration(
                timedelta(hours=26, minutes=3, seconds=9)
            ),
            "26:03:09"
        )

    # --- 4. Проверка совместимости ---

    def test_old_task_manager_features_still_work(self):
        self.manager.assign_task(
            self.task.task_id,
            self.user.user_id
        )

        self.assertEqual(
            self.manager.get_user_tasks(self.user.user_id),
            [self.task]
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
