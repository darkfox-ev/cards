import sys, os, colorama, time, random
from collections import OrderedDict

COLORS = {'black':0, 'red':1, 'green':2, 'yellow':3, 'blue':4, 'magenta':5, 'cyan':6, 'white':7}


class Terminal:
    """
        https://www.lihaoyi.com/post/BuildyourownCommandLinewithANSIescapecodes.html
        https://en.wikipedia.org/wiki/ANSI_escape_code#CSI_codes
    """
    def __init__(self):
        colorama.init(autoreset=True)
        self.current_row = 1
        self.width, self.height = os.get_terminal_size()


    def clear_screen(self):
            sys.stdout.write(u"\u001b[2J")
            self.current_row = 1


    def text_blit(self, text, x=1, y=None, fore_colour=None, back_colour=None):
        fc = u'\u001b[3' + str(COLORS[fore_colour]) + 'm' if fore_colour else ''
        bc = u'\u001b[4' + str(COLORS[back_colour]) + 'm' if back_colour else ''
        
        if y is None:
            y = self.current_row
            self.current_row += 1

        sys.stdout.write(u'\u001b[{};{}H{}{}{}'.format(y, x, fc, bc, text))


    def get_input(self, msg):

        self.text_blit(msg, x=1, y=self.height - 1)
        self.text_blit(">>> ", x=1, y=self.height)
        
        msg_response = input()

        return msg_response


class Interface:
    def __init__(self):
        self.terminal = Terminal()
        self.terminal.clear_screen()
        self.current_display = OrderedDict() #dict of sections for display


    def print_line(self, text, centre=False):
        x = (self.terminal.width - len(text)) // 2 if centre else 1
        self.terminal.text_blit(text,x)


    def get_input(self, msg):
        return self.terminal.get_input(msg)


    def reset_display(self):
        self.current_display = {}


    def update_display(self):
        self.terminal.clear_screen()
        for v in self.current_display.values():
            for l in v:
                self.print_line(l)


    def set_game(self, g):
        self.game = g
    
    def welcome(self):
        pass

    def create_header(self):
        pass

    def start_game(self):
        pass

    def show_hand(self):
        pass

    def select_crib_cards(self, num_crib_cards):
        pass
    
    def show_turn_up(self, turn_up):
        pass

    def get_card_choice(self):
        pass

    def create_play_display(self):
        pass
    
    def show_play(self, current_player, card_played, count, score):
        pass

    def display_winner(self, winner):
        pass

    def show_round_score(self):
        pass

