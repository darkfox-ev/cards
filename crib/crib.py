# Crib module

import random
from card_deck import card_deck
from logger import logger
from interface import interface
from itertools import combinations
import copy


class Player:
    def __init__(self):
        self.hand = card_deck.Hand() #current hand before playing
        self.played_cards = card_deck.Hand()


class HumanPlayer(Player):
    def __init__(self, player_name, interf):
        Player.__init__(self)
        self.name = player_name
        self.interf = interf


    def play_card(self, current_count):

        if self.hand.num_cards == 0:
            return None

        card_chosen = self.interf.get_card_choice()
        
        if card_chosen is None:
            return None
        else:
            c = self.hand.play_card(card_chosen)
            return c


    def select_crib_cards(self, num_crib_cards):
        crib_chosen = self.interf.select_crib_cards(num_crib_cards)
        crib_chosen.sort(reverse=True)
        
        crib_cards = []
        for i in crib_chosen:
            crib_cards.append(self.hand.play_card(i))
        return crib_cards


class Test_Player(Player):
    def __init__(self, play_sequence):
        Player.__init__(self)
        self.play_sequence = play_sequence


    def select_crib_cards(self, num_crib_cards):
        """ will choose the cards indicated next in the play sequence list """
        card_indices = [self.play_sequence.pop(0) for i in range(num_crib_cards)]
        card_indices.sort(reverse=True)
        crib_cards = []
        for i in card_indices:
            crib_cards.append(self.hand.play_card(i))
        return crib_cards

    
    def play_card(self, current_count):
        """ will pay the card next in the play sequence list, -1 for "go" """
        card_index = self.play_sequence.pop(0)
        if card_index >= 0:
            return self.hand.play_card(card_index)
        else:
            return None
                

class AI_Player(Player):
    AI_VER = 1.0


    def __init__(self):
        Player.__init__(self)
        self.name = 'AI%s' % str(AI_Player.AI_VER)


    def select_crib_cards(self, num_crib_cards):
        cards = []

        # create temp deck with all cards not in hand
        temp_deck = card_deck.Deck(52).remove_cards(self.hand.cards)
        
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

    def __init__(self, num_players, players, interf, crib_player=None):

        if num_players < 2 or num_players > 4:
            raise ValueError
        if len(players) != num_players:
            raise ValueError

        self.num_players = num_players
        self.players = players
        self.round_number = 0
        self.score = [0 for _ in range(num_players)]
        self.interf = interf

        if not crib_player:
            self.crib_player = random.randint(0,num_players-1)
        elif crib_player < 0 or crib_player >= num_players:
            raise ValueError
        else:
            self.crib_player = crib_player

        game_details = ''
        self.logger = logger.Logger(game_details)
        

    def play(self):
        self.interf.start_game()

        while max(self.score) < 120:
            self.round_number += 1
            self.game_round = Round(self.num_players, self.players, self.crib_player, self.interf)
            self.logger.new_round(self.round_number, self.game_round.deal_cards())
            self.logger.crib(self.game_round.establish_crib())
            self.logger.turn_up(self.game_round.establish_turn_up())
            self.logger.the_play(self.game_round.play())
            self.logger.score_hands(self.game_round.score_hands())
            self.game_round.reset()
            
            self.score = [min(120, self.score[i] + self.game_round.score[i]) for i in range(self.num_players)]
            self.crib_player = (self.crib_player + 1) % self.num_players

        winner = self.score.index(max(self.score))
        self.interf.display_winner(winner)
        self.logger.record_winner(winner)
        

