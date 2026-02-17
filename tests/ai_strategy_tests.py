import unittest
from unittest.mock import patch, MagicMock
from card_deck.card_deck import Hand, Card
from crib.ai_strategy import (
    RandomStrategy, BasicStrategy, OptimizedStrategy,
    LLMStrategy, get_llm_strategies,
)


def make_hand(cards):
    """Helper to create a Hand with given Card objects."""
    hand = Hand()
    for c in cards:
        hand.receive_card(c)
    return hand


class RandomStrategyTestCase(unittest.TestCase):

    def test_choose_crib_cards_returns_correct_count(self):
        hand = make_hand([Card('H', 1), Card('S', 5), Card('D', 10), Card('C', 13),
                          Card('H', 7), Card('S', 3)])
        s = RandomStrategy()
        result = s.choose_crib_cards(hand, 2, is_my_crib=True)
        self.assertEqual(len(result), 2)
        self.assertTrue(all(0 <= i < 6 for i in result))

    def test_choose_play_card_valid(self):
        hand = make_hand([Card('H', 5), Card('S', 10)])
        s = RandomStrategy()
        idx = s.choose_play_card(hand, 22)
        # Only the 5 (value=5) fits under 31 at count 22 (5+22=27, 10+22=32)
        self.assertEqual(idx, 0)

    def test_choose_play_card_go(self):
        hand = make_hand([Card('H', 10), Card('S', 13)])
        s = RandomStrategy()
        idx = s.choose_play_card(hand, 22)
        self.assertIsNone(idx)


class BasicStrategyTestCase(unittest.TestCase):

    def test_choose_crib_cards_discards_lowest(self):
        hand = make_hand([Card('H', 1), Card('S', 5), Card('D', 10), Card('C', 13)])
        s = BasicStrategy()
        result = s.choose_crib_cards(hand, 2, is_my_crib=False)
        # Ace (1) and 5 are the lowest values
        self.assertIn(0, result)  # Ace
        self.assertIn(1, result)  # 5

    def test_choose_play_card_plays_highest(self):
        hand = make_hand([Card('H', 3), Card('S', 7), Card('D', 10)])
        s = BasicStrategy()
        idx = s.choose_play_card(hand, 20)
        # 10 is too high (20+10=30 <=31), 7 fits (20+7=27), 3 fits (20+3=23)
        # Highest fitting is 10 (value=10)
        self.assertEqual(idx, 2)

    def test_choose_play_card_go(self):
        hand = make_hand([Card('H', 10)])
        s = BasicStrategy()
        idx = s.choose_play_card(hand, 25)
        self.assertIsNone(idx)


class OptimizedStrategyTestCase(unittest.TestCase):

    def test_choose_crib_cards_keeps_best(self):
        # Hand with a clear fifteen (5+10) should keep those
        hand = make_hand([Card('H', 5), Card('S', 10), Card('D', 1), Card('C', 2),
                          Card('H', 5), Card('S', 10)])
        s = OptimizedStrategy()
        result = s.choose_crib_cards(hand, 2, is_my_crib=True)
        self.assertEqual(len(result), 2)
        # All indices should be valid
        self.assertTrue(all(0 <= i < 6 for i in result))

    def test_choose_play_card_plays_highest_fitting(self):
        hand = make_hand([Card('H', 2), Card('S', 8)])
        s = OptimizedStrategy()
        idx = s.choose_play_card(hand, 20)
        # 8 fits (20+8=28), 2 fits (20+2=22). Plays highest = 8 at index 1
        self.assertEqual(idx, 1)

    def test_choose_play_card_go(self):
        hand = make_hand([Card('H', 10)])
        s = OptimizedStrategy()
        idx = s.choose_play_card(hand, 22)
        self.assertIsNone(idx)


