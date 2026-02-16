import unittest
import sqlite3
import json
from card_deck.card_deck import Card, Hand
from crib.crib import Test_Player, Game, Round
from interface.interface import Interface
from logger.logger import Logger, card_to_str, cards_to_json, create_simulation, complete_simulation


class CardEncodingTests(unittest.TestCase):

    def test_card_to_str(self):
        self.assertEqual(card_to_str(Card('H', 1)), 'AH')
        self.assertEqual(card_to_str(Card('S', 10)), '10S')
        self.assertEqual(card_to_str(Card('C', 13)), 'KC')
        self.assertEqual(card_to_str(Card('D', 11)), 'JD')
        self.assertEqual(card_to_str(Card('H', 12)), 'QH')
        self.assertEqual(card_to_str(Card('S', 2)), '2S')

    def test_cards_to_json(self):
        cards = [Card('H', 1), Card('S', 10)]
        result = json.loads(cards_to_json(cards))
        self.assertEqual(result, ['AH', '10S'])


def _setup_round_with_known_hands(db_path=':memory:'):
    """Set up a game with known hands (same as round_tests.test_no_gos).

    Play sequence: 2H, 5H, 3S, 7S, 6C, AH, AC, AD
    No gos needed. p1 score=2, p2 score=7.
    """
    # 2 crib card picks + 4 play picks = 6 entries each
    # Crib: pick index 0 twice (removes first two cards from 6-card hand)
    # After crib, hands are the 4 cards we want to play
    # Play: always index 0
    p1_hand = [Card('H', 8), Card('D', 9),  # will go to crib
               Card('H', 2), Card('S', 3), Card('C', 6), Card('D', 1)]
    p2_hand = [Card('C', 8), Card('S', 9),  # will go to crib
               Card('H', 5), Card('S', 7), Card('H', 1), Card('C', 1)]

    p1 = Test_Player([0, 0, 0, 0, 0, 0])
    p2 = Test_Player([0, 0, 0, 0, 0, 0])

    interf = Interface()
    game = Game(2, [p1, p2], interf, crib_player=0, target_score=500)
    game.logger.close()
    game.logger = Logger(game, db_path=db_path)
    lg = game.logger
    conn = lg.conn

    # Create round and assign logger
    game.round_number = 1
    game.game_round = Round(2, [p1, p2], 0, interf)
    game.game_round.logger = lg

    # Manually assign hands instead of dealing
    p1.hand = Hand()
    for c in p1_hand:
        p1.hand.receive_card(c)
    p2.hand = Hand()
    for c in p2_hand:
        p2.hand.receive_card(c)

    return game, lg, conn, p1, p2


