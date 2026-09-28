import os
import csv
from pathlib import Path
import ssl
import shutil
import time
import zipfile
from urllib.request import Request, urlopen


from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from robocorp.tasks import task
from robocorp import browser

 
@task

def order_robots_from_RobotSpareBin():

    ensure_output_log_file()
    clean_receipt_folder()

    # Prefer a preinstalled browser on the runner to avoid Playwright CDN downloads that

    # fail in hosted environments with certificate/network issues.

    # Order: Edge -> Chrome.

    browser.configure(

        browser_engine="msedge",

        install=False,

        headless=False,

        viewport_size=(1366, 768),

        slowmo=1000,

    )

    try:

        open_robot_order_website()

    except Exception:

        browser.configure(

            browser_engine="chrome",

            install=False,

            headless=False,

            viewport_size=(1366, 768),

            slowmo=1000,

        )

    open_robot_order_website()

    time.sleep(int(os.getenv("BROWSER_WAIT_BEFORE_LOGIN_SECONDS", "5")))

    time.sleep(int(os.getenv("BROWSER_WAIT_BEFORE_LOGIN_SECONDS", "5")))

    for sales_rep in download_csv_file():

        fill_and_order_form(sales_rep)

    zip_receipts()

 

    """

    Orders robots from RobotSpareBin Industries Inc.

    Saves the order HTML receipt as a PDF file.

    Saves the screenshot of the ordered robot.

    Embeds the screenshot of the robot to the PDF receipt.

    Creates ZIP archive of the receipts and the images.

    """

 

def ensure_output_log_file():
    """Keeps the default Robocorp output log present so framework cleanup works."""
    output_dir = Path("output")
    output_dir.mkdir(parents=True, exist_ok=True)
    log_file = output_dir / "output.robolog"
    if not log_file.exists():
        log_file.touch()


def clean_receipt_folder():

    """Removes receipts from the previous run while keeping the folder available."""

    receipt_folder = Path("output") / "Reciept"

    receipt_folder.mkdir(parents=True, exist_ok=True)

 

    for receipt_path in receipt_folder.iterdir():

        if receipt_path.is_dir() and not receipt_path.is_symlink():

            shutil.rmtree(receipt_path)

        else:

            receipt_path.unlink()

 

def dismiss_popup_if_present():

    """Dismisses the consent popup when it is currently visible."""

    popup = browser.page().locator(".modal")

    if popup.count() == 0:
        return

    if not popup.is_visible():
        return

    try:
        popup.get_by_role("button", name="OK").click(timeout=1000)
    except PlaywrightTimeoutError:
        pass

 

def run_with_popup_handling(action):

    """Runs a page action, retrying once if the popup intercepts it."""

    dismiss_popup_if_present()

    try:

        action()

    except PlaywrightTimeoutError:

        dismiss_popup_if_present()

        action()

 

def click_order_until_receipt(page):

    """Retries Order when the site reports a transient server error."""

    receipt = page.locator("#receipt")

    server_error = page.locator(".alert-danger")

 

    for _ in range(10):

        run_with_popup_handling(lambda: page.click("#order"))

        try:

            receipt.wait_for(state="visible", timeout=5000)

            return

        except PlaywrightTimeoutError:

            if not server_error.is_visible():

                raise

 

    raise RuntimeError("The order could not be submitted after 10 attempts.")

 

def open_robot_order_website():

    """

    Opens the RobotSpareBin Industries Inc. website.

    Navigates to the robot order page.

    """

    page = browser.goto("https://robotsparebinindustries.com/#/robot-order")

    page.set_viewport_size({"width": 1366, "height": 768})

    page.evaluate("document.body.style.zoom = '80%'")

 

def close_browser():

    """Closes the current browser page when an explicit close is needed."""

    browser.page().close()

 

def zip_receipts():

    """Overwrites output/Reciept.zip with the current receipt files."""

    receipt_folder = Path("output") / "Reciept"

    archive_path = Path("output") / "Reciept.zip"

 

    with zipfile.ZipFile(

        archive_path,

        mode="w",

        compression=zipfile.ZIP_DEFLATED,

    ) as archive:

        for receipt_path in receipt_folder.iterdir():

            if receipt_path.is_file():

                archive.write(

                    receipt_path,

                    arcname=Path("Reciept") / receipt_path.name,

                )

 

def download_csv_file():

    """Downloads orders.csv, replaces the local copy, and returns its rows."""

    url = "https://robotsparebinindustries.com/orders.csv"

    request = Request(

        url,

        headers={

            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",

            "Accept": "text/csv,*/*;q=0.1",

            "Referer": "https://robotsparebinindustries.com/",

        },

    )

    with urlopen(

        request,

        timeout=30,

        context=ssl._create_unverified_context(),

    ) as response:

        content = response.read()

 

    csv_path = Path("orders.csv")

    temporary_csv_path = csv_path.with_name(".orders.csv.tmp")

    with open(temporary_csv_path, "wb") as csv_file:

        csv_file.write(content)

    try:

        os.replace(temporary_csv_path, csv_path)

    except PermissionError:

        csv_path.unlink(missing_ok=True)

        os.replace(temporary_csv_path, csv_path)

 

    with open(csv_path, "r", newline="", encoding="utf-8-sig") as csv_file:

        return list(csv.DictReader(csv_file))

 

def fill_and_order_form(sales_rep):

    """Fills, previews, saves, and submits one robot order."""

    page = browser.page()

    receipt_folder = Path("output") / "Reciept"

    receipt_folder.mkdir(parents=True, exist_ok=True)

 

    run_with_popup_handling(

        lambda: page.select_option("#head", str(sales_rep["Head"]))

    )

    run_with_popup_handling(

        lambda: page.locator(

            f"input[name='body'][value='{sales_rep['Body']}']"

        ).check()

    )

    run_with_popup_handling(

        lambda: page.get_by_placeholder("Enter the part number for the legs").fill(

            str(sales_rep["Legs"])

        )

    )

    run_with_popup_handling(

        lambda: page.get_by_placeholder("Shipping address").fill(sales_rep["Address"])

    )

    run_with_popup_handling(lambda: page.click("#preview"))

    page.locator("#robot-preview").wait_for(state="visible")

 

    click_order_until_receipt(page)

    receipt_path = receipt_folder / f"receipt_{sales_rep['Order number']}.pdf"

    page.pdf(path=str(receipt_path), format="A4")

 

    run_with_popup_handling(lambda: page.click("#order-another"))