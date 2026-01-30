# Happy Path - Quick Start Guide

Fastest path to run AI Agriculture Advisors locally.

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

1. Select one or more experts from the sidebar
2. Enter a query (example: `What are the benefits of crop rotation?`)
3. Click **Submit Query**

**Success:** You see expert responses with markdown formatting.

## Optional: Roundtable

1. Select at least 2 experts
2. Enter a complex query
3. Click **Round Table**

**Success:** You see a transcript plus a consensus answer.

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
