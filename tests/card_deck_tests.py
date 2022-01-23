import unittest
from card_deck import card_deck

class DeckTestCase(unittest.TestCase):
    
    
    def test_basic_deck(self):
        deck = card_deck.Deck()
        self.assertEqual(
            str(deck),
            'A\x03 2\x03 3\x03 4\x03 5\x03 6\x03 7\x03 8\x03 9\x03 10\x03 J\x03 Q\x03 K\x03 A\x04 2\x04 3\x04 4\x04 5\x04 6\x04 7\x04 8\x04 9\x04 10\x04 J\x04 Q\x04 K\x04 A\x05 2\x05 3\x05 4\x05 5\x05 6\x05 7\x05 8\x05 9\x05 10\x05 J\x05 Q\x05 K\x05 A\x06 2\x06 3\x06 4\x06 5\x06 6\x06 7\x06 8\x06 9\x06 10\x06 J\x06 Q\x06 K\x06 '
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