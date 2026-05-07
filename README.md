# 🤖 Multi-Agent Browser System

An AI-powered multi-agent system that autonomously browses the web, researches topics, and compiles structured reports — powered by your **preferred LLM** and **Playwright**.

## Architecture

```
User Prompt → Planner Agent → Browser Controller → Webpage Reader → Action Executor → Verifier → Next Step Planning → Final Report
```

### Agents

| Agent | Role |
|-------|------|
| 🧠 **Orchestrator** | Coordinates the entire pipeline |
| 📋 **Planner** | Decomposes prompts into browser action steps |
| 🌐 **Browser Controller** | Manages tabs, navigation, clicks |
| 📖 **Webpage Reader** | Extracts & structures page content via LLM |
| ⚡ **Action Executor** | Processes results and stores data |
| ✅ **Verifier** | Validates each step's success |

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   python -m playwright install chromium
   ```

2. **Configure API key:**
   ```bash
   cp .env.example .env
   # Edit .env and add your LLM API key
   # Get a free key at your provider's website
   ```

3. **Run:**
   ```bash
   # Interactive mode
   python main.py

   # Direct mode
   python main.py "Research top AI browser agent startups and summarize funding, features, pricing"
   ```

## Example Prompts

- `"Research top AI browser agent startups and summarize funding, features, pricing, competitors"`
- `"Find the best RTX 4060 laptop under ₹90,000 with good thermals and battery life. Compare at least 5 options."`
- `"What are the latest trends in AI-powered code editors? Compare Cursor, Windsurf, and GitHub Copilot."`

## How It Works

1. **Planning** — The Planner Agent uses an LLM to decompose your query into 8-15 browser actions
2. **Execution** — Each step runs through: Browser Action → Content Extraction → LLM Analysis → Verification
3. **Adaptation** — The system dynamically adjusts the plan based on what it discovers
4. **Report** — All collected data is compiled into a structured markdown report

## Project Structure

```
├── main.py                    # Entry point (interactive + direct mode)
├── config.py                  # Configuration & env vars
├── agents/
│   ├── orchestrator.py        # Master coordinator
│   ├── planner.py             # Task decomposition
│   ├── browser_controller.py  # Browser action execution
│   ├── webpage_reader.py      # Content extraction
│   ├── action_executor.py     # Result processing
│   └── verifier.py            # Step verification
├── browser/
│   └── manager.py             # Playwright browser lifecycle
├── models/
│   └── schemas.py             # Data models (Plan, Step, Result)
└── utils/
    ├── llm.py                 # LLM API client
    └── logger.py              # Rich terminal logging
```
