"""
main.py
Fetch tasks from Smartsheet for the specified week and group them by parent task.

Filtering criteria:
  - Assigned To == MY_NAME
  - End Date >= Monday of the target week
  - Start Date <= Friday of the target week
  - Only leaf rows (no children) are included as action items
  - Each leaf is grouped under its direct parent task name
"""

import smartsheet
from datetime import date, timedelta
from collections import defaultdict

# ── Configuration ─────────────────────────────────────
API_TOKEN = "your_smartsheet_api_token"
SHEET_ID = 123456789  # Your Sheet ID (integer), found in File > Properties
MY_NAME = "Wyatt Ho"  # Value in the "Assigned To" column
# ─────────────────────────────────────────────────────


def get_week_range(offset: int = 0) -> tuple[date, date]:
    """Return the Monday and Friday of the target week.

    Args:
        offset: 0 = current week, -1 = last week, 1 = next week, etc.
    """
    today = date.today()
    monday = today - timedelta(days=today.weekday()) + timedelta(weeks=offset)
    friday = monday + timedelta(days=4)
    return monday, friday


def parse_date(value: str | None) -> date | None:
    """Parse a date string returned by the Smartsheet API (ISO format: YYYY-MM-DD)."""
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def fetch_tasks(offset: int = 0) -> dict[str, list[str]]:
    """Fetch and group tasks from Smartsheet for the target week.

    Returns:
        A dict mapping parent task name -> list of leaf task names.
        Example: {"TotalEnergies Compatibility Testing": ["Tensile test", "Measure weight"]}
    """
    monday, friday = get_week_range(offset)
    print(f"Fetching tasks for: {monday} ~ {friday}")

    client = smartsheet.Smartsheet(API_TOKEN)
    sheet = client.Sheets.get_sheet(SHEET_ID)

    # Build column title -> column_id lookup
    col_map = {col.title: col.id for col in sheet.columns}

    def get_col_id(name: str) -> int:
        col_id = col_map.get(name)
        if col_id is None:
            raise KeyError(
                f"Column '{name}' not found. Available columns: {list(col_map.keys())}"
            )
        return col_id

    col_assigned = get_col_id("Assigned To")
    col_start = get_col_id("Start Date")
    col_end = get_col_id("End Date")
    col_task = get_col_id("Task Name")

    # Build row_id -> row data map, preserving parent_id for hierarchy traversal
    row_map: dict[int, dict] = {}
    for row in sheet.rows:
        cells = {cell.column_id: cell.display_value for cell in row.cells}
        row_map[row.id] = {
            "id": row.id,
            "parent_id": row.parent_id,
            "task": cells.get(col_task, "") or "",
            "assigned": cells.get(col_assigned, "") or "",
            "start": parse_date(cells.get(col_start)),
            "end": parse_date(cells.get(col_end)),
        }

    # Identify rows that have at least one child (they are not leaf rows)
    rows_with_children = {r["parent_id"] for r in row_map.values() if r["parent_id"]}

    # Apply all filters: leaf row + assigned to me + date range overlaps the target week
    leaf_rows = [
        r
        for r in row_map.values()
        if r["id"] not in rows_with_children
        and r["assigned"] == MY_NAME
        and r["start"] is not None
        and r["end"] is not None
        and r["end"] >= monday
        and r["start"] <= friday
    ]

    # Group leaf rows under their direct parent's task name
    grouped: dict[str, list[str]] = defaultdict(list)
    for r in leaf_rows:
        parent = row_map.get(r["parent_id"])
        group_title = parent["task"] if parent else r["task"]
        grouped[group_title].append(r["task"])

    return dict(grouped)


def to_gen_format(grouped: dict[str, list[str]]) -> str:
    """Serialize grouped tasks into the pipe-delimited format expected by gen.js.

    Format: "Title|item1|item2||Title2|item1"
    """
    parts = ["|".join([title] + items) for title, items in grouped.items()]
    return "||".join(parts)


def fmt_range(offset: int = 0) -> str:
    """Return a human-readable date range string, e.g. '5/4 ~ 5/8'."""
    mon, fri = get_week_range(offset)
    return f"{mon.month}/{mon.day} ~ {fri.month}/{fri.day}"


def main():
    for label, offset in [("Last week", -1), ("This week", 0)]:
        print(f"\n=== {label} ({fmt_range(offset)}) ===")
        tasks = fetch_tasks(offset)
        for title, items in tasks.items():
            print(f"  [{title}]")
            for item in items:
                print(f"    • {item}")
        print("\n  gen.js format:")
        print(f"  {to_gen_format(tasks)}")


if __name__ == "__main__":
    main()
