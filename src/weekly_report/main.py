import datetime
import zoneinfo

import streamlit as st

from weekly_report import cli, clipboard, config
from weekly_report.smartsheet_agent import SmartsheetAgent, Task

TIMEZONE = "Asia/Taipei"
STYLE_HEADER = "font-size:40pt; margin:0; margin-bottom:8px; text-align:left;"
STYLE_TASK_MAIN = "font-size:28pt; margin:20pt 0 0 0; text-align:left;"
STYLE_TASK_CHILD = "font-size:28pt; margin:6pt 0 0 0; color:gray; text-align:left;"


class App:
    def __init__(self):
        args = cli.parse_args()
        week_offset = self._get_week_offset(args)
        self.monday, self.friday = self._get_week_range(week_offset)

        api_token, sheet_id = config.load_env_config()
        self.smartsheet_agent = SmartsheetAgent(api_token, sheet_id)

        st.header("Smartsheet Weekly Reporter")
        employees = self.smartsheet_agent.fetch_employees()
        self.employee = st.selectbox(
            label="Select employee",
            options=sorted(employees),
            index=None,
            placeholder="Employee name...",
        )

        st.date_input(
            label="Week range",
            value=(self.monday, self.friday),
            format="YYYY.MM.DD",
        )

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

    def get_html(self):
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
        html = self.get_html()
        st.text("HTML content rendering")
        with st.container(border=True):
            st.html(body=html)


def main():
    app = App()
    app.render_html()
    # clipboard.copy_html_to_clipboard(html)
    # print("Copied to clipboard — paste into your slide with Ctrl+V.")


if __name__ == "__main__":
    main()
