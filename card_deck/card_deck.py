# card and deck module

import random

class Card:

    VALUES = ['A','2','3','4','5','6','7','8','9','10','J','Q','K']
    SUITS = ['H','D','C','S']
    SUIT_MAPPING = {'H':'\u2665', 'D':'\u2666', 'C':'\u2663', 'S':'\u2660'}

    def __init__(self, suit = 'H', number = 1):
        self.suit = suit # one of [S,H,C,D]
        self.number = number # ace = 1 through K = 13
        self.value = min(10,number)

    def __str__(self):

        return '{}{}{}'.format(
            '' if self.number == 10 else ' ',
            Card.VALUES[self.number-1],
            Card.SUIT_MAPPING[self.suit])

    def __eq__(self, other):
        if not isinstance(other, Card):
            return NotImplemented
        return self.suit == other.suit and self.number == other.number

    def __hash__(self):
        return hash((self.suit, self.number))


class Deck:

    def __init__(self, num_cards=52):
        self.cards = []
        self.max_cards = num_cards

        for suit in Card.SUITS:
            for number in range(1, 14):
                if len(self.cards) < self.max_cards:
                    self.cards.append(Card(suit, number))

    @property
    def num_cards(self):
        return len(self.cards)

    def __str__(self):
        return ' '.join(str(c) for c in self.cards) + (' ' if self.cards else '')

    def shuffle(self):
        random.shuffle(self.cards)

    def deal_card(self):
        return self.cards.pop(0)

    def cut_deck(self, return_card=False):
        """ cuts card from random spot in deck.
        returns card.
        if return_card True, then also keeps card in deck """

        i = random.randint(0, self.num_cards - 1)

        if return_card:
            return self.cards[i]
        else:
            return self.cards.pop(i)

    def remove_cards(self, cards_to_remove):
        """ removes list of cards from deck """
        self.cards = [c for c in self.cards if c not in cards_to_remove]
        return self

    def remove_cards_inverse(self, cards_to_keep):
        """ removes cards not in list to keep
        returns list of cards removed """
        cards_removed = [c for c in self.cards if c not in cards_to_keep]
        self.cards = [c for c in self.cards if c in cards_to_keep]
        return cards_removed


class Hand(Deck):

    def __init__(self):
        self.cards = []

    def receive_card(self, card):
        self.cards.append(card)

    def play_card(self, i):
        return self.cards.pop(i)

    def reset(self):
        self.cards = []
