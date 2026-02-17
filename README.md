# Cribbage

A command-line Cribbage card game built with Python 3. Play against an AI opponent in your terminal.

## Requirements

- Python 3
- `colorama` package
- `python-dotenv` package
- `anthropic` package (optional, for LLM opponents)

## How to Play

```bash
python3 main.py
```

Optionally set a custom target score (default is 121):

```bash
python3 main.py 60
```

Type `q` at any prompt to quit the game.

## Game Modes

At startup you choose between two modes:

- **Play** — play a game against an AI opponent with a terminal UI
- **Simulate** — pit two AI strategies against each other over multiple games. Configure the number of games, target score, and which strategies to use. Results are logged to a SQLite database (`cribbage_log.db`) and a summary is displayed when the simulation completes.

## AI Opponents

Choose from several AI strategies at game start:

- **AI-Random** — picks random valid cards
- **AI-Basic** — simple heuristics (discard lowest, play highest)
- **AI-Opt** — exhaustive evaluation of hand potential
- **AI-LLM** — powered by Anthropic Claude models (requires API key)

### LLM Setup

To enable LLM opponents, set your Anthropic API key in a `.env` file:

```bash
cp .env.example .env
# Edit .env and add your API key
```

Available Claude models are fetched automatically from the API. If the key is missing or invalid, a message is shown and the game continues with the non-LLM strategies.

### LLM Explanations

When selecting an LLM opponent, you'll be asked whether to enable explanations. When enabled, the LLM is prompted to explain its reasoning after each decision. Explanations are logged to `llm_calls.log` (not shown in the UI) and can be reviewed after a game or simulation.

## Running Tests

```bash
python3 -m unittest tests.card_deck_tests -v
python3 -m unittest tests.round_tests -v
python3 -m unittest tests.ai_strategy_tests -v
```
