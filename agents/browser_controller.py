"""
Browser Controller Agent — Executes browser actions based on step instructions.
Translates high-level actions into Playwright commands.
"""

from browser.manager import BrowserManager
from models.schemas import Step, ActionType, StepResult
from utils.logger import AgentLogger


class BrowserControllerAgent:
    """Executes browser actions: navigate, click, search, tab management, etc."""

    def __init__(self, browser: BrowserManager):
        self.browser = browser
        self.logger = AgentLogger("browser")

    async def execute_action(self, step: Step) -> StepResult:
        """Execute a browser action based on the step."""
        action_map = {
            ActionType.SEARCH_GOOGLE: self._search,
            ActionType.NAVIGATE: self._navigate,
            ActionType.CLICK: self._click,
            ActionType.TYPE_TEXT: self._type,
            ActionType.SCROLL: self._scroll,
            ActionType.OPEN_TAB: self._open_tab,
            ActionType.CLOSE_TAB: self._close_tab,
            ActionType.SWITCH_TAB: self._switch_tab,
            ActionType.GO_BACK: self._go_back,
            ActionType.SCREENSHOT: self._screenshot,
            ActionType.WAIT: self._wait,
            ActionType.READ_PAGE: self._read_page,
            ActionType.EXTRACT_DATA: self._read_page,
            ActionType.DONE: self._done,
        }

        handler = action_map.get(step.action, self._unknown)
        self.logger.info(f"Executing: {step.action.value} → {step.description}")

        try:
            return await handler(step)
        except Exception as e:
            self.logger.error(f"Action failed: {e}")
            return StepResult(
                step_id=step.id,
                success=False,
                error=str(e),
            )

    async def _search(self, step: Step) -> StepResult:
        """Perform a Google search."""
        success = await self.browser.search_google(step.target)
        page_content = await self.browser.get_page_content() if success else {}
        return StepResult(
            step_id=step.id,
            success=success,
            data=page_content.get("text", "")[:5000] if success else "",
            page_title=page_content.get("title", ""),
            page_url=page_content.get("url", ""),
        )

    async def _navigate(self, step: Step) -> StepResult:
        """Navigate to a URL."""
        success = await self.browser.navigate(step.target)
        page_content = await self.browser.get_page_content() if success else {}
        return StepResult(
            step_id=step.id,
            success=success,
            data=page_content.get("text", "")[:5000] if success else "",
            page_title=page_content.get("title", ""),
            page_url=page_content.get("url", ""),
        )

    async def _click(self, step: Step) -> StepResult:
        """Click an element."""
        success = await self.browser.click(step.target)
        page_content = await self.browser.get_page_content() if success else {}
        return StepResult(
            step_id=step.id,
            success=success,
            data=page_content.get("text", "")[:3000] if success else "",
            page_title=page_content.get("title", ""),
            page_url=page_content.get("url", ""),
        )

    async def _type(self, step: Step) -> StepResult:
        """Type text into a field."""
        parts = step.target.split("|", 1)
        selector = parts[0].strip()
        text = parts[1].strip() if len(parts) > 1 else ""
        success = await self.browser.type_text(selector, text)
        return StepResult(step_id=step.id, success=success)

    async def _scroll(self, step: Step) -> StepResult:
        """Scroll the page."""
        direction = "down" if "down" in step.target.lower() else "up"
        success = await self.browser.scroll(direction)
        return StepResult(step_id=step.id, success=success)

    async def _open_tab(self, step: Step) -> StepResult:
        """Open a new tab."""
        success = await self.browser.open_tab(step.target or "")
        return StepResult(step_id=step.id, success=success)

    async def _close_tab(self, step: Step) -> StepResult:
        """Close current tab."""
        success = await self.browser.close_tab()
        return StepResult(step_id=step.id, success=success)

    async def _switch_tab(self, step: Step) -> StepResult:
        """Switch to a specific tab."""
        try:
            index = int(step.target)
        except (ValueError, TypeError):
            index = 0
        success = await self.browser.switch_tab(index)
        return StepResult(step_id=step.id, success=success)

    async def _go_back(self, step: Step) -> StepResult:
        """Go back in browser history."""
        success = await self.browser.go_back()
        page_content = await self.browser.get_page_content() if success else {}
        return StepResult(
            step_id=step.id,
            success=success,
            data=page_content.get("text", "")[:3000] if success else "",
            page_title=page_content.get("title", ""),
            page_url=page_content.get("url", ""),
        )

    async def _screenshot(self, step: Step) -> StepResult:
        """Take a screenshot."""
        path = await self.browser.screenshot(step.target or "screenshot.png")
        return StepResult(
            step_id=step.id,
            success=bool(path),
            screenshot_path=path,
        )

    async def _wait(self, step: Step) -> StepResult:
        """Wait for a duration."""
        try:
            seconds = float(step.target)
        except (ValueError, TypeError):
            seconds = 2
        success = await self.browser.wait_for(seconds)
        return StepResult(step_id=step.id, success=success)

    async def _read_page(self, step: Step) -> StepResult:
        """Read/extract page content."""
        page_content = await self.browser.get_page_content()
        return StepResult(
            step_id=step.id,
            success="error" not in page_content,
            data=page_content.get("text", ""),
            page_title=page_content.get("title", ""),
            page_url=page_content.get("url", ""),
        )

    async def _done(self, step: Step) -> StepResult:
        """Mark task as done."""
        return StepResult(step_id=step.id, success=True, data="Task completed")

    async def _unknown(self, step: Step) -> StepResult:
        """Handle unknown actions."""
        self.logger.warning(f"Unknown action: {step.action}")
        return StepResult(step_id=step.id, success=False, error=f"Unknown action: {step.action}")
