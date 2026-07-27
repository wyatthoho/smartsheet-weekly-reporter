import copy
import datetime
import zoneinfo
from dataclasses import dataclass, field

import smartsheet

from weekly_report import cli, clipboard, config

TIMEZONE = "Asia/Taipei"
FIELDS = ["Task", "Assigned To", "Start Date", "End Date"]
STYLE_HEADER = "font-size:40pt; margin:0; margin-bottom:8px; text-align:left;"
STYLE_TASK_MAIN = "font-size:28pt; margin:20pt 0 0 0; text-align:left;"
STYLE_TASK_CHILD = "font-size:28pt; margin:6pt 0 0 0; color:gray; text-align:left;"


@dataclass
class Task:
    parent_id: int | None
    task_name: str
    assign: str
    children: list["Task"] = field(default_factory=list)


class App:
    def __init__(self):
        args = cli.parse_args()
        week_offset = self._get_week_offset(args)
        self.monday, self.friday = self._get_week_range(week_offset)

        api_token, sheet_id, self.employee = config.load_env_config()
        client = smartsheet.Smartsheet(api_token)

        self.column_ids = self._get_column_ids(client, sheet_id)
        self.sheet = client.Sheets.get_sheet(sheet_id, column_ids=self.column_ids)

    @staticmethod
    def _get_column_ids(client: smartsheet.Smartsheet, sheet_id: str) -> list[int]:
        # Limit to specific columns (instead of fetching all columns/rows) to avoid
        # a 500/errorCode 4000 "unexpected error" from the Smartsheet API, likely
        # caused by the full sheet response being too large or containing an
        # unsupported column type.
        columns = client.Sheets.get_columns(sheet_id).data
        _map = {col.title: col.id for col in columns if col.title in FIELDS}
        return [_map[field] for field in FIELDS]

    @staticmethod
    def _get_week_offset(args) -> int:
        if args.last_week:
            return -1
        elif args.next_week:
            return 1
        return 0

    @staticmethod
    def _get_week_range(week_offset: int) -> tuple[datetime.date, datetime.date]:
        tz = zoneinfo.ZoneInfo(TIMEZONE)
        today = datetime.datetime.now(tz).date()
        this_monday = today - datetime.timedelta(days=today.weekday())

        monday = this_monday + datetime.timedelta(weeks=week_offset)
        friday = monday + datetime.timedelta(days=4)
        return monday, friday

    @staticmethod
    def _parse_date(value: str | None) -> datetime.date | None:
        if not value:
            return None
        try:
            return datetime.datetime.fromisoformat(value).date()
        except ValueError:
            return None

    def _fetch_weekly_tasks(
        self, column_task: int, column_assign: int, column_start: int, column_end: int
    ) -> dict[int, Task]:
        tasks: dict[int, Task] = {}
        for row in self.sheet.rows:
            start = self._parse_date(row.get_column(column_start).value)
            end = self._parse_date(row.get_column(column_end).value)

            if not start or not end:
                continue

            if start > self.friday or end < self.monday:
                continue

            tasks[row.id_] = Task(
                parent_id=row.parent_id,
                task_name=row.get_column(column_task).value,
                assign=row.get_column(column_assign).value,
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

    def _fmt_children(self, children: list[Task]) -> str:
        if not children:
            return ""

        items = "".join(
            "<li>" + child.task_name + self._fmt_children(child.children) + "</li>"
            for child in children
        )

        return f"<ul style='{STYLE_TASK_CHILD}'>" + items + "</ul>"

    def _derive_html_content(self, tasks: dict[int, Task]) -> str:
        monday_fmt = self.monday.strftime("%b ") + str(self.monday.day)
        friday_fmt = (
            self.friday.strftime("%b ")
            + str(self.friday.day)
            + self.friday.strftime(", %Y")
        )
        header_str = f"{monday_fmt} - {friday_fmt}"

        header_html = f"<p style='{STYLE_HEADER}'><b>{header_str}</b></p>"

        items_html = ""
        for task in tasks.values():
            task_html = f"<p style='{STYLE_TASK_MAIN}'>{task.task_name}</p>"
            childs_html = "<ul>" + self._fmt_children(task.children) + "</ul>"
            items_html += task_html + childs_html

        return header_html + items_html

    def run(self):
        tasks_weekly = self._fetch_weekly_tasks(*self.column_ids)
        tasks_employee = self._fetch_employee_tasks(tasks_weekly, self.employee)
        if not tasks_employee:
            print("No tasks found.")
            return

        tasks = self._bubble_up(tasks_weekly, tasks_employee)
        html = self._derive_html_content(tasks)
        clipboard.copy_html_to_clipboard(html)
        print("Copied to clipboard — paste into your slide with Ctrl+V.")


def main():
    App().run()


if __name__ == "__main__":
    main()
