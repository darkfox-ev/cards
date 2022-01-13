# Crib module

import random
import CardDeck
from itertools import combinations
import copy
import Logger

class Player:

    def __init__(self):
        self.hand = CardDeck.Hand() #current hand before playing
        self.played_cards = CardDeck.Hand()

    def play_card(self, current_count):
        print(self.hand)
        print('Count: %s' % current_count)
        card_played = input('Choose: ')
        if card_played == 'go':
            return None
        else:
            card_played = int(card_played)
        c = self.hand.play_card(card_played)
        print(c)
        return c


class AI_Player(Player):

    def __init__(self):
        Player.__init__(self)
        # added comment


    def select_crib_cards(self, num_crib_cards):
        cards = []

        # create temp deck with all cards not in hand
        temp_deck = CardDeck.Deck(52).remove_cards(self.hand.cards)
        
        best_combo = None
        best_points = -1

        # find combo that has the highest potential score
        for combo in combinations(self.hand.cards, self.hand.num_cards - num_crib_cards):
            points = 0
            for card in temp_deck.cards:
                points += count_hand(combo, card)
            if points > best_points:
                best_combo = copy.deepcopy(combo)
                best_points = points
        
        return self.hand.remove_cards_inverse(best_combo)


    def play_card(self, current_count):
        # play first one that fits
        for i in range(self.hand.num_cards,0,-1):
            if current_count + min(10,self.hand.cards[i-1].number) <= 31:
                return self.hand.play_card(i-1)
        return None


class Game:
    
    CARDS_PER_HAND = {2:6,3:5,4:5} # keys are number of players

    def __init__(self, num_players, players, crib_player=None):

        if num_players < 2 or num_players > 4:
            raise ValueError
        if len(players) != num_players:
            raise ValueError

        self.num_players = num_players
        self.players = players
        self.round_number = 0
        self.score = [0 for _ in range(num_players)]
        
        if not crib_player:
            self.crib_player = random.randint(0,num_players-1)
            
        elif crib_player < 0 or crib_player >= num_players:
            raise ValueError
        else:
            self.crib_player = crib_player

        #self.logger = Logger.Logger()

    def play(self):
        
        while max(self.score) < 120:
            self.round_number += 1
            game_round = Round(self.num_players, self.players, self.crib_player)
            
            print('Round {} (player {} crib):'.format(self.round_number,self.crib_player))
            for i in range(self.num_players):
                print('Player {}: {}'.format(i,str(game_round.players[i].hand)))
            
            game_round.establish_crib()
            game_round.establish_turn_up()
            print('\n')
            print(game_round)
            
            print('\n the play...')
            game_round.play()
            game_round.score_hands()
            game_round.reset()
            
            self.score = [self.score[i] + game_round.score[i] for i in range(self.num_players)]
            for i in range(self.num_players):
                print('Player {}: {}/{}'.format(i, game_round.score[i], self.score[i]))

            self.crib_player = (self.crib_player + 1) % self.num_players
            print('\n')

        winner = self.score.index(max(self.score))
        print('Player {} wins!'.format(winner))
        