class LoggerTests(unittest.TestCase):

    def test_full_round_logging(self):
        """Play a single round with known hands and verify all 5 tables."""
        game, lg, conn, p1, p2 = _setup_round_with_known_hands()

        # Log the round phases (skip deal_cards since we set hands manually)
        lg.new_round(1, 'ok')
        lg.crib(game.game_round.establish_crib())
        lg.turn_up(game.game_round.establish_turn_up())
        lg.the_play(game.game_round.play())
        game.score = [game.score[i] + game.game_round.score[i] for i in range(2)]
        lg.score_hands(game.game_round.score_hands())
        lg.record_winner(0)

        # Verify games table
        row = conn.execute("SELECT * FROM games").fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row[3], 2)  # num_players
        self.assertEqual(row[4], 500)  # target_score
        self.assertEqual(row[5], 'completed')  # completion

        # Verify game_players
        conn.row_factory = sqlite3.Row
        players = conn.execute("SELECT * FROM game_players ORDER BY player_index").fetchall()
        conn.row_factory = None
        self.assertEqual(len(players), 2)
        self.assertEqual(players[0]['player_name'], 'Test')
        self.assertEqual(players[0]['player_type'], 'test')

        # Verify rounds
        rounds = conn.execute("SELECT * FROM rounds").fetchall()
        self.assertEqual(len(rounds), 1)
        self.assertEqual(rounds[0][2], 1)  # round_number
        self.assertIsNotNone(rounds[0][4])  # turn_up_card

        # Verify round_hands
        hands = conn.execute("SELECT * FROM round_hands ORDER BY player_index").fetchall()
        self.assertEqual(len(hands), 2)
        for h in hands:
            dealt = json.loads(h[3])  # dealt_cards
            self.assertEqual(len(dealt), 6)
            kept = json.loads(h[4])  # kept_cards
            self.assertEqual(len(kept), 4)
            crib_cards = json.loads(h[5])  # crib_cards
            self.assertEqual(len(crib_cards), 2)

        # Verify plays table has entries
        plays = conn.execute("SELECT * FROM plays ORDER BY sequence").fetchall()
        self.assertGreater(len(plays), 0)

        lg.close()

    def test_play_logging_detail(self):
        """Verify individual plays are logged with correct sequence."""
        game, lg, conn, p1, p2 = _setup_round_with_known_hands()

        lg.new_round(1, 'ok')
        lg.crib(game.game_round.establish_crib())
        lg.turn_up(game.game_round.establish_turn_up())
        lg.the_play(game.game_round.play())

        plays = conn.execute(
            "SELECT sequence, sub_round, card, running_count, points "
            "FROM plays ORDER BY sequence"
        ).fetchall()
        self.assertGreater(len(plays), 0)

        # Sequences should be consecutive starting at 1
        sequences = [p[0] for p in plays]
        self.assertEqual(sequences, list(range(1, len(plays) + 1)))

        # Sub-rounds should start at 1 and only increase
        sub_rounds = [p[1] for p in plays]
        self.assertGreaterEqual(min(sub_rounds), 1)
        for i in range(1, len(sub_rounds)):
            self.assertGreaterEqual(sub_rounds[i], sub_rounds[i - 1])

        # Verify card plays have card strings, gos have None
        for p in plays:
            if p[2] is not None:
                # Card string should be 2-3 chars (e.g., 'AH', '10S')
                self.assertIn(len(p[2]), [2, 3])

        lg.close()

    def test_quit_logging(self):
        """Verify record_quit sets completion to 'quit'."""
        p1 = Test_Player([])
        p2 = Test_Player([])
        interf = Interface()
        game = Game(2, [p1, p2], interf, crib_player=0, target_score=500)
        game.logger.close()
        game.logger = Logger(game, db_path=':memory:')
        lg = game.logger
        conn = lg.conn

        game.score = [42, 37]
        lg.record_quit()

        row = conn.execute("SELECT completion FROM games").fetchone()
        self.assertEqual(row[0], 'quit')

        players = conn.execute(
            "SELECT final_score FROM game_players ORDER BY player_index"
        ).fetchall()
        self.assertEqual(players[0][0], 42)
        self.assertEqual(players[1][0], 37)

        lg.close()

    def test_schema_indexes(self):
        """Verify all expected indexes exist."""
        p1 = Test_Player([])
        p2 = Test_Player([])
        interf = Interface()
        game = Game(2, [p1, p2], interf, crib_player=0)
        game.logger.close()
        game.logger = Logger(game, db_path=':memory:')
        conn = game.logger.conn

        indexes = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'"
        ).fetchall()
        index_names = {row[0] for row in indexes}

        expected = {
            'idx_games_completion',
            'idx_game_players_strategy',
            'idx_rounds_game',
            'idx_round_hands_round',
            'idx_plays_round',
            'idx_games_simulation',
        }
        self.assertEqual(expected, index_names)
        game.logger.close()

    def test_crib_cards_recorded(self):
        """Verify crib cards are correctly identified as diff of dealt vs kept."""
        game, lg, conn, p1, p2 = _setup_round_with_known_hands()

        lg.new_round(1, 'ok')
        lg.crib(game.game_round.establish_crib())

        hands = conn.execute(
            "SELECT dealt_cards, kept_cards, crib_cards FROM round_hands ORDER BY player_index"
        ).fetchall()

        # p1 discarded 8H, 9D (indices 0,0); kept 2H, 3S, 6C, AD
        p1_dealt = json.loads(hands[0][0])
        p1_kept = json.loads(hands[0][1])
        p1_crib = json.loads(hands[0][2])
        self.assertEqual(len(p1_dealt), 6)
        self.assertEqual(len(p1_kept), 4)
        self.assertEqual(len(p1_crib), 2)
        self.assertEqual(set(p1_crib), {'8H', '9D'})

        # p2 discarded 8C, 9S; kept 5H, 7S, AH, AC
        p2_crib = json.loads(hands[1][2])
        self.assertEqual(set(p2_crib), {'8C', '9S'})

        lg.close()

    def test_in_progress_default(self):
        """Verify game starts as 'in_progress' if not completed or quit."""
        p1 = Test_Player([])
        p2 = Test_Player([])
        interf = Interface()
        game = Game(2, [p1, p2], interf, crib_player=0)
        game.logger.close()
        game.logger = Logger(game, db_path=':memory:')
        conn = game.logger.conn

        row = conn.execute("SELECT completion FROM games").fetchone()
        self.assertEqual(row[0], 'in_progress')

        game.logger.close()


