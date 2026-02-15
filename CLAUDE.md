# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

**Run the game:**
```bash
python3 main.py
```

**Run tests:**
```bash
python3 -m unittest tests.card_deck_tests tests.round_tests tests.ai_strategy_tests -v
```

## Architecture

The game follows a layered architecture with four modules:

- **card_deck/** - Card, Deck, and Hand classes. Hand extends Deck to support receive/play operations.
- **crib/** - Core game logic. Contains Player hierarchy (HumanPlayer, AI_Player, Test_Player), Game (manages rounds until 121 points), and Round (deal → crib → turn-up → play → score). Scoring implements standard Cribbage rules (fifteens, pairs, runs, flushes, his nob). The `count_hand()` function handles all hand scoring.
- **interface/** - Terminal display using ANSI escape codes. CribInterface renders player hands, scores, and the play phase in a columnar table format.
- **logger/** - Stub module, not yet implemented.

**Control flow:** `main.py` → `Game.play()` loops rounds → each `Round` orchestrates deal/crib/play/score phases → `HumanPlayer` gets input via `CribInterface`, `AI_Player` analyzes card combinations to choose plays.

## Key Design Notes

- Game target score is 121 points
- Round play phase: players alternate cards until count reaches 31 or all pass ("Go")
- AI strategy evaluates all card subsets to maximize hand potential when discarding to crib
- Tests use `Test_Player` with deterministic card selections
