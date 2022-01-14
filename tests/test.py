# testing
from card_deck import card_deck
from crib import crib

def big_loop():
    f = open('c:\\temp\\crib.txt','w')
    for i in range(50000):    
        d = card_deck.Deck()
        d.shuffle()

        h = card_deck.Hand()
        for j in range(4):
            h.receive_card(d.deal_card())

        turn_up = d.cut_deck()
        
        f.write(str(crib.count_hand(h,turn_up)))
        f.write('\n')
    f.close()


def custom():
    h = card_deck.Hand()
    h.receive_card(card_deck.Card('H',5))
    h.receive_card(card_deck.Card('S',5))
    h.receive_card(card_deck.Card('C',5))
    h.receive_card(card_deck.Card('D',11))
    turn_up = card_deck.Card('D',5)

    print(crib.count_hand(h,turn_up))

def typical_game():
    p1 = crib.AI_Player()
    p2 = crib.AI_Player()
    g = crib.Game(2, [p1, p2])
    g.play()


def test_crib_selector():
    p1 = crib.AI_Player()
    d = card_deck.Deck()
    d.shuffle()
    for i in range(6):
        p1.hand.receive_card(d.deal_card())
    
    print(p1.hand)
    crib_cards = p1.select_crib_cards(2)
    for c in crib_cards:
        print(c)

def test_remove_cards():
    d = card_deck.Deck(52)
    print(d)
    cards = [card_deck.Card('H',1)]
    d.remove_cards(cards)
    print(d)

def test_remove_cards_inverse():
    d = card_deck.Deck(52)
    print(d)
    cards_to_keep = [card_deck.Card('H',5),card_deck.Card('S',10)]
    r = d.remove_cards_inverse(cards_to_keep)
    print(d)
    for c in r:
        print(c)


def test_count_played_points():
    h = card_deck.Hand()
    h.receive_card(card_deck.Card('H',1))
    h.receive_card(card_deck.Card('S',4))
    h.receive_card(card_deck.Card('C',3))
    h.receive_card(card_deck.Card('C',5))
    print(h)
    print(crib.check_played_points(h))


def test_play_counting():
    #this current requires interaction at terminal and manual inspection
    
    p1 = crib.Player()
    p2 = crib.Player()
    r = crib.Round(2, (p1,p2), 0)

    h1 = card_deck.Hand()
    h1.receive_card(card_deck.Card('H',9))
    h1.receive_card(card_deck.Card('H',10))
    h1.receive_card(card_deck.Card('H',11))
    h1.receive_card(card_deck.Card('H',12))
    p1.hand = h1

    h2 = card_deck.Hand()
    h2.receive_card(card_deck.Card('S',10))
    h2.receive_card(card_deck.Card('S',2))
    h2.receive_card(card_deck.Card('S',11))
    h2.receive_card(card_deck.Card('S',1))
    p2.hand = h2
    
    print(r)
    r.play()

def test_play_against_ai():

    p1 = crib.Player()
    p2 = crib.AI_Player()
    g = crib.Game(2, [p1, p2])
    g.play()



if __name__ == '__main__':
    #typical_game()
    test_play_against_ai()
    