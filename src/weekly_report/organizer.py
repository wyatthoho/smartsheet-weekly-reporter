import copy


def organize_family_tasks(tasks: dict[int, dict]) -> dict[int, dict]:
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
