import sqlite3
import json
from datetime import datetime
from card_deck.card_deck import Card


def card_to_str(card):
    """Encode a Card as a compact string like 'AH', '10S', 'KC'."""
    return Card.VALUES[card.number - 1] + card.suit


def cards_to_json(cards):
    """Encode a list of Cards as a JSON array of compact strings."""
    return json.dumps([card_to_str(c) for c in cards])


SCHEMA = """
CREATE TABLE IF NOT EXISTS games (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_time TEXT NOT NULL,
    end_time TEXT,
    num_players INTEGER NOT NULL,
    target_score INTEGER NOT NULL,
    completion TEXT NOT NULL DEFAULT 'in_progress'
);

CREATE TABLE IF NOT EXISTS game_players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER NOT NULL REFERENCES games(id),
    player_index INTEGER NOT NULL,
    player_name TEXT NOT NULL,
    player_type TEXT NOT NULL,
    strategy_name TEXT,
    final_score INTEGER,
    is_winner INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS rounds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER NOT NULL REFERENCES games(id),
    round_number INTEGER NOT NULL,
    dealer_index INTEGER NOT NULL,
    turn_up_card TEXT,
    jack_bonus_points INTEGER NOT NULL DEFAULT 0,
    crib_score INTEGER
);

CREATE TABLE IF NOT EXISTS round_hands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    round_id INTEGER NOT NULL REFERENCES rounds(id),
    player_index INTEGER NOT NULL,
    dealt_cards TEXT NOT NULL,
    kept_cards TEXT,
    crib_cards TEXT,
    hand_score INTEGER,
    play_score INTEGER,
    cumulative_score INTEGER
);

CREATE TABLE IF NOT EXISTS plays (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    round_id INTEGER NOT NULL REFERENCES rounds(id),
    player_index INTEGER NOT NULL,
    sequence INTEGER NOT NULL,
    sub_round INTEGER NOT NULL DEFAULT 1,
    card TEXT,
    running_count INTEGER NOT NULL,
    points INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_games_completion ON games(completion);
CREATE INDEX IF NOT EXISTS idx_game_players_strategy ON game_players(strategy_name, is_winner);
CREATE INDEX IF NOT EXISTS idx_rounds_game ON rounds(game_id);
CREATE INDEX IF NOT EXISTS idx_round_hands_round ON round_hands(round_id);
CREATE INDEX IF NOT EXISTS idx_plays_round ON plays(round_id);
"""


def _player_type(player):
    """Return a string describing the player type."""
    cls = type(player).__name__
    type_map = {
        'HumanPlayer': 'human',
        'AI_Player': 'ai',
        'Test_Player': 'test',
    }
    return type_map.get(cls, cls)


