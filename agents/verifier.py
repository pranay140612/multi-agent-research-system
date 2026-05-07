"""
Verifier Agent — Validates that each step achieved its success criteria.
"""

from utils.llm import LLMClient
from utils.logger import AgentLogger
from models.schemas import Step, StepResult, StepStatus

VERIFIER_SYSTEM_PROMPT = """You are a Verifier Agent. Determine if a browser automation step achieved its goal.
Be practical: if data was extracted and relevant, the step is successful."""


class VerifierAgent:
    """Verifies that steps achieve their success criteria."""

    def __init__(self, llm: LLMClient):
        self.llm = llm
        self.logger = AgentLogger("verifier")

    async def verify(self, step: Step, result: StepResult, extracted_data: str) -> dict:
        """Verify if a step achieved its success criteria."""
        self.logger.info(f"Verifying step {step.id}: {step.description}")

        if not result.success:
            self.logger.error(f"Step {step.id} failed: {result.error}")
            return {"passed": False, "reason": result.error, "recommendation": "retry"}

        if step.action.value == "done":
            self.logger.success(f"Step {step.id}: Task complete")
            return {"passed": True, "reason": "Done", "recommendation": "proceed"}

        prompt = f"""Verify if this step achieved its goal.

STEP: {step.description}
CRITERIA: {step.success_criteria}
Page title: {result.page_title}
Data extracted: {extracted_data[:2000] if extracted_data else 'None'}

Respond JSON: {{"passed": bool, "confidence": 0-1, "reason": "...", "recommendation": "proceed/retry/skip"}}"""

        verification = await self.llm.generate_json(prompt, VERIFIER_SYSTEM_PROMPT)

        passed = verification.get("passed", False)
        reason = verification.get("reason", "")
        confidence = verification.get("confidence", 0.5)

        if passed or confidence > 0.5:
            step.status = StepStatus.SUCCESS
            self.logger.success(f"Step {step.id} PASSED: {reason}")
        else:
            step.status = StepStatus.FAILED
            self.logger.error(f"Step {step.id} FAILED: {reason}")

        return {
            "passed": passed,
            "reason": reason,
            "recommendation": verification.get("recommendation", "proceed"),
            "confidence": confidence,
        }
