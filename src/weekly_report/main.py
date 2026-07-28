import datetime
import zoneinfo

import streamlit as st

from weekly_report import clipboard, config
from weekly_report.smartsheet_agent import SmartsheetAgent, Task

TIMEZONE = "Asia/Taipei"
STYLE_HEADER = "font-size:18pt; margin:0; text-align:left;"
STYLE_TASK_MAIN = "font-size:12pt; margin:0; text-align:left;"
STYLE_TASK_CHILD = "font-size:12pt; margin:0; color:gray; text-align:left;"


class App:
    def __init__(self):
        self.smartsheet_agent = SmartsheetAgent(*config.load_env_config())
        employees = self.smartsheet_agent.fetch_employees()

        st.header("Smartsheet Weekly Reporter")
        self.employee = st.selectbox(
            label="Select employee",
            options=sorted(employees),
            index=None,
            placeholder="Employee name...",
        )

        self.monday, self.friday = st.date_input(
            label="Assign date range",
            value=self._get_week_range(),
            format="YYYY.MM.DD",
        )

    @staticmethod
    def _get_week_range(week_offset: int = 0) -> tuple[datetime.date, datetime.date]:
        tz = zoneinfo.ZoneInfo(TIMEZONE)
        today = datetime.datetime.now(tz).date()
        this_monday = today - datetime.timedelta(days=today.weekday())

        monday = this_monday + datetime.timedelta(weeks=week_offset)
        friday = monday + datetime.timedelta(days=4)
        return monday, friday

    def _fmt_children(self, children: list[Task]) -> str:
        if not children:
            return ""

        items = "".join(
            "<li>" + child.task_name + self._fmt_children(child.children) + "</li>"
            for child in children
        )

        return f"<ul style='{STYLE_TASK_CHILD}'>" + items + "</ul>"

    def _derive_html_header(self) -> str:
        monday_fmt = self.monday.strftime("%b ") + str(self.monday.day)
        friday_fmt = (
            self.friday.strftime("%b ")
            + str(self.friday.day)
            + self.friday.strftime(", %Y")
        )
        header_str = f"{monday_fmt} - {friday_fmt}"
        return f"<p style='{STYLE_HEADER}'><b>{header_str}</b></p>"

    def _derive_html_items(self, tasks: dict[int, Task]) -> str:
        items_html = ""
        for task in tasks.values():
            task_html = f"<p style='{STYLE_TASK_MAIN}'>{task.task_name}</p>"
            childs_html = "<ul>" + self._fmt_children(task.children) + "</ul>"
            items_html += task_html + childs_html
        return items_html

    def _get_html(self):
        html_header = self._derive_html_header()

        if not self.employee:
            return html_header

        tasks = self.smartsheet_agent.fetch_tasks(
            employee=self.employee,
            monday=self.monday,
            friday=self.friday,
        )

        return html_header + self._derive_html_items(tasks)

    def render_html(self):
        st.text("Queried tasks")
        with st.container(border=True):
            st.html(body=self._get_html())


def main():
    app = App()
    app.render_html()
    # clipboard.copy_html_to_clipboard(html)
    # print("Copied to clipboard — paste into your slide with Ctrl+V.")


if __name__ == "__main__":
    main()
