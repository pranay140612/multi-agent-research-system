"""
Planner Agent — Decomposes user prompts into actionable browser steps.
Uses LLM to create a structured execution plan.
"""

from utils.llm import LLMClient
from utils.logger import AgentLogger
from models.schemas import Plan, Step, ActionType

PLANNER_SYSTEM_PROMPT = """You are a Planner Agent in a multi-agent browser automation system.
Your job is to take a user's request and decompose it into a sequence of browser actions.

Available actions:
- search_google: Search Google with a query string
- navigate: Go to a specific URL
- click: Click an element (by text or CSS selector)
- read_page: Extract and read page content
- scroll: Scroll up or down on a page
- open_tab: Open a new browser tab
- close_tab: Close current tab
- switch_tab: Switch to a different tab
- go_back: Go back in browser history
- extract_data: Extract specific data from page content
- done: Mark task as complete

Rules:
1. Start with search_google to find relevant pages
2. After navigating to a page, always use read_page to extract content
3. Use extract_data to pull specific information from page content
4. Be thorough — visit multiple sources for better results
5. Keep steps focused and specific
6. Typically aim for 8-15 steps for a research task
7. If the user asks for specific data (like buying links, company website links, LinkedIn profiles, prices, etc.), ensure this is EXPLICITLY stated in the `data_to_extract` field for the relevant steps.
8. End with a "done" action to compile results
"""


class PlannerAgent:
    """Decomposes user prompts into actionable browser automation steps."""

    def __init__(self, llm: LLMClient):
        self.llm = llm
        self.logger = AgentLogger("planner")

    async def create_plan(self, user_prompt: str) -> Plan:
        """Create an execution plan from a user prompt."""
        self.logger.info("Analyzing prompt and creating plan...")

        prompt = f"""Create a step-by-step browser automation plan for this user request:

USER REQUEST: "{user_prompt}"

Return a JSON object with this structure:
{{
    "goal": "Brief summary of the goal",
    "steps": [
        {{
            "id": 1,
            "action": "search_google",
            "description": "What this step does",
            "target": "search query or URL or selector",
            "data_to_extract": "What data to extract from this step",
            "success_criteria": "How to verify this step succeeded"
        }}
    ]
}}

Make the plan thorough. For research tasks, search multiple queries and visit multiple pages.
For comparison tasks, ensure you gather data for all items to compare.
Pay close attention to specific data points the user wants (e.g., "buying link", "LinkedIn URL"). Explicitly include these requirements in `data_to_extract`.
Always end with a "done" step that compiles all collected data into a final report."""

        result = await self.llm.generate_json(prompt, PLANNER_SYSTEM_PROMPT)

        if "error" in result and "raw" in result:
            self.logger.error("Failed to parse plan from LLM. Using fallback plan.")
            return self._fallback_plan(user_prompt)

        return self._parse_plan(result, user_prompt)

    async def replan(self, plan: Plan, context: str) -> list[Step]:
        """Generate new steps based on current progress and context."""
        self.logger.info("Re-planning based on current results...")

        completed = [
            {"id": s.id, "action": s.action.value, "description": s.description, "result": s.result or ""}
            for s in plan.completed_steps
        ]
        pending = [s.to_dict() for s in plan.pending_steps]

        prompt = f"""Based on the current progress, adjust the remaining plan.

ORIGINAL GOAL: {plan.goal}

COMPLETED STEPS: {completed}

REMAINING STEPS: {pending}

CURRENT CONTEXT: {context}

Return a JSON object with:
{{
    "steps": [
        {{
            "id": <next_id>,
            "action": "action_type",
            "description": "What this step does",
            "target": "target",
            "data_to_extract": "what to extract",
            "success_criteria": "how to verify"
        }}
    ],
    "reasoning": "Why these changes were made"
}}

You may add new steps, modify pending steps, or remove unnecessary ones.
If enough data has been collected, you can end with just a "done" step."""

        result = await self.llm.generate_json(prompt, PLANNER_SYSTEM_PROMPT)

        if "error" in result:
            return plan.pending_steps

        new_steps = []
        next_id = max(s.id for s in plan.steps) + 1 if plan.steps else 1

        for step_data in result.get("steps", []):
            try:
                action = ActionType(step_data.get("action", "read_page"))
            except ValueError:
                action = ActionType.READ_PAGE

            new_steps.append(Step(
                id=next_id,
                action=action,
                description=step_data.get("description") or "",
                target=step_data.get("target") or "",
                data_to_extract=step_data.get("data_to_extract") or "",
                success_criteria=step_data.get("success_criteria") or "",
            ))
            next_id += 1

        if result.get("reasoning"):
            self.logger.info(f"Replan reason: {result['reasoning']}")

        return new_steps

    def _parse_plan(self, data: dict, user_prompt: str) -> Plan:
        """Parse LLM response into a Plan object."""
        plan = Plan(goal=data.get("goal", user_prompt))

        for step_data in data.get("steps", []):
            try:
                action = ActionType(step_data.get("action", "read_page"))
            except ValueError:
                action = ActionType.READ_PAGE

            step = Step(
                id=step_data.get("id") or (len(plan.steps) + 1),
                action=action,
                description=step_data.get("description") or "",
                target=step_data.get("target") or "",
                data_to_extract=step_data.get("data_to_extract") or "",
                success_criteria=step_data.get("success_criteria") or "",
            )
            plan.steps.append(step)

        self.logger.success(f"Plan created with {len(plan.steps)} steps")
        return plan

    def _fallback_plan(self, user_prompt: str) -> Plan:
        """Create a basic fallback plan when LLM parsing fails."""
        plan = Plan(goal=user_prompt)
        plan.steps = [
            Step(
                id=1,
                action=ActionType.SEARCH_GOOGLE,
                description="Search for information",
                target=user_prompt,
                data_to_extract="Relevant results",
                success_criteria="Search results loaded",
            ),
            Step(
                id=2,
                action=ActionType.READ_PAGE,
                description="Read search results",
                target="",
                data_to_extract="Top results and links",
                success_criteria="Content extracted",
            ),
            Step(
                id=3,
                action=ActionType.DONE,
                description="Compile results",
                target="",
                data_to_extract="Final summary",
                success_criteria="Report generated",
            ),
        ]
        self.logger.warning("Using fallback plan due to LLM parse failure")
        return plan
