"""
Action Executor Agent — Processes step results and decides data storage.
Coordinates between browser actions and data extraction.
"""

from utils.llm import LLMClient
from utils.logger import AgentLogger
from models.schemas import Step, StepResult, Plan, ActionType


EXECUTOR_SYSTEM_PROMPT = """You are an Action Executor Agent. You process browser action results
and decide what data should be stored from each step.

Your job is to:
1. Analyze the extracted content from each step
2. Determine if the step achieved its goal
3. Identify key data points to store
4. Suggest if the browser should navigate to any specific links found"""


class ActionExecutorAgent:
    """Processes step results, stores data, and coordinates next actions."""

    def __init__(self, llm: LLMClient):
        self.llm = llm
        self.logger = AgentLogger("executor")

    async def process(self, step: Step, result: StepResult, extracted_data: str, plan: Plan) -> dict:
        """Process step result and determine data to store."""
        self.logger.info(f"Processing results for step {step.id}")

        if step.action == ActionType.DONE:
            return {"action": "complete", "data": extracted_data}

        if not result.success:
            self.logger.warning(f"Step {step.id} failed: {result.error}")
            return {
                "action": "retry_or_skip",
                "error": result.error,
                "suggestion": "Try an alternative approach or skip this step",
            }

        prompt = f"""Analyze the result of this browser automation step:

STEP: {step.description}
ACTION: {step.action.value}
TARGET: {step.target}
EXTRACTION GOAL: {step.data_to_extract}

PAGE TITLE: {result.page_title}
PAGE URL: {result.page_url}

EXTRACTED DATA:
{extracted_data[:5000]}

GOAL: {plan.goal}

Respond with a JSON object:
{{
    "success": true/false,
    "key_data": "The most important data extracted (concise but complete)",
    "data_quality": "high/medium/low",
    "urls_to_visit": ["url1", "url2"],
    "notes": "Any observations or suggestions"
}}"""

        analysis = await self.llm.generate_json(prompt, EXECUTOR_SYSTEM_PROMPT)

        if analysis.get("success", False) or analysis.get("key_data"):
            key_data = analysis.get("key_data", extracted_data[:2000])
            plan.add_data(step.id, step.description, key_data)
            self.logger.success(f"Data stored for step {step.id}")
        else:
            self.logger.warning(f"No useful data from step {step.id}")

        return analysis

    async def compile_final_report(self, plan: Plan) -> str:
        """Compile all collected data into a final report."""
        self.logger.info("Compiling final report...")

        collected = "\n\n".join(
            f"--- Step: {d['key']} ---\n{d['value']}" 
            for d in plan.collected_data
        )

        prompt = f"""Create a comprehensive final report based on all the research data collected.

ORIGINAL USER REQUEST: {plan.goal}

ALL COLLECTED DATA:
{collected[:15000]}

Create a well-structured, detailed report that answers the user's original request.
Use markdown formatting with headers, bullet points, and tables where appropriate.
If the user asked for comparisons, create comparison tables.
Include specific numbers, prices, names, and facts.
Be thorough and actionable in your recommendations."""

        report = await self.llm.generate(prompt, EXECUTOR_SYSTEM_PROMPT)
        self.logger.success("Final report compiled")
        return report
