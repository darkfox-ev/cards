# AI Strategy module - defines different AI decision-making strategies

import random
import copy
from itertools import combinations
from card_deck import card_deck


class AIStrategy:
    """Base class for AI decision-making strategies."""
    name = "Base"
    description = "Base strategy"

    def choose_crib_cards(self, hand, num_crib_cards):
        """Return list of card indices to discard to crib."""
        raise NotImplementedError

    def choose_play_card(self, hand, current_count):
        """Return index of card to play, or None for Go."""
        raise NotImplementedError


class RandomStrategy(AIStrategy):
    """Picks random valid cards for both decisions."""
    name = "AI-Random"
    description = "Random card selection"

    def choose_crib_cards(self, hand, num_crib_cards):
        indices = list(range(hand.num_cards))
        return random.sample(indices, num_crib_cards)

    def choose_play_card(self, hand, current_count):
        valid = [i for i in range(hand.num_cards)
                 if current_count + hand.cards[i].value <= 31]
        if valid:
            return random.choice(valid)
        return None


class BasicStrategy(AIStrategy):
    """Simple heuristics: discard lowest-value cards, play highest fitting card."""
    name = "AI-Basic"
    description = "Simple heuristic strategy"

    def choose_crib_cards(self, hand, num_crib_cards):
        # Discard the lowest-value cards
        indexed = sorted(range(hand.num_cards), key=lambda i: hand.cards[i].value)
        return indexed[:num_crib_cards]

    def choose_play_card(self, hand, current_count):
        # Play highest card that fits under 31
        best_idx = None
        best_val = -1
        for i in range(hand.num_cards):
            if current_count + hand.cards[i].value <= 31:
                if hand.cards[i].value > best_val:
                    best_val = hand.cards[i].value
                    best_idx = i
        return best_idx


class OptimizedStrategy(AIStrategy):
    """Exhaustive evaluation of hand potential for crib discards,
    plays highest fitting card during play phase."""
    name = "AI-Opt"
    description = "Optimized exhaustive evaluation strategy"

    def choose_crib_cards(self, hand, num_crib_cards):
        from crib.crib import count_hand

        # Create temp deck with all cards not in hand
        temp_deck = card_deck.Deck(52).remove_cards(hand.cards)

        best_combo = None
        best_points = -1

        # Find combo that has the highest potential score
        for combo in combinations(hand.cards, hand.num_cards - num_crib_cards):
            points = 0
            for card in temp_deck.cards:
                points += count_hand(combo, card)
            if points > best_points:
                best_combo = copy.deepcopy(combo)
                best_points = points

        # Return indices of cards NOT in best_combo (the ones to discard)
        best_numbers = [(c.suit, c.number) for c in best_combo]
        return [i for i in range(hand.num_cards)
                if (hand.cards[i].suit, hand.cards[i].number) not in best_numbers]

    def choose_play_card(self, hand, current_count):
        # Play highest card that fits (same as current AI logic)
        for i in range(hand.num_cards, 0, -1):
            if current_count + hand.cards[i-1].value <= 31:
                return i-1
        return None


class LLMStrategy(AIStrategy):
    """LLM-powered strategy using Anthropic API.
    TODO: Implement API calls. Falls back to BasicStrategy for now."""
    name = "AI-LLM"
    description = "LLM-powered strategy (stub)"

    def __init__(self):
        self._fallback = BasicStrategy()

    def choose_crib_cards(self, hand, num_crib_cards):
        # TODO: Call Anthropic API with hand state
        return self._fallback.choose_crib_cards(hand, num_crib_cards)

    def choose_play_card(self, hand, current_count):
        # TODO: Call Anthropic API with play state
        return self._fallback.choose_play_card(hand, current_count)
