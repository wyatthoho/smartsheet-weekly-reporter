import sys
import copy
import win32clipboard
from datetime import date, datetime, timedelta
from dotenv import load_dotenv, find_dotenv

import smartsheet
from smartsheet.models.sheet import Sheet as SmartSheet
from weekly_report.utils import get_env_variable


ENV_API_TOKEN = "API_TOKEN"
ENV_SHEET_ID = "SHEET_ID"
ENV_EMPLOYEE = "EMPLOYEE"
FIELD_ASSIGN = "Assigned To"
FIELD_START = "Start Date"
FIELD_END = "End Date"
FIELD_TASK = "Task"


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


def _load_env_config() -> tuple[str, str, str]:
    try:
        load_dotenv(find_dotenv())
        api_token = get_env_variable(ENV_API_TOKEN)
        sheet_id = get_env_variable(ENV_SHEET_ID)
        employee = get_env_variable(ENV_EMPLOYEE)
    except ValueError:
        sys.exit(1)
    return api_token, sheet_id, employee


# ---------------------------------------------------------------------------
# Date helpers
# ---------------------------------------------------------------------------


def _get_week_range(offset: int = 0) -> tuple[date, date]:
    today = date.today()
    monday = today - timedelta(days=today.weekday()) + timedelta(weeks=offset)
    friday = monday + timedelta(days=4)
    return monday, friday


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Smartsheet fetching
# ---------------------------------------------------------------------------


def _fetch_weekly_tasks(
    sheet: SmartSheet,
    col_ids: dict[str, int],
    employee: str,
    monday: date,
    friday: date,
) -> dict[int, dict]:
    tasks: dict[int, dict] = {}
    for row in sheet.rows:
        assigned = row.get_column(col_ids[FIELD_ASSIGN]).value

        if assigned != employee:
            continue

        start = _parse_date(row.get_column(col_ids[FIELD_START]).value)
        end = _parse_date(row.get_column(col_ids[FIELD_END]).value)

        if not start and not end:
            continue

        if start > friday or end < monday:
            continue

        task_name = row.get_column(col_ids[FIELD_TASK]).value

        tasks[row.id_] = {
            "parent_id": row.parent_id,
            "task_name": task_name,
            "children": [],
        }
    return tasks


# ---------------------------------------------------------------------------
# Task organisation
# ---------------------------------------------------------------------------


def _organize_family_tasks(tasks: dict[int, dict]) -> dict[int, dict]:
    tasks_copy = copy.deepcopy(tasks)

    all_row_ids = set(tasks_copy.keys())
    child_ids = set()

    for row_id, task in tasks_copy.items():
        parent_id = task["parent_id"]

        if parent_id and parent_id in all_row_ids:
            tasks_copy[parent_id]["children"].append(task)
            child_ids.add(row_id)

    return {
        row_id: task for row_id, task in tasks_copy.items() if row_id not in child_ids
    }


# ---------------------------------------------------------------------------
# HTML content derivation
# ---------------------------------------------------------------------------


def _derive_html_content(monday: date, friday: date, tasks_org: dict[int, dict]) -> str:
    def format_children(children: list, depth: int = 0) -> str:
        """Render second-layer and deeper as a bullet list in gray."""
        if not children:
            return ""
        items = "".join(
            "<li>"
            + c["task_name"]
            + format_children(c.get("children", []), depth + 1)
            + "</li>"
            for c in children
        )
        return (
            "<ul style='text-align:left; font-size:28pt; color:gray;'>"
            + items
            + "</ul>"
        )

    week_str = f"Week of {monday.strftime('%b %#d')} - {friday.strftime('%b %#d, %Y')}"
    header = (
        "<p style='font-size:48pt; margin:0;margin-bottom:24px; text-align:left;'>"
        + f"<b>{week_str}</b>"
        + "</p>"
    )

    # First layer: no bullet, no indent — plain block elements
    first_layer_items = "".join(
        "<p style='font-size:28pt; margin:20pt 0 0 0; text-align:left;'>"
        + task["task_name"]
        + "<ul>"
        + format_children(task.get("children", []))
        + "</ul>"
        + "</p>"
        for task in tasks_org.values()
    )

    return header + first_layer_items


# ---------------------------------------------------------------------------
# Clipboard
# ---------------------------------------------------------------------------


def _copy_html_to_clipboard(html: str) -> None:
    CF_HTML = win32clipboard.RegisterClipboardFormat("HTML Format")

    html_body = f"<html><body>{html}</body></html>"
    header_template = (
        "Version:0.9\r\n"
        "StartHTML:{start_html:08d}\r\n"
        "EndHTML:{end_html:08d}\r\n"
        "StartFragment:{start_frag:08d}\r\n"
        "EndFragment:{end_frag:08d}\r\n"
    )

    dummy_header = header_template.format(
        start_html=0, end_html=0, start_frag=0, end_frag=0
    )
    start_html = len(dummy_header)
    start_frag = start_html + html_body.index("<html>")
    end_frag = start_html + html_body.index("</body>") + len("</body>")
    end_html = start_html + len(html_body)

    header = header_template.format(
        start_html=start_html,
        end_html=end_html,
        start_frag=start_frag,
        end_frag=end_frag,
    )
    data = (header + html_body).encode("utf-8")

    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(CF_HTML, data)
    win32clipboard.CloseClipboard()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Generate weekly report to clipboard.")
    parser.add_argument(
        "--last-week",
        action="store_true",
        help="Generate report for last week instead of this week.",
    )
    args = parser.parse_args()

    offset = -1 if args.last_week else 0
    week_label = "last week" if args.last_week else "this week"

    api_token, sheet_id, employee = _load_env_config()

    client = smartsheet.Smartsheet(api_token)
    sheet = client.Sheets.get_sheet(sheet_id)

    col_ids: dict[str, int] = {col.title: col.id for col in sheet.columns}

    monday, friday = _get_week_range(offset)

    tasks = _fetch_weekly_tasks(sheet, col_ids, employee, monday, friday)

    if not tasks:
        print(f"No tasks found for {week_label}.")
        return

    tasks_org = _organize_family_tasks(tasks)
    html = _derive_html_content(monday, friday, tasks_org)
    _copy_html_to_clipboard(html)

    print(
        f"Copied {week_label} "
        f"({monday.strftime('%b %#d')} - {friday.strftime('%b %#d, %Y')}) "
        f"to clipboard — paste into your slide with Ctrl+V."
    )


if __name__ == "__main__":
    main()