class Round:
    def __init__(self, num_players, players, crib_player, interf=None):
        self.deck = card_deck.Deck(52)
        self.num_players = num_players
        self.players = players
        self.score = [0 for _ in range(num_players)]
        self.crib_player = crib_player
        self.crib = card_deck.Hand()
        self.turn_up = None
        self.count = 0
        
        if interf:
            self.interf = interf
        else:
            self.interf = interface.Interface()
    

    def deal_cards(self):
        self.deck.shuffle()
        for i in range(Game.CARDS_PER_HAND[self.num_players]):
            for p in self.players:
                p.hand.receive_card(self.deck.deal_card())
        self.interf.show_hand()

        return 'ok'
        

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

        return 'ok'


    def establish_turn_up(self):
        self.turn_up = self.deck.cut_deck()
        if self.turn_up.suit == 'J':
            self.score[self.crib_player] += 2

        self.interf.show_turn_up(self.turn_up)
        return 'ok'


    def check_played(self, card_played, current_player):
        """ check if the card_played is valid"""

        if not card_played:
            valid_play = True
            for c in self.players[current_player].hand.cards:
                if self.count + c.value <= 31:
                    valid_play = False

        elif self.count + card_played.value > 31:
            valid_play = False
        
        else:
            valid_play= True

        return valid_play


    def score_played(self, card_played, played_cards):
        """ calculates the score the for the current played card given the cards already played"""

        score = 0
        if self.count == 15 or self.count == 31:
            score += 2

        if played_cards.num_cards >= 2:
            matches = 0
            while matches < played_cards.num_cards and played_cards.cards[-1].number == played_cards.cards[-1-matches].number:
                matches += 1
            if matches > 1:
                score += (2,6,12)[matches-2] #2 points for pair, 6 for three of kind, 12 for 4 of kind

            len_run = played_cards.num_cards
            while len_run > 2:
                numbers = sorted([c.number for c in played_cards.cards[-len_run:]])
                if numbers == list(range(min(numbers),max(numbers)+1)):
                    score += len_run
                    break
                else:
                    len_run -= 1
    
        return score


    def play(self):
        self.count = 0
        played_cards = card_deck.Hand()
        gos = [False for _ in self.players]
        current_player = (self.crib_player + 1) % self.num_players
        who_played_last = None
        self.interf.create_play_display()

        playing = True
        while playing:
            
            #if self.players[current_player].hand.num_cards == 0:
            #    gos[current_player] = True
            if not gos[current_player]:
                card_played = self.players[current_player].play_card(self.count) # play None for a "Go"
                while not self.check_played(card_played, current_player):
                    self.players[current_player].hand.receive_card(card_played) # return card
                    card_played = self.players[current_player].play_card(self.count) # play None for a "Go"

                if card_played:
                    self.count += card_played.value
                    played_cards.receive_card(card_played)
                    who_played_last = current_player
                    temp_score = self.score_played(card_played, played_cards)
                    self.score[who_played_last] += temp_score
                    self.interf.show_play(current_player, card_played, self.count, temp_score)
                    
                else:
                    gos[current_player] = True
                    self.interf.show_play(current_player, None, self.count, 0)
                    
            if self.count == 31 or all(gos):
                if all(gos):
                    self.score[who_played_last] += 1
                    self.interf.show_play(who_played_last, None, 0, 1)
                    
                self.count = 0
                gos = [False for _ in self.players]
                played_cards.reset()
                
            # check for end condition
            if all([p.hand.num_cards == 0 for p in self.players]):
                if self.count > 0 and not all(gos):
                    #the count will be zero if the last play was to 31
                    self.score[who_played_last] += 1
                    self.interf.show_play(who_played_last, None, 0, 1)
                self.interf.end_play()  
                playing = False
                print('\n')
            else:
                current_player = (current_player + 1) % self.num_players

        return 'ok'

        
    def score_hands(self):
        for i in range(self.num_players):
            self.score[i] += count_hand(self.players[i].played_cards, self.turn_up)
        self.score[self.crib_player] += count_hand(self.crib, self.turn_up)
        self.interf.show_round_score()
        return 'ok'


    def reset(self):
        for p in self.players:
            p.hand.reset()
            p.played_cards.reset()


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