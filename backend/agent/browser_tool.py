"""Browser 浏览器自动化工具 (M4.8) — Playwright

导航 / 点击 / 填表 / 截图 / 取文本。Playwright 可选, 未装时优雅降级。
"""

from __future__ import annotations

import logging
from typing import Any, List, Optional

logger = logging.getLogger(__name__)

try:
    from playwright.async_api import async_playwright  # type: ignore

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    async_playwright = None  # type: ignore[assignment, misc]


class BrowserSession:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self._pw = None
        self._browser = None
        self._page = None

    async def get_page(self):
        if self._page is not None:
            return self._page
        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError(
                "Playwright 未安装 (pip install playwright && playwright install chromium)"
            )
        if self._pw is None:
            self._pw = await async_playwright().start()
            self._browser = await self._pw.chromium.launch(headless=self.headless)
        self._page = await self._browser.new_page()
        return self._page

    async def close(self) -> None:
        if self._browser is not None:
            try:
                await self._browser.close()
            except Exception as e:
                logger.warning("关闭浏览器失败: %s", e)
        if self._pw is not None:
            try:
                await self._pw.stop()
            except Exception:
                pass
        self._pw = self._browser = self._page = None

    @property
    def available(self) -> bool:
        return PLAYWRIGHT_AVAILABLE


_global_session: Optional[BrowserSession] = None


def get_browser_session() -> BrowserSession:
    global _global_session
    if _global_session is None:
        _global_session = BrowserSession()
    return _global_session


async def close_browser_session() -> None:
    global _global_session
    if _global_session is not None:
        await _global_session.close()
        _global_session = None


async def _navigate(url: str, timeout_ms: int = 30000) -> str:
    if not url.startswith(("http://", "https://")):
        return "URL 必须以 http(s):// 开头"
    session = get_browser_session()
    if not session.available:
        return "Browser unavailable (Playwright 未安装)"
    try:
        page = await session.get_page()
        await page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")
        return f"已导航到 {url}, 标题: {await page.title()}"
    except Exception as e:
        return f"浏览器导航失败: {e}"


async def _extract_text(max_chars: int = 4000) -> str:
    try:
        page = await get_browser_session().get_page()
        text = await page.evaluate("() => document.body ? document.body.innerText : ''")
        return text[:max_chars]
    except Exception as e:
        return f"提取页面文本失败: {e}"


async def _click(selector: str) -> str:
    try:
        await (await get_browser_session().get_page()).click(selector, timeout=10000)
        return f"已点击: {selector}"
    except Exception as e:
        return f"点击失败 ({selector}): {e}"


async def _fill(selector: str, value: str) -> str:
    try:
        await (await get_browser_session().get_page()).fill(
            selector, value, timeout=10000
        )
        return f"已填充 {selector}"
    except Exception as e:
        return f"填充失败 ({selector}): {e}"


async def _screenshot() -> str:
    try:
        b64 = await (await get_browser_session().get_page()).screenshot(
            full_page=True, type="png"
        )
        import base64

        return f"data:image/png;base64,{base64.b64encode(b64).decode()}"
    except Exception as e:
        return f"截图失败: {e}"


def build_browser_tools() -> List[Any]:
    if not PLAYWRIGHT_AVAILABLE:
        logger.warning("Playwright 未安装, 浏览器工具不可用")
        return []
    try:
        from langchain_core.tools import tool
    except ImportError:
        logger.warning("langchain_core 未安装, 无法构建浏览器工具")
        return []

    @tool
    async def browser_navigate(url: str, timeout_ms: int = 30000) -> str:
        """Navigate the browser to a URL and wait for the page to load."""
        return await _navigate(url, timeout_ms)

    @tool
    async def browser_extract_text(max_chars: int = 4000) -> str:
        """Extract the visible text of the current browser page."""
        return await _extract_text(max_chars)

    @tool
    async def browser_click(selector: str) -> str:
        """Click the element matching the given CSS selector."""
        return await _click(selector)

    @tool
    async def browser_fill(selector: str, value: str) -> str:
        """Fill text into the input matching the given CSS selector."""
        return await _fill(selector, value)

    @tool
    async def browser_screenshot() -> str:
        """Take a screenshot of the current page, returns a base64 data URL."""
        return await _screenshot()

    @tool
    async def browser_get_url() -> str:
        """Get the current page URL."""
        try:
            return f"当前 URL: {(await get_browser_session().get_page()).url}"
        except Exception as e:
            return f"获取 URL 失败: {e}"

    return [
        browser_navigate,
        browser_extract_text,
        browser_click,
        browser_fill,
        browser_screenshot,
        browser_get_url,
    ]
