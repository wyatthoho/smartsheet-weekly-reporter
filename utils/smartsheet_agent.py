import copy
import datetime
from dataclasses import dataclass, field

import smartsheet

COLUMN_TASK = "Task"
COLUMN_ASSIGN = "Assigned To"
COLUMN_START = "Start Date"
COLUMN_END = "End Date"


@dataclass
class Task:
    parent_id: int | None
    task_name: str
    assign: str
    children: list["Task"] = field(default_factory=list)


class SmartsheetAgent:
    def __init__(self, api_token: str, sheet_id: str):
        self.client = smartsheet.Smartsheet(api_token)
        self.sheet_id = sheet_id

        self.columns_map = self._get_columns_map()
        self.sheet = self.client.Sheets.get_sheet(
            sheet_id=sheet_id,
            column_ids=list(self.columns_map.values()),
        )

    def _get_columns_map(self) -> dict[str, int]:
        # Limit to specific columns (instead of fetching all columns/rows) to avoid
        # a 500/errorCode 4000 "unexpected error" from the Smartsheet API, likely
        # caused by the full sheet response being too large or containing an
        # unsupported column type.
        titles = [COLUMN_TASK, COLUMN_ASSIGN, COLUMN_START, COLUMN_END]
        columns = self.client.Sheets.get_columns(self.sheet_id).data
        return {col.title: col.id for col in columns if col.title in titles}

    @staticmethod
    def _parse_date(value: str | None) -> datetime.date | None:
        if not value:
            return None
        try:
            return datetime.datetime.fromisoformat(value).date()
        except ValueError:
            return None

    def _fetch_weekly_tasks(
        self, monday: datetime.date, friday: datetime.date
    ) -> dict[int, Task]:
        tasks: dict[int, Task] = {}
        column_start = self.columns_map[COLUMN_START]
        column_end = self.columns_map[COLUMN_END]
        column_task = self.columns_map[COLUMN_TASK]
        column_assign = self.columns_map[COLUMN_ASSIGN]

        for row in self.sheet.rows:
            start = self._parse_date(row.get_column(column_start).value)
            end = self._parse_date(row.get_column(column_end).value)

            if not start or not end:
                continue

            if start > friday or end < monday:
                continue

            tasks[row.id_] = Task(
                parent_id=row.parent_id,
                task_name=row.get_column(column_task).value,
                assign=row.get_column(column_assign).display_value,
            )
        return tasks

    @staticmethod
    def _fetch_employee_tasks(tasks: dict[int, Task], employee: str) -> dict[int, Task]:
        return {
            row_id: task for row_id, task in tasks.items() if task.assign == employee
        }

    def _climb(self, row_id: int, tasks: dict[int, Task], visited: set[int]):
        task = tasks[row_id]
        parent_id = task.parent_id

        visited.add(row_id)

        if not parent_id or parent_id not in tasks:
            return

        parent = tasks[parent_id]
        if task not in parent.children:
            parent.children.append(task)

        visited.add(parent_id)
        self._climb(parent_id, tasks, visited)

    def _bubble_up(
        self, tasks_weekly: dict[int, Task], tasks_employee: dict[int, Task]
    ) -> dict[int, Task]:
        tasks = copy.deepcopy(tasks_weekly)
        visited: set[int] = set()

        for row_id in tasks_employee:
            self._climb(row_id, tasks, visited)

        return {
            row_id: task
            for row_id, task in tasks.items()
            if row_id in visited and not task.parent_id
        }

    def fetch_tasks(self, employee: str, monday: datetime.date, friday: datetime.date):
        tasks_weekly = self._fetch_weekly_tasks(monday, friday)
        tasks_employee = self._fetch_employee_tasks(tasks_weekly, employee)

        if not tasks_employee:
            print("No tasks found.")
            return

        return self._bubble_up(tasks_weekly, tasks_employee)

    def fetch_employees(self):
        column_assign = self.columns_map[COLUMN_ASSIGN]

        employees = set()
        for row in self.sheet.rows:
            _name = row.get_column(column_assign).display_value
            if _name and (_name not in employees):
                employees.add(_name)

        return employees