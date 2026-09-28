# Robocorp Order Automation

This project automates ordering robots from RobotSpareBin Industries using Robocorp and Playwright.

It reads order data from `orders.csv`, fills the robot order form, handles the consent popup, submits each order, saves the receipt PDF, and zips the generated output files.

## What this bot does

- Opens the RobotSpareBin order page
- Downloads and refreshes the latest order list
- Fills the form for each row in the CSV
- Handles the popup dialog when it appears
- Submits each order and waits for the receipt
- Saves receipt PDFs into the output folder
- Packages receipts into a ZIP archive

## Project files

- [tasks.py](tasks.py) — main automation logic
- [robot.yaml](robot.yaml) — Robocorp task configuration
- [conda.yaml](conda.yaml) — Python and dependency environment
- [orders.csv](orders.csv) — order data source
- [output/](output/) — generated runtime artifacts such as PDFs and logs

## Prerequisites

- Python environment managed through Robocorp/Conda
- Robocorp task runner or VS Code with the relevant tooling
- Browser support for the configured browser engine

## Run the task

From the project folder:

```bash
python -m robocorp.tasks run tasks.py
```

Or in VS Code, run the task configured in [robot.yaml](robot.yaml).

## Output

After the task finishes, check the generated files in the output folder, especially:

- `output/log.html`
- `output/Reciept/`
- `output/Reciept.zip`

## Notes

- The automation includes a popup guard to avoid failing when the consent dialog is hidden instead of visible.
- The order CSV is refreshed before processing so the latest data is used for each run.
- The project is configured to work with the Robocorp browser layer and the managed Python environment.

## Related resources

- [Robocorp Documentation](https://robocorp.com/docs)
- [Robocorp GitHub](https://github.com/robocorp/robocorp)
- [Playwright](https://playwright.dev/)
