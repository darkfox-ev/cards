# Cribbage

A command-line Cribbage card game built with Python 3. Play against an AI opponent in your terminal.

## Requirements

- Python 3
- `colorama` package

## How to Play

```bash
python3 main.py
```

Optionally set a custom target score (default is 121):

```bash
python3 main.py 60
```

Type `q` at any prompt to quit the game.

## Running Tests

```bash
python3 -m unittest tests.card_deck_tests -v
python3 -m unittest tests.round_tests -v
```
