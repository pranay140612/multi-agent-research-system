"""
Browser Manager — Manages the Playwright browser lifecycle.
Handles browser launch, page/tab management, and cleanup.
"""

import asyncio
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from config import Config
from utils.logger import AgentLogger


class BrowserManager:
    """Manages browser lifecycle and tab state using Playwright."""

    def __init__(self):
        self.logger = AgentLogger("browser")
        self._playwright = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._pages: list[Page] = []
        self._current_page_index: int = -1

    @property
    def current_page(self) -> Page | None:
        """Get the currently active page/tab."""
        if 0 <= self._current_page_index < len(self._pages):
            return self._pages[self._current_page_index]
        return None

    @property
    def tab_count(self) -> int:
        return len(self._pages)

    async def start(self):
        """Launch the browser and create initial context."""
        self.logger.info("Launching browser...")
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=Config.BROWSER_HEADLESS,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ],
        )
        self._context = await self._browser.new_context(
            viewport={"width": 1366, "height": 768},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
        )
        # Open initial tab
        page = await self._context.new_page()
        self._pages.append(page)
        self._current_page_index = 0
        self.logger.success("Browser launched successfully")

    async def stop(self):
        """Close the browser and clean up."""
        self.logger.info("Closing browser...")
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        self._pages = []
        self._current_page_index = -1
        self.logger.success("Browser closed")

    async def navigate(self, url: str) -> bool:
        """Navigate current tab to a URL."""
        page = self.current_page
        if not page:
            return False
        try:
            self.logger.info(f"Navigating to: {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=Config.BROWSER_TIMEOUT)
            await asyncio.sleep(1)  # Let page settle
            return True
        except Exception as e:
            self.logger.error(f"Navigation failed: {e}")
            return False

    async def search_google(self, query: str) -> bool:
        """Perform a Google search."""
        url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        return await self.navigate(url)

    async def click(self, selector: str) -> bool:
        """Click an element on the page."""
        page = self.current_page
        if not page:
            return False
        try:
            self.logger.info(f"Clicking: {selector}")
            # Try different strategies
            try:
                # First try CSS selector
                await page.click(selector, timeout=5000)
            except Exception:
                # Try text-based selector
                try:
                    await page.click(f"text={selector}", timeout=5000)
                except Exception:
                    # Try XPath
                    await page.click(f"xpath=//*[contains(text(), '{selector}')]", timeout=5000)
            await asyncio.sleep(1)
            return True
        except Exception as e:
            self.logger.error(f"Click failed: {e}")
            return False

    async def type_text(self, selector: str, text: str) -> bool:
        """Type text into an input field."""
        page = self.current_page
        if not page:
            return False
        try:
            self.logger.info(f"Typing into: {selector}")
            await page.fill(selector, text, timeout=5000)
            return True
        except Exception as e:
            self.logger.error(f"Type failed: {e}")
            return False

    async def get_page_content(self) -> dict:
        """Extract content from the current page."""
        page = self.current_page
        if not page:
            return {"error": "No active page"}

        try:
            title = await page.title()
            url = page.url

            # Extract text content from body
            text_content = await page.evaluate("""
                () => {
                    // Remove script and style elements
                    const scripts = document.querySelectorAll('script, style, noscript, iframe');
                    scripts.forEach(el => el.remove());
                    
                    // Get text from body
                    const body = document.body;
                    if (!body) return '';
                    
                    // Get all text nodes
                    const walker = document.createTreeWalker(
                        body,
                        NodeFilter.SHOW_TEXT,
                        null,
                        false
                    );
                    
                    let text = '';
                    let node;
                    while (node = walker.nextNode()) {
                        const trimmed = node.textContent.trim();
                        if (trimmed) {
                            text += trimmed + '\\n';
                        }
                    }
                    return text;
                }
            """)

            # Get links
            links = await page.evaluate("""
                () => {
                    const anchors = document.querySelectorAll('a[href]');
                    return Array.from(anchors).slice(0, 30).map(a => ({
                        text: a.textContent.trim().substring(0, 100),
                        href: a.href,
                    })).filter(l => l.text && l.href.startsWith('http'));
                }
            """)

            # Truncate content
            if len(text_content) > Config.PAGE_CONTENT_MAX_CHARS:
                text_content = text_content[:Config.PAGE_CONTENT_MAX_CHARS] + "\n... [truncated]"

            return {
                "title": title,
                "url": url,
                "text": text_content,
                "links": links,
            }
        except Exception as e:
            self.logger.error(f"Content extraction failed: {e}")
            return {"error": str(e)}

    async def scroll(self, direction: str = "down", amount: int = 500) -> bool:
        """Scroll the page."""
        page = self.current_page
        if not page:
            return False
        try:
            delta = amount if direction == "down" else -amount
            await page.mouse.wheel(0, delta)
            await asyncio.sleep(0.5)
            return True
        except Exception as e:
            self.logger.error(f"Scroll failed: {e}")
            return False

    async def open_tab(self, url: str = "") -> bool:
        """Open a new tab, optionally navigating to a URL."""
        try:
            page = await self._context.new_page()
            self._pages.append(page)
            self._current_page_index = len(self._pages) - 1
            self.logger.info(f"Opened new tab (total: {self.tab_count})")
            if url:
                await self.navigate(url)
            return True
        except Exception as e:
            self.logger.error(f"Open tab failed: {e}")
            return False

    async def close_tab(self, index: int = -1) -> bool:
        """Close a tab by index. Default closes current tab."""
        try:
            if index == -1:
                index = self._current_page_index
            if 0 <= index < len(self._pages):
                page = self._pages.pop(index)
                await page.close()
                if self._pages:
                    self._current_page_index = min(index, len(self._pages) - 1)
                else:
                    self._current_page_index = -1
                self.logger.info(f"Closed tab {index} (remaining: {self.tab_count})")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Close tab failed: {e}")
            return False

    async def switch_tab(self, index: int) -> bool:
        """Switch to a specific tab by index."""
        if 0 <= index < len(self._pages):
            self._current_page_index = index
            await self._pages[index].bring_to_front()
            self.logger.info(f"Switched to tab {index}")
            return True
        self.logger.error(f"Invalid tab index: {index}")
        return False

    async def go_back(self) -> bool:
        """Navigate back in history."""
        page = self.current_page
        if not page:
            return False
        try:
            await page.go_back(wait_until="domcontentloaded", timeout=Config.BROWSER_TIMEOUT)
            await asyncio.sleep(1)
            return True
        except Exception as e:
            self.logger.error(f"Go back failed: {e}")
            return False

    async def screenshot(self, path: str = "screenshot.png") -> str:
        """Take a screenshot of the current page."""
        page = self.current_page
        if not page:
            return ""
        try:
            await page.screenshot(path=path, full_page=False)
            self.logger.info(f"Screenshot saved: {path}")
            return path
        except Exception as e:
            self.logger.error(f"Screenshot failed: {e}")
            return ""

    async def wait_for(self, seconds: float = 2) -> bool:
        """Wait for a specified number of seconds."""
        await asyncio.sleep(seconds)
        return True