class Logger:
    def __init__(self, game, db_path='cribbage_log.db'):
        self.game = game
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.executescript(SCHEMA)

        # Insert game row
        cur = self.conn.execute(
            "INSERT INTO games (start_time, num_players, target_score) VALUES (?, ?, ?)",
            (datetime.now().isoformat(), game.num_players, game.target_score)
        )
        self.game_id = cur.lastrowid

        # Insert game_players rows
        from crib.crib import AI_Player
        for i, p in enumerate(game.players):
            strategy_name = None
            if isinstance(p, AI_Player):
                strategy_name = p.strategy.name if hasattr(p, 'strategy') else None
            self.conn.execute(
                "INSERT INTO game_players (game_id, player_index, player_name, player_type, strategy_name) "
                "VALUES (?, ?, ?, ?, ?)",
                (self.game_id, i, p.name, _player_type(p), strategy_name)
            )
        self.conn.commit()

        self.current_round_id = None
        self._play_sequence = 0
        self._sub_round = 1

    def new_round(self, round_number, dealt_result):
        game = self.game
        cur = self.conn.execute(
            "INSERT INTO rounds (game_id, round_number, dealer_index) VALUES (?, ?, ?)",
            (self.game_id, round_number, game.crib_player)
        )
        self.current_round_id = cur.lastrowid

        # Snapshot each player's dealt hand
        for i, p in enumerate(game.players):
            self.conn.execute(
                "INSERT INTO round_hands (round_id, player_index, dealt_cards) VALUES (?, ?, ?)",
                (self.current_round_id, i, cards_to_json(p.hand.cards))
            )
        self.conn.commit()

        # Reset play tracking for new round
        self._play_sequence = 0
        self._sub_round = 1

    def crib(self, crib_result):
        game = self.game
        round_obj = game.game_round

        for i, p in enumerate(game.players):
            kept_cards = cards_to_json(p.hand.cards)
            # Determine which cards went to crib by diffing dealt vs kept
            cur = self.conn.execute(
                "SELECT dealt_cards FROM round_hands WHERE round_id = ? AND player_index = ?",
                (self.current_round_id, i)
            )
            dealt_json = cur.fetchone()[0]
            dealt_list = json.loads(dealt_json)
            kept_list = [card_to_str(c) for c in p.hand.cards]
            crib_cards = [c for c in dealt_list if c not in kept_list]

            self.conn.execute(
                "UPDATE round_hands SET kept_cards = ?, crib_cards = ? "
                "WHERE round_id = ? AND player_index = ?",
                (kept_cards, json.dumps(crib_cards), self.current_round_id, i)
            )
        self.conn.commit()

    def turn_up(self, turn_up_result):
        round_obj = self.game.game_round
        jack_bonus = 2 if round_obj.turn_up.number == 11 else 0
        self.conn.execute(
            "UPDATE rounds SET turn_up_card = ?, jack_bonus_points = ? WHERE id = ?",
            (card_to_str(round_obj.turn_up), jack_bonus, self.current_round_id)
        )
        self.conn.commit()

    def the_play(self, played_result):
        pass

    def log_play(self, player_index, card, running_count, points):
        """Log a single play (card or go) to the plays table."""
        self._play_sequence += 1
        card_str = card_to_str(card) if card else None
        self.conn.execute(
            "INSERT INTO plays (round_id, player_index, sequence, sub_round, card, running_count, points) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (self.current_round_id, player_index, self._play_sequence,
             self._sub_round, card_str, running_count, points)
        )
        self.conn.commit()

    def new_sub_round(self):
        """Increment sub-round counter when count resets."""
        self._sub_round += 1

    def score_hands(self, score_result):
        game = self.game
        round_obj = game.game_round

        from crib.crib import count_hand
        for i, p in enumerate(game.players):
            hand_score = count_hand(p.played_cards, round_obj.turn_up)
            self.conn.execute(
                "UPDATE round_hands SET hand_score = ?, play_score = ?, cumulative_score = ? "
                "WHERE round_id = ? AND player_index = ?",
                (hand_score, round_obj.score[i], game.score[i],
                 self.current_round_id, i)
            )

        crib_score = count_hand(round_obj.crib, round_obj.turn_up)
        self.conn.execute(
            "UPDATE rounds SET crib_score = ? WHERE id = ?",
            (crib_score, self.current_round_id)
        )
        self.conn.commit()

    def record_winner(self, winner):
        game = self.game
        now = datetime.now().isoformat()
        self.conn.execute(
            "UPDATE games SET end_time = ?, completion = 'completed' WHERE id = ?",
            (now, self.game_id)
        )
        for i, p in enumerate(game.players):
            self.conn.execute(
                "UPDATE game_players SET final_score = ?, is_winner = ? "
                "WHERE game_id = ? AND player_index = ?",
                (game.score[i], 1 if i == winner else 0, self.game_id, i)
            )
        self.conn.commit()

    def record_quit(self):
        game = self.game
        now = datetime.now().isoformat()
        self.conn.execute(
            "UPDATE games SET end_time = ?, completion = 'quit' WHERE id = ?",
            (now, self.game_id)
        )
        for i, p in enumerate(game.players):
            self.conn.execute(
                "UPDATE game_players SET final_score = ? WHERE game_id = ? AND player_index = ?",
                (game.score[i], self.game_id, i)
            )
        self.conn.commit()

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None
