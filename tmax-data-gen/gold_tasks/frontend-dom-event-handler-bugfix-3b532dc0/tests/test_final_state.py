from playwright.sync_api import sync_playwright

HTML_PATH = "/home/user/app/index.html"


def test_counter_increments_by_one_and_updates_immediately():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(f"file://{HTML_PATH}")

        assert page.locator("#count").inner_text() == "0"

        button = page.locator("#increment")
        for expected in ("1", "2", "3"):
            button.click()
            actual = page.locator("#count").inner_text()
            assert actual == expected, f"after a click, expected #count={expected!r}, got {actual!r}"

        browser.close()

