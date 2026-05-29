import copy
from datetime import date, datetime, timedelta

import smartsheet

from weekly_report import cli
from weekly_report import clipboard
from weekly_report import config


FIELD_ASSIGN = "Assigned To"
FIELD_START = "Start Date"
FIELD_END = "End Date"
FIELD_TASK = "Task"

STYLE_HEADER = "font-size:40pt; margin:0; margin-bottom:24px; text-align:left;"
STYLE_TASK_MAIN = "font-size:28pt; margin:20pt 0 0 0; text-align:left;"
STYLE_TASK_CHILD = "font-size:28pt; color:gray; text-align:left;"


class App:
    def __init__(self):
        args = cli.parse_args()

        if args.last_week:
            self.week_offset = -1
        elif args.next_week:
            self.week_offset = 1
        else:
            self.week_offset = 0

        api_token, sheet_id, self.employee = config.load_env_config()

        client = smartsheet.Smartsheet(api_token)
        self.sheet = client.Sheets.get_sheet(sheet_id)

        self.col_ids = self.get_col_ids()
        self.monday, self.friday = self.get_week_range()

    def run(self):
        tasks_weekly = self._fetch_weekly_tasks()
        tasks_employee = self._fetch_employee_tasks(tasks_weekly)
        if not tasks_employee:
            print("No tasks found.")
            return

        tasks_child = self._attach_child_to_parent(tasks_weekly, tasks_employee)
        self._recurse(tasks_child)
        html = self.derive_html_content(tasks_child)
        clipboard.copy_html_to_clipboard(html)
        print("Copied to clipboard — paste into your slide with Ctrl+V.")

    def get_col_ids(self) -> dict[str, int]:
        return {col.title: col.id for col in self.sheet.columns}

    def get_week_range(self) -> tuple[date, date]:
        today = date.today()
        monday = (
            today - timedelta(days=today.weekday()) + timedelta(weeks=self.week_offset)
        )
        friday = monday + timedelta(days=4)
        return monday, friday

    def _parse_date(self, value: str | None) -> date | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value).date()
        except ValueError:
            return None

    def _fetch_weekly_tasks(self) -> dict[int, dict]:
        tasks: dict[int, dict] = {}
        for row in self.sheet.rows:
            start = self._parse_date(row.get_column(self.col_ids[FIELD_START]).value)
            end = self._parse_date(row.get_column(self.col_ids[FIELD_END]).value)

            if not start or not end:
                continue

            if start > self.friday or end < self.monday:
                continue

            tasks[row.id_] = {
                "parent_id": row.parent_id,
                "task_name": row.get_column(self.col_ids[FIELD_TASK]).value,
                "assign": row.get_column(self.col_ids[FIELD_ASSIGN]).value,
                "children": [],
            }
        return tasks

    def _fetch_employee_tasks(self, tasks: dict[int, dict]) -> dict[int, dict]:
        return {
            row_id: task
            for row_id, task in tasks.items()
            if task["assign"] == self.employee
        }

    def _attach_child_to_parent(
        self, tasks_week: dict[int, dict], tasks_employee: dict[int, dict]
    ) -> dict[int, dict]:
        tasks_week_copy = copy.deepcopy(tasks_week)

        top_parent_ids = set()
        for row_id, task in tasks_employee.items():
            parent_id = task["parent_id"]

            if parent_id:
                parent = tasks_week_copy[parent_id]
                parent["children"].append(tasks_week_copy[row_id])

                if not parent["parent_id"]:
                    top_parent_ids.add(parent_id)
        return tasks_week_copy

    def _recurse(self, tasks_child: dict[int, dict]):
        visited: set[int] = set()

        def bubble_up(row_id: int):
            task = tasks_child[row_id]
            parent_id = task["parent_id"]

            visited.add(row_id)

            if not parent_id or parent_id not in tasks_child:
                return

            parent = tasks_child[parent_id]
            if task not in parent["children"]:
                parent["children"].append(task)

            visited.add(parent_id)
            bubble_up(parent_id)

        for row_id, task in tasks_child.items():
            if task["children"]:
                bubble_up(row_id)

        for row_id in list(tasks_child.keys()):
            task = tasks_child[row_id]
            if row_id not in visited or task["parent_id"] in tasks_child:
                del tasks_child[row_id]

    def _fmt_childs(self, children: list) -> str:
        if not children:
            return ""

        items = "".join(
            "<li>"
            + child["task_name"]
            + self._fmt_childs(child.get("children", []))
            + "</li>"
            for child in children
        )

        return f"<ul style='{STYLE_TASK_CHILD}'>" + items + "</ul>"

    def derive_html_content(self, tasks: dict[int, dict]) -> str:
        monday_fmt = self.monday.strftime("%b %#d")
        friday_fmt = self.friday.strftime("%b %#d, %Y")
        header_str = f"{monday_fmt} - {friday_fmt}"

        header_html = f"<p style='{STYLE_HEADER}'>" + f"<b>{header_str}</b>" + "</p>"

        items_html = ""
        for task in tasks.values():
            task_html = f"<p style='{STYLE_TASK_MAIN}'>" + task["task_name"] + "</p>"
            childs_html = "<ul>" + self._fmt_childs(task.get("children", [])) + "</ul>"
            items_html += task_html + childs_html

        return header_html + items_html


def main():
    App().run()


if __name__ == "__main__":
    main()
