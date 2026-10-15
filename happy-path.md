# Happy Path - Quick Start Guide

Fastest path to run AI Advisors locally.

## Prerequisites

- **Python 3.12+**
- **uv** (Astral) package manager
- **OpenRouter API Key**: https://openrouter.ai/keys

## Step 1: Install Dependencies

```bash
uv sync
```

## Step 2: Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and set your API key:

```env
OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here
OPENROUTER_MODEL=mistralai/mistral-7b-instruct:free
PORT=8123
CHROMADB_PATH=.chromadb
```

## Step 3: Start the App

**Option A: start script**
```bash
./start.sh
```

**Option B: direct**
```bash
uv run uvicorn main:app --reload --port 8123
```

Open: http://localhost:8123

## Step 4: Verify the UI

1. Choose a panel in the Advisor Panel selector.
2. Choose one of its example questions, or follow [the demo walkthrough](docs/DEMO-WALKTHROUGH.md) for a concrete scenario.
3. Click **Submit Query** for one perspective, or select two advisors and use a one-round **Round Table** to compare perspectives.

**Success:** The responses distinguish recommendations from assumptions and identify the missing information that could change the decision. The advisors reason from the supplied question; they do not independently verify it.

## Optional: Roundtable

1. Select two advisors with different roles.
2. Set **Roundtable Rounds** to **1** for a compact first comparison.
3. Enter a concrete question with the decision, constraints, and evidence you already have.
4. Click **Round Table**, then save the result if you want to resume later.

**Success:** You see each advisor's contribution and a synthesis that distinguishes shared reasoning, disagreement, and unknowns. Agreement between AI personas is not independent evidence.

## Quick Troubleshooting

### Error: `OPENROUTER_API_KEY environment variable is required`

- Ensure `.env` exists and has a valid key
- Restart the server

### Error: `Invalid CSRF token`

- Refresh the page and try again
- Ensure cookies are enabled for `localhost`

### Port in use

Set a different port in `.env`:

```env
PORT=8124
```

The browser remembers your last panel and selections. Switching panels keeps your question and current results. Save a result to preserve its captured advisor definitions; older results explicitly show that those definitions were not captured. See the [guided five-panel demo](docs/DEMO-WALKTHROUGH.md) for scenarios that surface meaningful tradeoffs, evidence gaps, and recovery paths.