class SimulationTests(unittest.TestCase):

    def test_create_simulation(self):
        """Verify create_simulation inserts a row with correct fields."""
        conn, sim_id = create_simulation(
            ':memory:', 'Test Sim', 'A test simulation',
            10, 'Random', 'Basic', 121
        )
        row = conn.execute("SELECT * FROM simulations WHERE id = ?", (sim_id,)).fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row[1], 'Test Sim')       # name
        self.assertEqual(row[2], 'A test simulation')  # description
        self.assertEqual(row[3], 10)                # num_games
        self.assertEqual(row[4], 'Random')          # player1_strategy
        self.assertEqual(row[5], 'Basic')           # player2_strategy
        self.assertEqual(row[6], 121)               # target_score
        self.assertIsNotNone(row[7])                # start_time
        self.assertIsNone(row[8])                   # end_time (not yet completed)
        conn.close()

    def test_game_linked_to_simulation(self):
        """Verify games created with simulation_id link correctly."""
        conn, sim_id = create_simulation(
            ':memory:', 'Link Test', None, 5, 'Opt', 'Opt', 121
        )
        db_path = ':memory:'
        # We need to use the same connection, so use file-based temp db
        import tempfile, os
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        conn.close()

        conn2, sim_id = create_simulation(
            db_path, 'Link Test', None, 5, 'Opt', 'Opt', 121
        )
        conn2.close()

        p1 = Test_Player([])
        p2 = Test_Player([])
        interf = Interface()
        game = Game(2, [p1, p2], interf, crib_player=0, target_score=500)
        game.logger.close()
        game.logger = Logger(game, db_path=db_path, simulation_id=sim_id)
        lg = game.logger

        row = lg.conn.execute(
            "SELECT simulation_id FROM games WHERE id = ?", (lg.game_id,)
        ).fetchone()
        self.assertEqual(row[0], sim_id)

        lg.close()
        os.unlink(db_path)

    def test_complete_simulation(self):
        """Verify complete_simulation sets end_time."""
        import tempfile, os
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        conn, sim_id = create_simulation(
            db_path, 'Complete Test', None, 3, 'R', 'B', 121
        )
        conn.close()

        import sqlite3
        conn2 = sqlite3.connect(db_path)
        complete_simulation(conn2, sim_id)

        conn3 = sqlite3.connect(db_path)
        row = conn3.execute(
            "SELECT end_time FROM simulations WHERE id = ?", (sim_id,)
        ).fetchone()
        self.assertIsNotNone(row[0])
        conn3.close()
        os.unlink(db_path)


if __name__ == '__main__':
    unittest.main()
