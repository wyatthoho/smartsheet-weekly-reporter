# Weekly Report Generator

Fetch tasks from Smartsheet for the specified week and group them by parent task.

## Filtering criteria

- Assigned To == `EMPLOYEE`
- `End Date` >= Monday of the target week
- `Start Date` <= Friday of the target week
- Only leaf rows (no children) are included as action items
- Each leaf is grouped under its direct parent task name
