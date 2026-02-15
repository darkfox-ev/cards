# AI Strategy module - defines different AI decision-making strategies

import os
import re
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


def get_llm_strategies():
    """Fetch available models from Anthropic API and return LLMStrategy instances.
    Returns (strategies, error_message) tuple. On failure, strategies is empty
    and error_message describes the problem."""
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        return [], "ANTHROPIC_API_KEY environment variable not set. LLM opponents disabled."
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        response = client.models.list(limit=100)
        strategies = []
        for model in response.data:
            strategies.append(LLMStrategy(model.id, model.display_name, client))
        if not strategies:
            return [], "No models available from Anthropic API."
        return strategies, None
    except Exception as e:
        return [], f"Could not initialize Anthropic API: {e}"


class LLMStrategy(AIStrategy):
    """LLM-powered strategy using Anthropic API.
    Model is configurable via constructor parameter.
    Falls back to BasicStrategy on any API or parsing error."""

    SYSTEM_PROMPT = (
        "You are an expert Cribbage player. In Cribbage:\n"
        "- Card values: A=1, 2-9=face value, 10/J/Q/K=10\n"
        "- Hand scoring: pairs (2pts), fifteens (2pts each combo summing to 15), "
        "runs of 3+ (1pt per card), flush (4+ same suit), his nob (J of turn suit)\n"
        "- Play phase: players alternate playing cards, running count must not exceed 31. "
        "Reaching exactly 15 or 31 scores 2pts. Pairs/runs in sequence score points.\n"
        "Respond ONLY with the requested card number(s), nothing else."
    )

    def __init__(self, model_id, display_name=None, client=None):
        self.model = model_id
        self._fallback = BasicStrategy()
        if client is not None:
            self.client = client
        else:
            import anthropic
            api_key = os.environ.get('ANTHROPIC_API_KEY')
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY environment variable not set")
            self.client = anthropic.Anthropic(api_key=api_key)
        self.name = f"AI-LLM ({display_name or model_id})"
        self.description = model_id

    @staticmethod
    def _format_cards(hand):
        """Format hand cards as a numbered list for the LLM."""
        return ", ".join(
            f"{i}: {card_deck.Card.VALUES[c.number-1]}{c.suit}"
            for i, c in enumerate(hand.cards)
        )

    def _ask(self, user_prompt):
        """Send a prompt to the LLM and return the response text."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=50,
            system=self.SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return response.content[0].text.strip()

    def choose_crib_cards(self, hand, num_crib_cards):
        try:
            cards_str = self._format_cards(hand)
            prompt = (
                f"Your hand: [{cards_str}]\n"
                f"Choose {num_crib_cards} card(s) to discard to the crib.\n"
                f"Reply with ONLY the card indices (0-{hand.num_cards - 1}) "
                f"separated by commas. Example: 0,3"
            )
            text = self._ask(prompt)
            indices = [int(x.strip()) for x in re.findall(r'\d+', text)]
            # Validate indices
            if (len(indices) == num_crib_cards
                    and all(0 <= i < hand.num_cards for i in indices)
                    and len(set(indices)) == num_crib_cards):
                return indices
        except Exception:
            pass
        return self._fallback.choose_crib_cards(hand, num_crib_cards)

    def choose_play_card(self, hand, current_count):
        try:
            cards_str = self._format_cards(hand)
            valid = [i for i in range(hand.num_cards)
                     if current_count + hand.cards[i].value <= 31]
            if not valid:
                return None
            prompt = (
                f"Your hand: [{cards_str}]\n"
                f"Current count: {current_count}\n"
                f"Valid card indices (count won't exceed 31): {valid}\n"
                f"Choose ONE card index to play. Reply with ONLY the index number."
            )
            text = self._ask(prompt)
            numbers = re.findall(r'\d+', text)
            if numbers:
                idx = int(numbers[0])
                if idx in valid:
                    return idx
        except Exception:
            pass
        return self._fallback.choose_play_card(hand, current_count)
