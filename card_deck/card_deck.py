# card and deck module

import random

class Card:

    VALUES = ['A','2','3','4','5','6','7','8','9','10','J','Q','K']
    SUITS = ['H','D','C','S']
    SUIT_MAPPING = {'H':chr(3), 'D':chr(4), 'C':chr(5), 'S':chr(6)}

    def __init__(self, suit = 'H', number = 1):
        self.suit = suit # one of [S,H,C,D]
        self.number = number # ace = 1 through K = 13
        
    def __str__(self):
        
        return '{}{}'.format(Card.VALUES[self.number-1], Card.SUIT_MAPPING[self.suit])

class Deck:

    def __init__(self, num_cards=52):
        self.cards = list()
        self.num_cards = num_cards
        self.max_cards = num_cards

        value = 0
        suit = 0
        for i in range(self.max_cards):
            self.cards.append(Card(Card.SUITS[suit], value + 1))
            value = value + 1
            if value > 12:
                value = 0
                suit = (suit + 1) % 4

    def __str__(self):
        out_str = ""
        for i in range(self.num_cards):
            out_str += str(self.cards[i]) + ' '
        return out_str

    def shuffle(self):
        random.shuffle(self.cards)

    def deal_card(self):
        c = self.cards.pop(0)
        self.num_cards -= 1
        return c

    def cut_deck(self, return_card=False):
        """ cuts card from random spot in deck. 
        returns card.
        if return_card True, then also keeps card in deck """

        i = random.randint(0,self.num_cards-1)
        
        if return_card:
            return self.cards[i]
        else:
            c = self.cards.pop(i)
            self.num_cards -= 1
            return c

    def remove_cards(self, cards_to_remove):
        """ removes list of cards from deck """
        
        for i in range(self.num_cards, 0, -1):
            for c in cards_to_remove:
                try:
                    if self.cards[i-1].suit == c.suit and self.cards[i-1].number == c.number:
                        self.cards.pop(i-1)
                except IndexError:
                    pass
        self.num_cards = len(self.cards)
        return self


    def remove_cards_inverse(self, cards_to_keep):
        """ removes cards not in list to keep
        returns list of cards removed """
        cards_removed = []
        for i in range(self.num_cards, 0, -1):
            found = False
            for c in cards_to_keep:
                if c.suit == self.cards[i-1].suit and c.number == self.cards[i-1].number:
                    found = True
            if not found:
                cards_removed.append(self.cards.pop(i-1))
                self.num_cards -= 1    
                
        return cards_removed


class Hand(Deck):

    def __init__(self):
        self.cards = []
        self.num_cards = 0

    def receive_card(self, card):
        self.cards.append(card)
        self.num_cards += 1

    def play_card(self, i):
        self.num_cards -= 1
        return self.cards.pop(i)

    def reset(self):
        self.cards = []
        self.num_cards = 0
        