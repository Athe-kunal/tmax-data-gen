You're a web developer building a feature. There's a small counter widget
at /home/user/app/index.html (+ /home/user/app/script.js) with a bug report: "the
on-page count doesn't match how many times I clicked the button."

Fix /home/user/app/script.js so that after N clicks of the "+1" button, the
`#count` element's text is exactly the string `N` (starting from `0`
before any clicks). Do not change index.html's structure/ids.

`playwright` (Python) is already installed. To check your fix without
guessing, you can run a quick headless-browser check as plain text output
(no screenshots - this endpoint's model can't accept image content), e.g.:
    python3 -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    page = p.chromium.launch().new_page()
    page.goto('file:///home/user/app/index.html')
    b = page.locator('#increment')
    for _ in range(3):
        b.click()
    print(page.locator('#count').inner_text())
"
That should print exactly "3". Use it (or just read/reason about the JS)
to verify your fix before finishing.

