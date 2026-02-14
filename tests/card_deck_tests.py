import unittest
from card_deck import card_deck

class DeckTestCase(unittest.TestCase):
    
    
    def test_basic_deck(self):
        deck = card_deck.Deck()
        self.assertEqual(
            str(deck),
            ' A\u2665  2\u2665  3\u2665  4\u2665  5\u2665  6\u2665  7\u2665  8\u2665  9\u2665 10\u2665  J\u2665  Q\u2665  K\u2665  A\u2666  2\u2666  3\u2666  4\u2666  5\u2666  6\u2666  7\u2666  8\u2666  9\u2666 10\u2666  J\u2666  Q\u2666  K\u2666  A\u2663  2\u2663  3\u2663  4\u2663  5\u2663  6\u2663  7\u2663  8\u2663  9\u2663 10\u2663  J\u2663  Q\u2663  K\u2663  A\u2660  2\u2660  3\u2660  4\u2660  5\u2660  6\u2660  7\u2660  8\u2660  9\u2660 10\u2660  J\u2660  Q\u2660  K\u2660 '
        )


    def test_cut_deck(self):
        deck = card_deck.Deck()
        c1 = deck.cut_deck(False)
        self.assertIsInstance(c1, card_deck.Card)
        self.assertEqual(deck.num_cards,51)

        c2 = deck.cut_deck(True)
        self.assertIsInstance(c2, card_deck.Card)
        self.assertEqual(deck.num_cards,51)


    def test_remove_cards(self):
        deck = card_deck.Deck()
        cards_to_remove = [card_deck.Card('H',1)]
        deck = deck.remove_cards(cards_to_remove)
        self.assertEqual(deck.num_cards, 51)

        cards_to_remove = [card_deck.Card('S',1), card_deck.Card('D',1)]
        deck = deck.remove_cards(cards_to_remove)
        self.assertEqual(deck.num_cards, 49)

        #try to remove cards that don't exist
        deck = deck.remove_cards(cards_to_remove)
        self.assertIsInstance(deck, card_deck.Deck)


    def test_remove_cards_inverse(self):
        deck = card_deck.Deck()
        cards_to_keep = [card_deck.Card('S',1), card_deck.Card('D',1)]
        cards_removed = deck.remove_cards_inverse(cards_to_keep)
        self.assertEqual(deck.num_cards, 2)
        self.assertEqual(len(cards_removed), 50)


if __name__ == '__main__':
    unittest.main()