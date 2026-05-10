from datetime import date


def derive_html_content(monday: date, friday: date, tasks_org: dict[int, dict]) -> str:
    def format_children(children: list, depth: int = 0) -> str:
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
        "<p style='font-size:48pt; margin:0; margin-bottom:24px; text-align:left;'>"
        + f"<b>{week_str}</b>"
        + "</p>"
    )

    first_layer_items = "".join(
        "<p style='font-size:28pt; margin:20pt 0 0 0; text-align:left;'>"
        + task["task_name"]
        + "</p>"
        + "<ul>"
        + format_children(task.get("children", []))
        + "</ul>"
        for task in tasks_org.values()
    )
    return header + first_layer_items
