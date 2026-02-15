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

## Running Tests

```bash
python3 -m unittest tests.card_deck_tests -v
python3 -m unittest tests.round_tests -v
python3 -m unittest tests.ai_strategy_tests -v
```
