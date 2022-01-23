import unittest
from card_deck.card_deck import Hand, Card
from crib import crib

class RoundTestCase(unittest.TestCase):
    
    def setUp(self):
        pass

    def test_no_gos(self):
        """ sequence of play 2, 5, 3, 7, 6, 1, 1, 1
            tests no "go"s, pair and 3 of a kind

            p1 score = 2
            p2 score = 7
        """

        p1 = crib.Test_Player([0,0,0,0])
        p1.hand = Hand()
        for c in [Card('H',2), Card('S',3), Card('C',6), Card('D',1)]:
            p1.hand.receive_card(c)
        
        p2 = crib.Test_Player([0,0,0,0])
        p2.hand = Hand()
        for c in [Card('H',5), Card('S',7), Card('C',1), Card('H',1)]:
            p2.hand.receive_card(c)
        
        r = crib.Round(2, [p1, p2], 1)
        r.play()
        
        self.assertEqual(r.score[0], 2)
        self.assertEqual(r.score[1], 7)


    def test_card_runs(self):
        """ sequence of play 7, 8, 9, go, go, 10, 9, 11, go, go, 10, 12
        tests multiple "go"s, 15s, runs 
        
        p1 score = 4
        p2 score = 7 """
        
        p1 = crib.Test_Player([0,0,-1,0,-1,0])
        p1.hand = Hand()
        for c in [Card('H',7), Card('S',9), Card('C',9), Card('D',10)]:
            p1.hand.receive_card(c)
        
        p2 = crib.Test_Player([0,-1,0,0,-1,0])
        p2.hand = Hand()
        for c in [Card('H',8), Card('S',10), Card('C',11), Card('H',12)]:
            p2.hand.receive_card(c)
        
        r = crib.Round(2, [p1, p2], 1)
        r.play()
        
        self.assertEqual(r.score[0], 4)
        self.assertEqual(r.score[1], 7)


    def test_card_runs2(self):
        """ sequence of play 2, 5, 3, 6, 4, J, A, Q
        tests long hidden run and 31
        
        p1 score = 7
        p2 score = 1 """

        p1 = crib.Test_Player([0,0,0,0])
        p1.hand = Hand()
        for c in [Card('H',2), Card('H',3), Card('H',4), Card('H',1)]:
            p1.hand.receive_card(c)
        
        p2 = crib.Test_Player([0,0,0,0])
        p2.hand = Hand()
        for c in [Card('S',5), Card('S',6), Card('S',11), Card('S',12)]:
            p2.hand.receive_card(c)
        
        r = crib.Round(2, [p1, p2], 1)
        r.play()

        self.assertEqual(r.score[0], 7)
        self.assertEqual(r.score[1], 1)
        

if __name__ == '__main__':
    unittest.main()