class Round:

    def __init__(self, num_players, players, crib_player):
        self.deck = CardDeck.Deck(52)
        self.deck.shuffle()
        self.num_players = num_players
        self.players = players
        self.score = [0 for _ in range(num_players)]
        self.crib_player = crib_player

        for i in range(Game.CARDS_PER_HAND[self.num_players]):
            for p in self.players:
                p.hand.receive_card(self.deck.deal_card())
        
        self.crib = CardDeck.Hand()
        self.turn_up = None

        #self.the_play = [] # list of dicts.. the dicts are {player: , card: , count: , points_awarded: }

        self.count = 0
        

    def __str__(self):
        s = ''
        for i in range(self.num_players):
            s += 'player {}: {}\n'.format(i, str(self.players[i].hand))
        s += 'crib: {}\n'.format(str(self.crib))
        s += 'turn up: {}'.format(str(self.turn_up))
        return s

    
    def establish_crib(self):
        if self.num_players == 2:
            num_crib_cards = 2
        else:
            num_crib_cards = 1

        for p in self.players:
            crib_cards = p.select_crib_cards(num_crib_cards)
            for c in crib_cards:
                self.crib.receive_card(c)
        
        if self.num_players == 3:
            self.crib.receive_card(self.deck.deal_card())


    def establish_turn_up(self):
        self.turn_up = self.deck.cut_deck()
        if self.turn_up.suit == 'J':
            self.score[self.crib_player] += 2


    def play(self):
        self.count = 0
        count_played_cards = CardDeck.Hand()
        num_played_cards = 0
        num_gos = 0
        who_played_last = None
        current_player = (self.crib_player + 1) % self.num_players
        playing = True
        
        while playing:
            valid_play = False
            while not valid_play:
                card_played = self.players[current_player].play_card(self.count) # play None for a "Go"
                
                # check if valid card
                if not card_played:
                    # check if Go is valid
                    valid_play = True
                    for c in self.players[current_player].hand.cards:
                        if self.count + min(10,c.number) <= 31:
                            valid_play = False
                elif self.count + min(10, card_played.number) > 31:
                    valid_play = False
                else:
                    valid_play= True

                if not valid_play:
                    # return card
                    self.players[current_player].hand.receive_card(card_played)

            # valid play
            temp_score = 0
            if not card_played:
                print('Player {}: Go'.format(current_player))
                num_gos += 1
            else:
                self.count += min(10, card_played.number)
                count_played_cards.receive_card(card_played)
                self.players[current_player].played_cards.receive_card(card_played)
                num_played_cards += 1
                who_played_last = current_player
                num_gos = 0 # these reset if the other player can play
                if self.count == 15 or self.count == 31:
                    temp_score += 2

                temp_score += check_played_points(count_played_cards)
                
                self.score[current_player] += temp_score
                print('Player {}: {}, count: {}, for {}'.format(current_player, str(card_played), self.count, temp_score))

            if self.count == 31 or num_gos == self.num_players:
                if num_gos == self.num_players:
                    temp_score += 1
                    self.score[who_played_last] += 1
                    print('Player {}: ... for 1'.format(who_played_last))
                
                self.count = 0
                num_gos = 0
                count_played_cards.reset()

            # check for end condition
            if num_played_cards == self.num_players * 4:
                if self.count > 0 and num_gos < self.num_players:
                    #the count will be zero if the last play was to 31
                    self.score[who_played_last] += 1
                    print('Player {}: ... last card for 1'.format(who_played_last))
                playing = False
                print('\n')
            else:
                current_player = (current_player + 1) % self.num_players

        
    def score_hands(self):
        for i in range(self.num_players):
            self.score[i] += count_hand(self.players[i].played_cards, self.turn_up)
        self.score[self.crib_player] += count_hand(self.crib, self.turn_up)


    def reset(self):
        for p in self.players:
            p.hand.reset()
            p.played_cards.reset()


def check_played_points(hand):
    if hand.num_cards < 2:
        return 0

    matches = 0
    while matches < hand.num_cards and hand.cards[-1].number == hand.cards[-1-matches].number:
        matches += 1
        
    if matches > 1:
        return (2,6,12)[matches-2] #2 points for pair, 6 for three of kind, 12 for 4 of kind

    len_run = hand.num_cards
    while len_run > 2:
        numbers = sorted([c.number for c in hand.cards[-len_run:]])
        if numbers == list(range(min(numbers),max(numbers)+1)):
            return len_run
        else:
            len_run -= 1
    
    return 0


def count_hand(hand, turn_up):
    
    try:
        cards = list(hand.cards)
    except AttributeError:
        cards = list(hand)
    
    all_cards = cards
    all_cards.append(turn_up)

    score = 0

    # count the fifteens, pairs and runs
    for i in range(2,len(all_cards)+1):
        for combo in combinations(all_cards,i):
            # count the fifteens
            x = 0
            for card in combo:
                x += min(10,card.number)
            
            if x == 15:
                score += 2

            #if a 2 combo check for pair
            if i == 2:
                if combo[0].number == combo[1].number:
                    score += 2

            #if a 3 combo or more, check for run, if 4 or 5 combo remove previous run score
            if i >= 3:
                numbers = sorted([c.number for c in combo])
                
                if numbers == list(range(min(numbers),max(numbers)+1)):
                    score += i
                    
                    if i == 4:
                        score -= 6 # two 3 card runs would have been found already
                        
                    if i == 5:
                        score -= 5 # two 4 card runs would have been found already
                        
                
   
    # check for flush
    suits = [c.suit for c in cards]
    
    if len(set(suits)) == 1:
        score += 4
        if suits[0] == turn_up.suit:
            score +=1

    # check for turn_up jack
    for c in cards:
        if c.number == 11 and c.suit == turn_up.suit:
            score += 1

    return score