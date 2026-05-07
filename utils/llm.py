"""
LLM Client wrapper for generic OpenAI-compatible APIs.
Uses a configured model via the specified endpoint.
"""

import json
import httpx
from config import Config


class LLMClient:
    """Wrapper around LLM API for agent reasoning."""

    def __init__(self):
        if not Config.LLM_API_KEY:
            raise ValueError(
                "LLM_API_KEY not set! Copy .env.example to .env and add your key.\n"
                "Get a key at your preferred provider's website"
            )
        self.api_key = Config.LLM_API_KEY
        self.model = Config.LLM_MODEL
        self.base_url = Config.LLM_BASE_URL
        self.client = httpx.AsyncClient(timeout=180.0)

    async def generate(self, prompt: str, system_instruction: str = "") -> str:
        """Generate a response from the LLM."""
        try:
            messages = []
            if system_instruction:
                messages.append({"role": "system", "content": system_instruction})
            messages.append({"role": "user", "content": prompt})

            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": 0.3,
                    "max_tokens": 4096,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as e:
            return f"LLM Error (HTTP {e.response.status_code}): {e.response.text[:300]}"
        except Exception as e:
            return f"LLM Error: {type(e).__name__} - {str(e)}"

    async def generate_json(self, prompt: str, system_instruction: str = "") -> dict:
        """Generate a JSON response from the LLM."""
        full_prompt = (
            f"{prompt}\n\n"
            "IMPORTANT: Respond ONLY with valid JSON. No markdown code fences, "
            "no explanations, no extra text. Just pure JSON."
        )
        response = await self.generate(full_prompt, system_instruction)

        # Clean up response - remove markdown code fences if present
        cleaned = response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            # Try to find JSON object in the response
            start = cleaned.find("{")
            end = cleaned.rfind("}") + 1
            if start != -1 and end > start:
                try:
                    return json.loads(cleaned[start:end])
                except json.JSONDecodeError:
                    pass

            # Try array
            start = cleaned.find("[")
            end = cleaned.rfind("]") + 1
            if start != -1 and end > start:
                try:
                    return {"items": json.loads(cleaned[start:end])}
                except json.JSONDecodeError:
                    pass

            return {"error": "Failed to parse JSON", "raw": response}

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
