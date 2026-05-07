"""
Configuration module for the Multi-Agent Browser System.
Loads environment variables and provides centralized settings.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Central configuration for the multi-agent system."""

    # LLM Settings (NVIDIA NIM API)
    NVIDIA_API_KEY: str = os.getenv("NVIDIA_API_KEY", "")
    NVIDIA_MODEL: str = os.getenv("NVIDIA_MODEL", "google/gemma-4-31b-it")
    NVIDIA_BASE_URL: str = "https://integrate.api.nvidia.com/v1"

    # Browser Settings
    BROWSER_HEADLESS: bool = os.getenv("BROWSER_HEADLESS", "false").lower() == "true"
    BROWSER_TIMEOUT: int = int(os.getenv("BROWSER_TIMEOUT", "30000"))

    # Agent Settings
    MAX_STEPS: int = 20  # Max steps before forcing completion
    MAX_RETRIES: int = 3  # Max retries per step
    PAGE_CONTENT_MAX_CHARS: int = 15000  # Max chars to send to LLM from a page

    @classmethod
    def validate(cls) -> bool:
        """Validate that required configuration is set."""
        if not cls.NVIDIA_API_KEY:
            return False
        return True
