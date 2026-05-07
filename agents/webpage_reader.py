"""
Webpage Reader Agent — Extracts and structures content from web pages.
Uses LLM to understand and summarize page content relevant to the task.
"""

from utils.llm import LLMClient
from utils.logger import AgentLogger
from models.schemas import Step, StepResult

READER_SYSTEM_PROMPT = """You are a Webpage Reader Agent. Your job is to extract 
relevant information from web page content based on what the user is looking for.

Rules:
1. Focus ONLY on information relevant to the extraction goal
2. Structure the data clearly with labels and values
3. If the page doesn't contain relevant information, say so
4. Be concise but thorough — don't miss important details
5. Extract numbers, prices, names, URLs, and facts accurately
6. If the user asks for specific links (e.g. buying links, company websites, LinkedIn profiles), you MUST extract the full URLs and include them in the result.
7. If you find links to more detailed pages, note them"""


class WebpageReaderAgent:
    """Extracts and structures relevant content from web pages using LLM."""

    def __init__(self, llm: LLMClient):
        self.llm = llm
        self.logger = AgentLogger("reader")

    async def extract(self, step: Step, page_content: str, page_title: str, page_url: str) -> str:
        """Extract relevant data from page content based on step instructions."""
        if not page_content or page_content.strip() == "":
            self.logger.warning("No page content to extract from")
            return "No content available on this page."

        self.logger.info(f"Extracting: {step.data_to_extract}")

        prompt = f"""Extract the following information from this webpage:

EXTRACTION GOAL: {step.data_to_extract}
STEP DESCRIPTION: {step.description}

PAGE TITLE: {page_title}
PAGE URL: {page_url}

PAGE CONTENT:
{page_content[:12000]}

---

Extract the relevant information in a clear, structured format.
If there are links to more detailed pages that should be visited, include them as URLs.
If the page doesn't contain the needed information, explain what's missing."""

        result = await self.llm.generate(prompt, READER_SYSTEM_PROMPT)
        
        if result and not result.startswith("LLM Error"):
            self.logger.success(f"Extracted data ({len(result)} chars)")
            self.logger.data(f"Extracted from: {page_title[:50]}", result)
        else:
            self.logger.error(f"Extraction failed: {result}")

        return result

    async def summarize_for_navigation(self, page_content: str, goal: str) -> list[dict]:
        """Find relevant links on a page that should be visited next."""
        prompt = f"""From this page content, identify the most relevant links to visit for this goal:

GOAL: {goal}

PAGE CONTENT (with links):
{page_content[:8000]}

Return a JSON array of the top 3-5 most relevant links:
[
    {{"url": "https://...", "reason": "Why this link is relevant"}}
]

Only include links that would provide useful information for the goal."""

        result = await self.llm.generate_json(prompt, READER_SYSTEM_PROMPT)

        if isinstance(result, dict) and "items" in result:
            return result["items"]
        elif isinstance(result, dict) and "error" not in result:
            return [result]
        return []
