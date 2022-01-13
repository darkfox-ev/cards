# testing
import CardDeck
import Crib

def big_loop():
    f = open('c:\\temp\\crib.txt','w')
    for i in range(50000):    
        d = CardDeck.Deck()
        d.shuffle()

        h = CardDeck.Hand()
        for j in range(4):
            h.receive_card(d.deal_card())

        turn_up = d.cut_deck()
        
        f.write(str(Crib.count_hand(h,turn_up)))
        f.write('\n')
    f.close()


def custom():
    h = CardDeck.Hand()
    h.receive_card(CardDeck.Card('H',5))
    h.receive_card(CardDeck.Card('S',5))
    h.receive_card(CardDeck.Card('C',5))
    h.receive_card(CardDeck.Card('D',11))
    turn_up = CardDeck.Card('D',5)

    print(Crib.count_hand(h,turn_up))

def typical_game():
    p1 = Crib.AI_Player()
    p2 = Crib.AI_Player()
    g = Crib.Game(2, [p1, p2])
    g.play()


def test_crib_selector():
    p1 = Crib.AI_Player()
    d = CardDeck.Deck()
    d.shuffle()
    for i in range(6):
        p1.hand.receive_card(d.deal_card())
    
    print(p1.hand)
    crib_cards = p1.select_crib_cards(2)
    for c in crib_cards:
        print(c)

def test_remove_cards():
    d = CardDeck.Deck(52)
    print(d)
    cards = [CardDeck.Card('H',1)]
    d.remove_cards(cards)
    print(d)

def test_remove_cards_inverse():
    d = CardDeck.Deck(52)
    print(d)
    cards_to_keep = [CardDeck.Card('H',5),CardDeck.Card('S',10)]
    r = d.remove_cards_inverse(cards_to_keep)
    print(d)
    for c in r:
        print(c)


def test_count_played_points():
    h = CardDeck.Hand()
    h.receive_card(CardDeck.Card('H',1))
    h.receive_card(CardDeck.Card('S',4))
    h.receive_card(CardDeck.Card('C',3))
    h.receive_card(CardDeck.Card('C',5))
    print(h)
    print(Crib.check_played_points(h))

if __name__ == '__main__':
    typical_game()
    #test_count_played_points()
    