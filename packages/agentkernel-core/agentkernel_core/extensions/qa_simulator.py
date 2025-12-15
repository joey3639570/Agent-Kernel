"""QA Simulator using Playwright for automated browser testing.

This module provides a User Simulator that can interact with web
applications using vision-based understanding and browser automation.
"""

from __future__ import annotations

import asyncio
import base64
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class UserPersona(str, Enum):
    """Pre-defined user personas for testing."""

    NORMAL = "normal"
    CONFUSED = "confused"
    ANGRY = "angry"
    HACKER = "hacker"
    POWER_USER = "power_user"
    ELDERLY = "elderly"
    IMPATIENT = "impatient"


@dataclass
class PersonaConfig:
    """Configuration for a user persona.

    Attributes:
        name: Persona name.
        description: Detailed description for LLM.
        action_delay_ms: Delay between actions.
        error_tolerance: How many errors before giving up.
        exploration_rate: Probability of trying unexpected actions.
    """

    name: str
    description: str
    action_delay_ms: int = 1000
    error_tolerance: int = 3
    exploration_rate: float = 0.1


PERSONA_CONFIGS = {
    UserPersona.NORMAL: PersonaConfig(
        name="Normal User",
        description="A typical user who follows standard workflows and expects things to work as documented.",
        action_delay_ms=800,
        error_tolerance=2,
        exploration_rate=0.1,
    ),
    UserPersona.CONFUSED: PersonaConfig(
        name="Confused User",
        description="A user who gets easily confused, may click wrong buttons, and needs clear guidance.",
        action_delay_ms=2000,
        error_tolerance=5,
        exploration_rate=0.3,
    ),
    UserPersona.ANGRY: PersonaConfig(
        name="Angry User",
        description="An impatient user who gets frustrated easily and may spam clicks or try aggressive actions.",
        action_delay_ms=300,
        error_tolerance=1,
        exploration_rate=0.2,
    ),
    UserPersona.HACKER: PersonaConfig(
        name="Malicious User",
        description="A user attempting to find security vulnerabilities, XSS, SQL injection, or bypass restrictions.",
        action_delay_ms=500,
        error_tolerance=10,
        exploration_rate=0.5,
    ),
    UserPersona.POWER_USER: PersonaConfig(
        name="Power User",
        description="An experienced user who knows shortcuts, uses keyboard navigation, and expects advanced features.",
        action_delay_ms=400,
        error_tolerance=2,
        exploration_rate=0.15,
    ),
    UserPersona.ELDERLY: PersonaConfig(
        name="Elderly User",
        description="An older user who types slowly, may have vision difficulties, and prefers large UI elements.",
        action_delay_ms=3000,
        error_tolerance=4,
        exploration_rate=0.05,
    ),
    UserPersona.IMPATIENT: PersonaConfig(
        name="Impatient User",
        description="A user who doesn't wait for pages to load and may interrupt actions.",
        action_delay_ms=200,
        error_tolerance=1,
        exploration_rate=0.25,
    ),
}


class BrowserAction(BaseModel):
    """An action to perform in the browser.

    Attributes:
        action_type: Type of action (click, type, scroll, etc.).
        selector: CSS selector for target element.
        value: Value for type actions.
        options: Additional action options.
    """

    action_type: str
    selector: Optional[str] = None
    value: Optional[str] = None
    options: Dict[str, Any] = Field(default_factory=dict)


class PageState(BaseModel):
    """State of the current page.

    Attributes:
        url: Current URL.
        title: Page title.
        screenshot: Base64 encoded screenshot.
        html_snippet: Relevant HTML snippet.
        visible_elements: List of visible interactive elements.
        errors: Any JavaScript errors on page.
    """

    url: str
    title: str
    screenshot: Optional[str] = None
    html_snippet: Optional[str] = None
    visible_elements: List[Dict[str, Any]] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