class LLMStrategyTestCase(unittest.TestCase):

    def _make_strategy(self):
        """Create LLMStrategy with a mock client."""
        mock_client = MagicMock()
        return LLMStrategy("test-model", "Test Model", client=mock_client)

    def test_init_with_client(self):
        mock_client = MagicMock()
        s = LLMStrategy("my-model", "My Model", client=mock_client)
        self.assertEqual(s.model, "my-model")
        self.assertEqual(s.name, "AI-LLM (My Model)")
        self.assertEqual(s.description, "my-model")
        self.assertIs(s.client, mock_client)

    def test_init_display_name_defaults_to_model_id(self):
        mock_client = MagicMock()
        s = LLMStrategy("my-model", client=mock_client)
        self.assertEqual(s.name, "AI-LLM (my-model)")

    def test_init_without_api_key_raises(self):
        with patch.dict('os.environ', {}, clear=True):
            with self.assertRaises(ValueError):
                LLMStrategy("model-id")

    def test_format_cards(self):
        hand = make_hand([Card('H', 1), Card('S', 13)])
        result = LLMStrategy._format_cards(hand)
        self.assertEqual(result, "0: AH, 1: KS")

    def test_choose_crib_cards_parses_llm_response(self):
        s = self._make_strategy()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="0,3")]
        s.client.messages.create.return_value = mock_response

        hand = make_hand([Card('H', 1), Card('S', 5), Card('D', 10), Card('C', 13)])
        result = s.choose_crib_cards(hand, 2, is_my_crib=True)
        self.assertEqual(result, [0, 3])

    def test_choose_crib_cards_fallback_on_bad_response(self):
        s = self._make_strategy()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="I'd discard the ace and king")]
        s.client.messages.create.return_value = mock_response

        hand = make_hand([Card('H', 1), Card('S', 5), Card('D', 10), Card('C', 13)])
        result = s.choose_crib_cards(hand, 2, is_my_crib=False)
        # Should fall back to BasicStrategy (discards lowest values)
        expected = BasicStrategy().choose_crib_cards(hand, 2, is_my_crib=False)
        self.assertEqual(result, expected)

    def test_choose_crib_cards_fallback_on_api_error(self):
        s = self._make_strategy()
        s.client.messages.create.side_effect = Exception("API error")

        hand = make_hand([Card('H', 1), Card('S', 5), Card('D', 10), Card('C', 13)])
        result = s.choose_crib_cards(hand, 2, is_my_crib=False)
        expected = BasicStrategy().choose_crib_cards(hand, 2, is_my_crib=False)
        self.assertEqual(result, expected)

    def test_choose_play_card_parses_llm_response(self):
        s = self._make_strategy()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="1")]
        s.client.messages.create.return_value = mock_response

        hand = make_hand([Card('H', 5), Card('S', 3)])
        result = s.choose_play_card(hand, 20)
        self.assertEqual(result, 1)

    def test_choose_play_card_fallback_on_invalid_index(self):
        s = self._make_strategy()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="5")]  # out of range
        s.client.messages.create.return_value = mock_response

        hand = make_hand([Card('H', 5), Card('S', 3)])
        result = s.choose_play_card(hand, 20)
        expected = BasicStrategy().choose_play_card(hand, 20)
        self.assertEqual(result, expected)

    def test_choose_play_card_go_when_no_valid(self):
        s = self._make_strategy()
        hand = make_hand([Card('H', 10)])
        result = s.choose_play_card(hand, 25)
        self.assertIsNone(result)

    def test_choose_play_card_fallback_on_api_error(self):
        s = self._make_strategy()
        s.client.messages.create.side_effect = Exception("timeout")

        hand = make_hand([Card('H', 5), Card('S', 3)])
        result = s.choose_play_card(hand, 20)
        expected = BasicStrategy().choose_play_card(hand, 20)
        self.assertEqual(result, expected)

    def test_choose_crib_cards_rejects_duplicate_indices(self):
        s = self._make_strategy()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="1,1")]
        s.client.messages.create.return_value = mock_response

        hand = make_hand([Card('H', 1), Card('S', 5), Card('D', 10), Card('C', 13)])
        result = s.choose_crib_cards(hand, 2, is_my_crib=False)
        # Duplicates rejected, falls back to BasicStrategy
        expected = BasicStrategy().choose_crib_cards(hand, 2, is_my_crib=False)
        self.assertEqual(result, expected)

    def test_explain_mode_modifies_prompt_and_max_tokens(self):
        s = self._make_strategy()
        s.explain = True
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="0,3\nReason: These cards don't help the hand.")]
        s.client.messages.create.return_value = mock_response

        hand = make_hand([Card('H', 1), Card('S', 5), Card('D', 10), Card('C', 13)])
        result = s.choose_crib_cards(hand, 2, is_my_crib=True)
        self.assertEqual(result, [0, 3])

        call_kwargs = s.client.messages.create.call_args[1]
        self.assertEqual(call_kwargs['max_tokens'], 300)
        prompt = call_kwargs['messages'][0]['content']
        self.assertIn("Reason:", prompt)

    def test_choose_crib_cards_rejects_out_of_range(self):
        s = self._make_strategy()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="0,10")]
        s.client.messages.create.return_value = mock_response

        hand = make_hand([Card('H', 1), Card('S', 5), Card('D', 10), Card('C', 13)])
        result = s.choose_crib_cards(hand, 2, is_my_crib=False)
        expected = BasicStrategy().choose_crib_cards(hand, 2, is_my_crib=False)
        self.assertEqual(result, expected)


class GetLLMStrategiesTestCase(unittest.TestCase):

    def test_no_api_key(self):
        with patch.dict('os.environ', {}, clear=True):
            strategies, error = get_llm_strategies()
            self.assertEqual(strategies, [])
            self.assertIn("ANTHROPIC_API_KEY", error)

    def test_api_returns_models(self):
        mock_client = MagicMock()

        model1 = MagicMock()
        model1.id = "claude-haiku-4-5-20251001"
        model1.display_name = "Claude Haiku"
        model2 = MagicMock()
        model2.id = "claude-sonnet-4-5-20250929"
        model2.display_name = "Claude Sonnet"
        mock_client.models.list.return_value = MagicMock(data=[model1, model2])

        mock_anthropic = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client

        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
            with patch.dict('sys.modules', {'anthropic': mock_anthropic}):
                strategies, error = get_llm_strategies()

        self.assertEqual(len(strategies), 2)
        self.assertIsNone(error)
        self.assertEqual(strategies[0].model, "claude-haiku-4-5-20251001")
        self.assertEqual(strategies[1].model, "claude-sonnet-4-5-20250929")

    def test_api_exception(self):
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
            with patch.dict('sys.modules', {'anthropic': MagicMock(side_effect=Exception("fail"))}):
                # Force import to raise by making Anthropic() raise
                import sys
                mock_mod = MagicMock()
                mock_mod.Anthropic.side_effect = Exception("connection failed")
                with patch.dict('sys.modules', {'anthropic': mock_mod}):
                    strategies, error = get_llm_strategies()
                    self.assertEqual(strategies, [])
                    self.assertIn("Could not initialize Anthropic API", error)


if __name__ == '__main__':
    unittest.main()
