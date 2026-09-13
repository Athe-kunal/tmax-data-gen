import pathlib

from playwright.sync_api import sync_playwright

HTML_PATH = "/home/user/app/index.html"
SCREENSHOT_DIR = pathlib.Path("/logs/verifier/screenshots")


def test_counter_increments_by_one_and_updates_immediately():
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(f"file://{HTML_PATH}")

        page.screenshot(path=str(SCREENSHOT_DIR / "click_0.png"))
        assert page.locator("#count").inner_text() == "0"

        button = page.locator("#increment")
        for i, expected in enumerate(("1", "2", "3"), start=1):
            button.click()
            page.screenshot(path=str(SCREENSHOT_DIR / f"click_{i}.png"))
            actual = page.locator("#count").inner_text()
            assert actual == expected, f"after click {i}, expected #count={expected!r}, got {actual!r}"

        browser.close()

