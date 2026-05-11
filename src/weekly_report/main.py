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
        self.next_week = 1 if args.next_week else 0

        api_token, sheet_id, self.employee = config.load_env_config()

        client = smartsheet.Smartsheet(api_token)
        self.sheet = client.Sheets.get_sheet(sheet_id)

        self.col_ids = self.get_col_ids()
        self.monday, self.friday = self.get_week_range()

    def run(self):
        self.tasks = self.fetch_employee_weekly_tasks()
        if not self.tasks:
            return
        html = self.derive_html_content()
        clipboard.copy_html_to_clipboard(html)
        print("Copied to clipboard — paste into your slide with Ctrl+V.")

    def get_col_ids(self) -> dict[str, int]:
        return {col.title: col.id for col in self.sheet.columns}

    def get_week_range(self) -> tuple[date, date]:
        today = date.today()
        monday = (
            today - timedelta(days=today.weekday()) + timedelta(weeks=self.next_week)
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

    def _fetch_raw_employee_weekly_tasks(self) -> dict[int, dict]:
        tasks: dict[int, dict] = {}
        for row in self.sheet.rows:
            assigned = row.get_column(self.col_ids[FIELD_ASSIGN]).value

            if assigned != self.employee:
                continue

            start = self._parse_date(row.get_column(self.col_ids[FIELD_START]).value)
            end = self._parse_date(row.get_column(self.col_ids[FIELD_END]).value)

            if not start and not end:
                continue

            if start > self.friday or end < self.monday:
                continue

            task_name = row.get_column(self.col_ids[FIELD_TASK]).value

            tasks[row.id_] = {
                "parent_id": row.parent_id,
                "task_name": task_name,
                "children": [],
            }
        return tasks

    def _organize_raw_tasks(self, tasks: dict[int, dict]) -> dict[int, dict]:
        tasks_copy = copy.deepcopy(tasks)

        all_row_ids = set(tasks_copy.keys())
        child_ids = set()

        for row_id, task in tasks_copy.items():
            parent_id = task["parent_id"]

            if parent_id and parent_id in all_row_ids:
                tasks_copy[parent_id]["children"].append(task)
                child_ids.add(row_id)

        return {
            row_id: task
            for row_id, task in tasks_copy.items()
            if row_id not in child_ids
        }

    def fetch_employee_weekly_tasks(self) -> dict[int, dict]:
        tasks_raw = self._fetch_raw_employee_weekly_tasks()

        if not tasks_raw:
            print("No tasks found.")
            return {}

        return self._organize_raw_tasks(tasks_raw)

    def _format_children(self, children: list) -> str:
        if not children:
            return ""

        items = "".join(
            "<li>"
            + child["task_name"]
            + self._format_children(child.get("children", []))
            + "</li>"
            for child in children
        )

        return f"<ul style='{STYLE_TASK_CHILD}'>" + items + "</ul>"

    def derive_html_content(self) -> str:
        monday_fmt = self.monday.strftime("%b %#d")
        friday_fmt = self.friday.strftime("%b %#d, %Y")
        header_str = f"{monday_fmt} - {friday_fmt}"

        header_html = f"<p style='{STYLE_HEADER}'>" + f"<b>{header_str}</b>" + "</p>"

        items_html = ""
        for task in self.tasks.values():
            task_html = f"<p style='{STYLE_TASK_MAIN}'>" + task["task_name"] + "</p>"
            children_html = (
                "<ul>" + self._format_children(task.get("children", [])) + "</ul>"
            )
            items_html += task_html + children_html

        return header_html + items_html


def main():
    App().run()


if __name__ == "__main__":
    main()