class TestResult(BaseModel):
    """Result of a test session.

    Attributes:
        success: Whether the goal was achieved.
        steps_taken: Number of actions performed.
        errors_encountered: List of errors found.
        screenshots: Screenshots at key moments.
        action_log: Full log of actions taken.
        duration_ms: Total test duration.
    """

    success: bool
    steps_taken: int = 0
    errors_encountered: List[str] = Field(default_factory=list)
    screenshots: List[str] = Field(default_factory=list)
    action_log: List[Dict[str, Any]] = Field(default_factory=list)
    duration_ms: float = 0.0


class QASimulator:
    """Playwright-based QA simulator for web application testing.

    This class provides:
    - Browser automation via Playwright
    - Vision-based page understanding
    - Persona-driven test behavior
    - Automated test result reporting
    """

    def __init__(
        self,
        persona: UserPersona = UserPersona.NORMAL,
        headless: bool = True,
        viewport_width: int = 1280,
        viewport_height: int = 720,
    ) -> None:
        """Initialize the QA Simulator.

        Args:
            persona: User persona to simulate.
            headless: Run browser in headless mode.
            viewport_width: Browser viewport width.
            viewport_height: Browser viewport height.
        """
        self.persona = persona
        self.persona_config = PERSONA_CONFIGS[persona]
        self.headless = headless
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height

        self._browser: Optional[Any] = None
        self._context: Optional[Any] = None
        self._page: Optional[Any] = None
        self._action_log: List[Dict[str, Any]] = []
        self._errors: List[str] = []

    async def start(self) -> None:
        """Start the browser and create a new page."""
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            raise ImportError("playwright package required. Install with: pip install playwright")

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=self.headless)
        self._context = await self._browser.new_context(
            viewport={"width": self.viewport_width, "height": self.viewport_height},
            user_agent=f"QASimulator/{self.persona.value}",
        )
        self._page = await self._context.new_page()

        # Set up error tracking
        self._page.on("pageerror", lambda err: self._errors.append(str(err)))
        self._page.on("console", self._handle_console)

        logger.info("QA Simulator started with %s persona", self.persona_config.name)

    async def stop(self) -> None:
        """Close the browser and clean up."""
        if self._browser:
            await self._browser.close()
        if hasattr(self, "_playwright") and self._playwright:
            await self._playwright.stop()
        logger.info("QA Simulator stopped")

    async def _handle_console(self, msg: Any) -> None:
        """Handle console messages from the page.

        Args:
            msg: Console message object.
        """
        if msg.type == "error":
            self._errors.append(f"Console error: {msg.text}")

    async def navigate(self, url: str) -> PageState:
        """Navigate to a URL.

        Args:
            url: URL to navigate to.

        Returns:
            Current page state.
        """
        if not self._page:
            raise RuntimeError("Simulator not started")

        await self._page.goto(url, wait_until="networkidle")
        self._log_action("navigate", url=url)
        return await self.get_page_state()

    async def get_page_state(self, include_screenshot: bool = True) -> PageState:
        """Get the current page state.

        Args:
            include_screenshot: Whether to capture a screenshot.

        Returns:
            PageState object.
        """
        if not self._page:
            raise RuntimeError("Simulator not started")

        # Get basic info
        url = self._page.url
        title = await self._page.title()

        # Get screenshot
        screenshot = None
        if include_screenshot:
            screenshot_bytes = await self._page.screenshot()
            screenshot = base64.b64encode(screenshot_bytes).decode()

        # Get visible interactive elements
        elements = await self._page.evaluate("""
            () => {
                const interactable = document.querySelectorAll(
                    'button, a, input, select, textarea, [role="button"], [onclick]'
                );
                return Array.from(interactable).slice(0, 50).map(el => ({
                    tag: el.tagName,
                    text: el.innerText?.slice(0, 100) || '',
                    type: el.type || '',
                    id: el.id || '',
                    class: el.className || '',
                    visible: el.offsetParent !== null,
                }));
            }
        """)

        return PageState(
            url=url,
            title=title,
            screenshot=screenshot,
            visible_elements=elements,
            errors=list(self._errors),
        )

    async def execute_action(self, action: BrowserAction) -> bool:
        """Execute a browser action.

        Args:
            action: The action to execute.

        Returns:
            True if action succeeded.
        """
        if not self._page:
            raise RuntimeError("Simulator not started")

        try:
            # Add persona-based delay
            await asyncio.sleep(self.persona_config.action_delay_ms / 1000)

            if action.action_type == "click":
                await self._page.click(action.selector, **action.options)

            elif action.action_type == "type":
                await self._page.fill(action.selector, action.value or "", **action.options)

            elif action.action_type == "press":
                await self._page.press(action.selector or "body", action.value or "Enter")

            elif action.action_type == "scroll":
                await self._page.evaluate(f"window.scrollBy(0, {action.value or 300})")

            elif action.action_type == "hover":
                await self._page.hover(action.selector, **action.options)

            elif action.action_type == "select":
                await self._page.select_option(action.selector, action.value)

            elif action.action_type == "wait":
                await asyncio.sleep(float(action.value or 1))

            self._log_action(action.action_type, selector=action.selector, value=action.value)
            return True

        except Exception as e:
            self._errors.append(f"Action failed: {action.action_type} - {e}")
            self._log_action(action.action_type, error=str(e))
            return False

    def _log_action(self, action_type: str, **kwargs: Any) -> None:
        """Log an action for later reporting.

        Args:
            action_type: Type of action.
            **kwargs: Action details.
        """
        self._action_log.append({
            "timestamp": datetime.now().isoformat(),
            "action": action_type,
            **kwargs,
        })

    async def run_test(
        self,
        start_url: str,
        goal: str,
        max_steps: int = 20,
        decision_fn: Optional[Any] = None,
    ) -> TestResult:
        """Run an automated test session.

        Args:
            start_url: URL to start testing from.
            goal: Description of the test goal.
            max_steps: Maximum actions to take.
            decision_fn: Async function that takes PageState and returns BrowserAction.

        Returns:
            TestResult with test outcome.
        """
        start_time = datetime.now()
        self._action_log = []
        self._errors = []
        screenshots = []

        await self.navigate(start_url)

        for step in range(max_steps):
            state = await self.get_page_state()

            # Capture screenshot at key moments
            if step % 5 == 0 and state.screenshot:
                screenshots.append(state.screenshot)

            # Get next action from decision function
            if decision_fn:
                try:
                    action = await decision_fn(state, goal, self.persona_config)
                    if action is None:
                        # Decision function says we're done
                        break
                    await self.execute_action(action)
                except Exception as e:
                    self._errors.append(f"Decision error: {e}")
                    if len(self._errors) >= self.persona_config.error_tolerance:
                        break
            else:
                # No decision function, just capture state
                break

        duration = (datetime.now() - start_time).total_seconds() * 1000

        return TestResult(
            success=len(self._errors) == 0,
            steps_taken=len(self._action_log),
            errors_encountered=list(self._errors),
            screenshots=screenshots,
            action_log=list(self._action_log),
            duration_ms=duration,
        )

    def get_persona_prompt(self) -> str:
        """Get a prompt describing the current persona for LLM.

        Returns:
            Persona description string.
        """
        return f"""You are simulating a {self.persona_config.name}.
{self.persona_config.description}

Behavior characteristics:
- Action speed: {'Fast' if self.persona_config.action_delay_ms < 500 else 'Slow' if self.persona_config.action_delay_ms > 1500 else 'Normal'}
- Error tolerance: {'Low' if self.persona_config.error_tolerance <= 2 else 'High'}
- Exploration tendency: {'High' if self.persona_config.exploration_rate > 0.2 else 'Low'}

When deciding on actions, behave according to this persona's characteristics."""

