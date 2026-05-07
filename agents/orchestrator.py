"""
Orchestrator — Master coordinator for the multi-agent browser system.
Manages the execution loop: Plan → Execute → Read → Verify → Replan.
"""

import asyncio
from utils.llm import LLMClient
from utils.logger import AgentLogger, console
from models.schemas import Plan, StepStatus, ActionType
from browser.manager import BrowserManager
from agents.planner import PlannerAgent
from agents.browser_controller import BrowserControllerAgent
from agents.webpage_reader import WebpageReaderAgent
from agents.action_executor import ActionExecutorAgent
from agents.verifier import VerifierAgent
from config import Config


class Orchestrator:
    """Master coordinator that runs the full agent pipeline."""

    def __init__(self):
        self.logger = AgentLogger("orchestrator")
        self.llm = LLMClient()
        self.browser_manager = BrowserManager()
        self.planner = PlannerAgent(self.llm)
        self.browser_controller = BrowserControllerAgent(self.browser_manager)
        self.reader = WebpageReaderAgent(self.llm)
        self.executor = ActionExecutorAgent(self.llm)
        self.verifier = VerifierAgent(self.llm)

    async def run(self, user_prompt: str) -> str:
        """Run the full multi-agent pipeline for a user prompt."""
        AgentLogger.header()
        self.logger.info(f"Received prompt: {user_prompt}")
        AgentLogger.divider("Phase 1: Planning")

        # Phase 1: Create plan
        plan = await self.planner.create_plan(user_prompt)
        AgentLogger.plan_table([s.to_dict() for s in plan.steps])

        # Phase 2: Execute
        AgentLogger.divider("Phase 2: Execution")
        await self.browser_manager.start()

        try:
            step_count = 0
            retry_count = 0

            while plan.current_step and step_count < Config.MAX_STEPS:
                step = plan.current_step
                step.status = StepStatus.RUNNING
                step_count += 1
                total = len(plan.steps)

                self.logger.step(step_count, total, f"[{step.action.value}] {step.description}")

                # 1. Browser Controller: Execute action
                result = await self.browser_controller.execute_action(step)

                # 2. Webpage Reader: Extract content
                extracted = ""
                if result.success and step.action not in (ActionType.DONE, ActionType.WAIT, ActionType.CLOSE_TAB):
                    extracted = await self.reader.extract(step, result.data, result.page_title, result.page_url)

                # 3. Action Executor: Process and store
                if step.action == ActionType.DONE:
                    plan.final_report = await self.executor.compile_final_report(plan)
                    step.status = StepStatus.SUCCESS
                    step.result = "Report compiled"
                    break
                else:
                    analysis = await self.executor.process(step, result, extracted, plan)

                # 4. Verifier: Check success
                verification = await self.verifier.verify(step, result, extracted)

                # 5. Handle verification result
                rec = verification.get("recommendation", "proceed")
                if rec == "retry" and retry_count < Config.MAX_RETRIES:
                    retry_count += 1
                    step.status = StepStatus.PENDING
                    self.logger.warning(f"Retrying step {step.id} (attempt {retry_count})")
                    continue
                elif rec == "skip":
                    step.status = StepStatus.SKIPPED
                    self.logger.warning(f"Skipping step {step.id}")
                elif step.status != StepStatus.SUCCESS:
                    step.status = StepStatus.SUCCESS  # Force proceed

                step.result = extracted[:500] if extracted else "Done"
                retry_count = 0

                # 6. Check if we need to navigate to discovered URLs
                urls = analysis.get("urls_to_visit", []) if isinstance(analysis, dict) else []
                if urls and len(plan.pending_steps) < 3:
                    await self._add_url_steps(plan, urls[:2])

                # Update plan display
                AgentLogger.plan_table([s.to_dict() for s in plan.steps])

            # Phase 3: Compile report if not already done
            AgentLogger.divider("Phase 3: Report")
            if not plan.final_report:
                plan.final_report = await self.executor.compile_final_report(plan)

            AgentLogger.final_report(plan.final_report)

        finally:
            await self.browser_manager.stop()

        return plan.final_report

    async def _add_url_steps(self, plan: Plan, urls: list[str]):
        """Dynamically add steps to visit discovered URLs."""
        next_id = max(s.id for s in plan.steps) + 1

        for url in urls:
            if not isinstance(url, str) or not url.startswith("http"):
                continue
            from models.schemas import Step
            nav_step = Step(
                id=next_id,
                action=ActionType.NAVIGATE,
                description=f"Visit discovered page",
                target=url,
                data_to_extract="Relevant information for the goal",
                success_criteria="Page content extracted",
            )
            # Insert before the last "done" step
            done_idx = next((i for i, s in enumerate(plan.steps) if s.action == ActionType.DONE and s.status == StepStatus.PENDING), None)
            if done_idx is not None:
                plan.steps.insert(done_idx, nav_step)
            else:
                plan.steps.append(nav_step)
            next_id += 1
            self.logger.info(f"Added dynamic step: Visit {url[:60]}...")