class CribInterface(Interface):
    COL_WIDTH = 15

    def __init__(self):
        Interface.__init__(self)


    def welcome(self):
        self.terminal.clear_screen()
        self.print_line('*************************************', True)
        self.print_line('*  WELCOME TO THE GAME OF CRIBBAGE  *', True)
        self.print_line('*  ver 0.1                          *', True)
        self.print_line('*************************************', True)
        return self.get_input('Enter player name: ')


    def update_display(self, show_hand=False):
        self.current_display['header'] = self.create_header()
        if show_hand:
            self.current_display['your_hand'] = self.show_hand()
        else:
            self.current_display['your_hand'] = list()
        Interface.update_display(self)


    def create_header(self):
        header = []
        s = 'THE GAME OF CRIBBAGE ver %s' % '0.1'
        header.append(s)
        header.append('*' * len(s))

        max_name_length = max([len(p.name) for p in self.game.players])
        for i in range(len(self.game.players)):
            padding = max_name_length - len(self.game.players[i].name) + 1
            s = '%s %s%s: %s\n' % (
                '*' if i == self.game.crib_player else ' ',
                self.game.players[i].name,
                ' ' * padding,
                self.game.score[i])

            header.append(s)
        header.append('-' * self.terminal.width)
        return(header)


    def start_game(self):
        self.update_display()
        self.print_line('')
        self.print_line('%s gets first Crib\n' % self.game.players[self.game.crib_player].name)
        
        self.get_input('Press <ENTER> to continue.')


    def show_hand(self):
        your_hand = ['Your hand: %s' % str(self.game.players[0].hand),]
        your_hand.append('           ')
        for i in range(self.game.players[0].hand.num_cards):
            your_hand[1] += ' %s^ ' % str(i + 1)
        your_hand.append('')
        return your_hand
        

    def select_crib_cards(self, num_crib_cards):
        valid_choice = False
        num_cards = self.game.players[0].hand.num_cards

        while not valid_choice:
            self.update_display(show_hand=True)
            r = self.get_input(
                'Choose %s cards for the crib using the numbers 1 through %s separated by spaces.'
                % (num_crib_cards, num_cards))
            try:
                card_indices = [int(i) - 1 for i in r.split(' ')]
                if all([i >= 0 and i < num_cards for i in card_indices]):
                    valid_choice = True
            except ValueError:
                pass
                
        return card_indices
    

    def show_turn_up(self, turn_up):
        self.current_display['turn_up'] = ['Turn up: %s' % str(turn_up), '']

        if turn_up.number == 11:
            self.current_display['turn_up'][0] += \
                '  (%s +2)' % self.game.players[self.game.game_round.crib_player].name
        self.update_display(show_hand=True)


    def get_card_choice(self):
        valid_choice = False
        num_cards = self.game.players[0].hand.num_cards

        while not valid_choice:
            self.update_display(show_hand=True)
            c = self.get_input(
                'Choose card to play using the numbers 1 through %s or 0 for a "Go".'
                % num_cards)
            
            try:
                card_index = int(c) - 1
                if card_index >= -1 and card_index < num_cards:
                    valid_choice = True
            except ValueError:
                pass

        if card_index == -1:
            return None
        else:
            return card_index


    def create_play_display(self):
        
        max_name_length = CribInterface.COL_WIDTH - 3
        play_order = [(self.game.game_round.crib_player + i) % self.game.num_players
            for i in range(1, self.game.num_players + 1)]
        play_display = ['',]
        for i in play_order:
            display_name = self.game.players[i].name[:max_name_length]
            play_display[0] += display_name
            play_display[0] += ' ' * (CribInterface.COL_WIDTH - len(display_name))
        play_display.append('-' * CribInterface.COL_WIDTH * self.game.num_players)
        self.current_display['play'] = play_display
        self.update_display(show_hand=True)
        

    def show_play(self, current_player, card_played, count, score):
        play_display = self.current_display['play']
        play_order = [(self.game.game_round.crib_player + i) % self.game.num_players
            for i in range(1, self.game.num_players + 1)]
        
        #remove previous count line if exists
        try:
            if play_display[-1][:5] == 'count':
                del(play_display[-1])
        except IndexError:
            pass
        
        #the play display is a table with players as columns and successive plays as rows
        #cell to add to table
        play_line = ''
        if card_played:
            play_line += str(card_played)
            if score > 0:
                play_line += ' +%s' % score
        elif count > 0:
            play_line += ' Go'
        elif score > 0:
            play_line += ' +%s' % score
        if play_line != ' +1':
            play_line += ' ' * (CribInterface.COL_WIDTH - len(play_line))

        #put it in the right position
        pos = play_order.index(current_player)
        if play_line == ' +1':
            to_remove = CribInterface.COL_WIDTH - len(' Go')
            play_display[-1] = play_display[-1][:-to_remove] + play_line
        elif pos == 0 or (card_played and count == card_played.value): #new line
            left_pad = ' ' * (CribInterface.COL_WIDTH * pos)
            play_display.append(left_pad + play_line)
        else:
            play_display[-1] += play_line
        
        #add the count to the end
        play_display.append('count: %s' % count)
        self.update_display(show_hand=True)


    def end_play(self):
        self.update_display(show_hand=False)
        self.get_input('Press <ENTER> to continue')


    def show_round_score(self, hand_score, crib_score):

        """
        AI1.0 hand:
        6♠  3♣  J♠  Q♥ --> 15

        goop hand:				      crib:
        6♠  3♣  J♠  Q♥ --> 15         6♠  3♣  J♠  Q♥ --> 15
        """
        score_lines = ['',]
        play_order = [(self.game.game_round.crib_player + i) % self.game.num_players
            for i in range(1, self.game.num_players + 1)]
        for p in play_order:
            score_lines.append('%s hand:' % self.game.players[p].name)
            score_lines.append('%s --> %s' % (str(self.game.players[p].played_cards),
                                              hand_score[p]))
            score_lines.append(' ')
        score_lines[-3] += '%scrib:' % (' ' * (24 - len(score_lines[-3])))
        score_lines[-2] += '%s%s --> %s' % (' ' * (24 - len(score_lines[-2])),
                                            str(self.game.game_round.crib), crib_score)

        self.current_display['score_lines'] = score_lines
        self.update_display(show_hand=False)
        self.get_input('Press <ENTER> to continue')
        self.reset_display()

    def display_winner(self, winner):
        self.get_input('Press <ENTER> to continue')









