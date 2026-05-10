import smartsheet

from weekly_report.cli import parse_args
from weekly_report.clipboard import copy_html_to_clipboard
from weekly_report.config import load_env_config
from weekly_report.dateutils import get_week_range
from weekly_report.fetcher import fetch_weekly_tasks
from weekly_report.organizer import organize_family_tasks
from weekly_report.renderer import derive_html_content


def main():
    args = parse_args()

    offset = -1 if args.last_week else 0
    week_label = "last week" if args.last_week else "this week"

    api_token, sheet_id, employee = load_env_config()

    client = smartsheet.Smartsheet(api_token)
    sheet = client.Sheets.get_sheet(sheet_id)

    col_ids: dict[str, int] = {col.title: col.id for col in sheet.columns}

    monday, friday = get_week_range(offset)

    tasks = fetch_weekly_tasks(sheet, col_ids, employee, monday, friday)

    if not tasks:
        print(f"No tasks found for {week_label}.")
        return

    tasks_org = organize_family_tasks(tasks)
    html = derive_html_content(monday, friday, tasks_org)
    copy_html_to_clipboard(html)

    print(
        f"Copied {week_label} "
        f"({monday.strftime('%b %#d')} - {friday.strftime('%b %#d, %Y')}) "
        f"to clipboard — paste into your slide with Ctrl+V."
    )


if __name__ == "__main__":
    main()
