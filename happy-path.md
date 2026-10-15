# Happy Path - Quick Start Guide

Fastest path to try the AI Advisors 2.1.0 candidate locally. Existing installations should use the [upgrade and recovery notes](docs/RELEASE-READINESS.md#upgrade-and-recovery) and keep their current configuration and saved results.

## Prerequisites

- **Python 3.12+**
- **uv** (Astral) package manager
- **OpenRouter API Key**: https://openrouter.ai/keys

## Step 1: Install Dependencies

```bash
uv sync --locked
```

## Step 2: Configure Environment

```bash
test -f .env || cp .env.example .env
```

Edit `.env` and set your API key and an available model ID from your OpenRouter account. The example values below are placeholders:

```env
OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here
OPENROUTER_API_URL=https://openrouter.ai/api/v1/chat/completions
OPENROUTER_MODEL=your_model_id_here
# Optional: choose a different available model for synthesis only.
# OPENROUTER_SYNTHESIS_MODEL=your_synthesis_model_id_here
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

**Success:** You see each advisor's contribution and a useful synthesis. AI Workflow returns a task packet, review checks, a checkpoint, and a measured success criterion. Accessibility & Effort returns a starter you can use, a resume record, dictation recovery, and a small trial. These panels end with one Decision Check; their individual roundtable turns do not repeat it. Agreement between AI personas is not independent evidence.

## Save and recover

Choose **Save Result**, reopen it from Saved Results, and export Markdown or an HTML brief. Reopening and exporting use the stored output without making new model requests. An existing saved answer will not acquire new wording simply because the application was upgraded.

If a call fails, keep the completed answers. Use **Retry failed advisors & synthesis** only for missing contributions, or **Retry synthesis** when all advisor answers succeeded. Wait for any retry countdown; it is a minimum pause, not a recovery promise. Save again after retry to retain a new version alongside the earlier save.

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

### Tests cannot import FastAPI or recognize `pytest.mark.asyncio`

Use `uv run pytest`, which selects the project environment, rather than a global `python -m pytest`. `uv sync --locked` installs the development dependencies. The [release readiness note](docs/RELEASE-READINESS.md) includes the final regression command.

The browser remembers your last panel and selections. Switching panels keeps your question and current results. Save a result to preserve its captured advisor definitions; older results explicitly show that those definitions were not captured. See the [guided five-panel demo](docs/DEMO-WALKTHROUGH.md) for scenarios that surface meaningful tradeoffs, evidence gaps, and recovery paths.
