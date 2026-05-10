from datetime import date

from smartsheet.models.sheet import Sheet as SmartSheet

from weekly_report.config import FIELD_ASSIGN, FIELD_END, FIELD_START, FIELD_TASK
from weekly_report.dateutils import parse_date


def fetch_weekly_tasks(
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

        start = parse_date(row.get_column(col_ids[FIELD_START]).value)
        end = parse_date(row.get_column(col_ids[FIELD_END]).value)

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
