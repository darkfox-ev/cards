import sys, os, re, colorama, time, random
from collections import OrderedDict


class GameQuitException(Exception):
    pass

COLORS = {'black':0, 'red':1, 'green':2, 'yellow':3, 'blue':4, 'magenta':5, 'cyan':6, 'white':7}

# ANSI escape codes for inline coloring
RED = '\u001b[31m'
WHITE = '\u001b[37m'
CYAN = '\u001b[36m'
YELLOW = '\u001b[33m'
GREEN = '\u001b[32m'
BOLD = '\u001b[1m'
UNDERLINE = '\u001b[4m'
RESET = '\u001b[0m'

ANSI_PATTERN = re.compile(r'\u001b\[[0-9;]*m')

def visible_len(text):
    """Return the visible length of text, excluding ANSI escape codes"""
    return len(ANSI_PATTERN.sub('', text))


class Terminal:
    """
        https://www.lihaoyi.com/post/BuildyourownCommandLinewithANSIescapecodes.html
        https://en.wikipedia.org/wiki/ANSI_escape_code#CSI_codes
    """
    def __init__(self):
        colorama.init(autoreset=True)
        self.current_row = 1
        try:
            self.width, self.height = os.get_terminal_size()
        except OSError:
            self.width, self.height = 80, 24


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

        hint = '  (q to quit)'
        if len(msg) + len(hint) <= self.width:
            msg += hint
        self.text_blit(msg, x=1, y=self.height - 1)
        self.text_blit(">>> ", x=1, y=self.height)

        msg_response = input()

        if msg_response.strip().lower() in ('q', 'quit'):
            raise GameQuitException()

        return msg_response


class Interface:
    def __init__(self):
        self.terminal = Terminal()
        self.terminal.clear_screen()
        self.current_display = OrderedDict() #dict of sections for display
        self.score = None

    def print_line(self, text, centre=False):
        x = (self.terminal.width - visible_len(text)) // 2 if centre else 1
        self.terminal.text_blit(text,x)


    def get_input(self, msg):
        return self.terminal.get_input(msg)


    def reset_display(self):
        self.current_display = {}


    def update_display(self):
        self.terminal.width, self.terminal.height = os.get_terminal_size()
        self.terminal.clear_screen()

        # Collect all lines and trim if they exceed terminal height
        all_lines = []
        for v in self.current_display.values():
            all_lines.extend(v)

        max_lines = self.terminal.height - 3  # reserve space for input area
        if len(all_lines) > max_lines:
            all_lines = all_lines[-max_lines:]

        for l in all_lines:
            self.print_line(l)


    def set_game(self, g):
        self.game = g
        self.score = [0 for i in range(g.num_players)]

    def welcome(self):
        pass

    def choose_ai(self, strategies):
        return strategies[0]

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

    def end_play(self):
        pass

    def show_round_score(self, hand_score, crib_score):
        pass

    def end_play(self):
        pass

class CribInterface(Interface):
    COL_WIDTH = 15

    def __init__(self):

        super().__init__()


    def colorize_card(self, card):
        """Return card string with red for hearts/diamonds, white for spades/clubs"""
        s = str(card)
        if card.suit in ('H', 'D'):
            return RED + s + RESET
        return s


    def colorize_card_str(self, cards):
        """Colorize all cards in a hand/deck string representation"""
        parts = []
        for card in cards:
            parts.append(self.colorize_card(card))
        return ' '.join(parts) + (' ' if cards else '')


    def welcome(self):
        self.terminal.clear_screen()
        self.print_line(CYAN + '*************************************' + RESET, True)
        self.print_line(CYAN + '*' + RESET + BOLD + '  WELCOME TO THE GAME OF CRIBBAGE  ' + RESET + CYAN + '*' + RESET, True)
        self.print_line(CYAN + '*  ver 0.1                          *' + RESET, True)
        self.print_line(CYAN + '*************************************' + RESET, True)
        return self.get_input('Enter player name: ')


    def choose_ai(self, strategies):
        self.print_line('')
        self.print_line('Choose your opponent:')
        for i, s in enumerate(strategies):
            self.print_line('  %s%d%s - %s (%s)' % (BOLD, i+1, RESET, s.name, s.description))
        valid = False
        while not valid:
            choice = self.get_input('Enter choice (1-%d): ' % len(strategies))
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(strategies):
                    valid = True
            except ValueError:
                pass
        return strategies[idx]


    def update_display(self, show_hand=False):
        self.current_display['header'] = self.create_header()
        if show_hand:
            self.current_display['your_hand'] = self.show_hand()
        else:
            self.current_display['your_hand'] = list()
        super().update_display()


    def create_header(self):
        header = []
        s = BOLD + 'THE GAME OF CRIBBAGE ver %s' % '0.1' + RESET
        header.append(s)
        header.append('*' * 27)

        max_name_length = max([len(p.name) for p in self.game.players])
        for i in range(len(self.game.players)):
            padding = max_name_length - len(self.game.players[i].name) + 1
            crib_marker = GREEN + '*' + RESET if i == self.game.crib_player else ' '
            name = CYAN + self.game.players[i].name + RESET
            score_val = YELLOW + str(self.score[i]) + RESET
            s = '%s %s%s: %s\n' % (
                crib_marker,
                name,
                ' ' * padding,
                score_val)

            header.append(s)
        header.append('-' * self.terminal.width)
        return(header)


    def start_game(self):
        self.update_display()
        self.print_line('')
        self.print_line('%s gets first Crib\n' % (CYAN + self.game.players[self.game.crib_player].name + RESET))

        self.get_input('Press <ENTER> to continue.')


    def show_hand(self):
        hand = self.game.players[0].hand
        hand.sort()
        num_cards = hand.num_cards
        colorized = self.colorize_card_str(hand.cards)
        prefix = 'Your hand (%s cards): ' % num_cards
        your_hand = ['%s%s' % (prefix, colorized),]
        your_hand.append(' ' * len(prefix))
        for i in range(num_cards):
            your_hand[1] += ' %s^ ' % str(i + 1)
        your_hand.append('')
        return your_hand


    def select_crib_cards(self, num_crib_cards):
        valid_choice = False
        num_cards = self.game.players[0].hand.num_cards
        error_msg = None

        while not valid_choice:
            self.update_display(show_hand=True)
            if error_msg:
                self.print_line(RED + error_msg + RESET)
            r = self.get_input(
                'Choose %s cards for the crib using the numbers 1 through %s separated by spaces.'
                % (num_crib_cards, num_cards))
            try:
                card_indices = [int(i) - 1 for i in r.split(' ')]
                if len(card_indices) == num_crib_cards and all([i >= 0 and i < num_cards for i in card_indices]):
                    valid_choice = True
                else:
                    error_msg = 'Invalid selection, try again.'
            except ValueError:
                error_msg = 'Invalid selection, try again.'

        return card_indices


    def show_turn_up(self, turn_up):
        colorized = self.colorize_card(turn_up)
        self.current_display['turn_up'] = ['Turn up: %s' % colorized, '']

        if turn_up.number == 11:
            self.current_display['turn_up'][0] += \
                '  (%s +2)' % self.game.players[self.game.game_round.crib_player].name
            self.score[self.game.game_round.crib_player] += 2
        self.update_display(show_hand=True)


    def get_card_choice(self):
        hand = self.game.players[0].hand
        num_cards = hand.num_cards
        current_count = self.game.game_round.count

        # Check if any card can be played
        can_play = any(current_count + c.value <= 31 for c in hand.cards)

        if not can_play:
            # Auto-Go: no playable cards
            self.update_display(show_hand=True)
            self.print_line(YELLOW + 'No playable cards — Go!' + RESET)
            self.get_input('Press ENTER to continue.')
            return None

        error_msg = None
        while True:
            self.update_display(show_hand=True)
            if error_msg:
                self.print_line(RED + error_msg + RESET)
            c = self.get_input(
                'Choose card to play (1-%s).' % num_cards)

            c = c.strip()
            if c == '':
                error_msg = 'Enter a card number (1-%s).' % num_cards
                continue

            try:
                card_index = int(c) - 1
                if card_index >= 0 and card_index < num_cards:
                    return card_index
                else:
                    error_msg = 'Invalid choice, try again.'
            except ValueError:
                error_msg = 'Invalid choice, try again.'


    def create_play_display(self):

        max_name_length = CribInterface.COL_WIDTH - 3
        play_order = [(self.game.game_round.crib_player + i) % self.game.num_players
            for i in range(1, self.game.num_players + 1)]
        play_display = ['',]
        for i in play_order:
            display_name = self.game.players[i].name[:max_name_length]
            play_display[0] += CYAN + BOLD + display_name + RESET
            play_display[0] += ' ' * (CribInterface.COL_WIDTH - len(display_name))
        play_display.append('-' * CribInterface.COL_WIDTH * self.game.num_players)
        self.current_display['play'] = play_display
        self.update_display(show_hand=True)


    def show_play(self, current_player, card_played, count, score):
        play_display = self.current_display['play']
        play_order = [(self.game.game_round.crib_player + i) % self.game.num_players
            for i in range(1, self.game.num_players + 1)]

        # remove previous transient lines (turn indicator, count) but keep dividers
        removed = 0
        while removed < 3 and len(play_display) > 2:
            stripped = ANSI_PATTERN.sub('', play_display[-1])
            if stripped.startswith('>>') or stripped.startswith('count'):
                del play_display[-1]
                removed += 1
            elif stripped.startswith('- '):
                break  # stop at divider — it's a permanent separator
            else:
                break

        #the play display is a table with players as columns and successive plays as rows
        #cell to add to table
        play_line = ''
        is_last_card = False
        if card_played:
            play_line += self.colorize_card(card_played)
            if score > 0:
                play_line += YELLOW + ' +%s' % score + RESET
                self.score[current_player] += score
        elif count > 0:
            play_line += ' Go'
        elif score > 0:
            # +1 for last card — append to the previous Go line
            is_last_card = True
            self.score[current_player] += score
            # Find the last play row and append the score to it
            last_row = play_display[-1]
            last_row_stripped = last_row.rstrip()
            play_display[-1] = last_row_stripped + YELLOW + ' +%s' % score + RESET
            # Add divider to mark end of sub-round
            divider_width = CribInterface.COL_WIDTH * self.game.num_players
            play_display.append('- ' * (divider_width // 2))

        if not is_last_card:
            # Calculate visual length (without ANSI codes) for padding
            vis_len = visible_len(play_line)
            play_line += ' ' * (CribInterface.COL_WIDTH - vis_len)

            #put it in the right position
            pos = play_order.index(current_player)
            col_start = CribInterface.COL_WIDTH * pos
            last_row_vis_len = visible_len(play_display[-1])
            if pos == 0 or (card_played and count == card_played.value) or last_row_vis_len > col_start:
                left_pad = ' ' * col_start
                play_display.append(left_pad + play_line)
            else:
                play_display[-1] += play_line

        if not is_last_card:
            #add the count to the end
            count_color = RED if count >= 25 else YELLOW
            count_line = count_color + 'count: %s' % count + RESET
            if count == 31:
                count_line += '  ' + GREEN + '(31!)' + RESET
            play_display.append(count_line)

            # Add divider after 31 to mark end of sub-round
            if count == 31:
                divider_width = CribInterface.COL_WIDTH * self.game.num_players
                play_display.append('- ' * (divider_width // 2))

            # add turn indicator
            next_player = play_order[(play_order.index(current_player) + 1) % len(play_order)]
            turn_name = self.game.players[next_player].name
            if next_player == 0:
                play_display.append(GREEN + '>> Your turn' + RESET)
            else:
                play_display.append(CYAN + ">> %s's turn" % turn_name + RESET)

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

        # Show turn-up card for reference
        turn_up = self.game.game_round.turn_up
        score_lines.append('Turn up: %s' % self.colorize_card(turn_up))
        score_lines.append('')

        play_order = [(self.game.game_round.crib_player + i) % self.game.num_players
            for i in range(1, self.game.num_players + 1)]
        for p in play_order:
            name = CYAN + self.game.players[p].name + RESET
            score_lines.append('%s hand:' % name)
            cards_str = self.colorize_card_str(self.game.players[p].played_cards.cards)
            score_val = YELLOW + str(hand_score[p]) + RESET
            score_lines.append('%s --> %s' % (cards_str, score_val))
            score_lines.append(' ')
            self.score[p] += hand_score[p]
        # Add crib info to the last player's lines
        header_vis_len = visible_len(score_lines[-3])
        padding = max(24 - header_vis_len, 2)
        score_lines[-3] += '%scrib:' % (' ' * padding)

        cards_vis_len = visible_len(score_lines[-2])
        padding2 = max(24 - cards_vis_len, 2)
        crib_cards_str = self.colorize_card_str(self.game.game_round.crib.cards)
        crib_score_val = YELLOW + str(crib_score) + RESET
        score_lines[-2] += '%s%s --> %s' % (' ' * padding2, crib_cards_str, crib_score_val)
        self.score[self.game.game_round.crib_player] += crib_score

        self.current_display['score_lines'] = score_lines
        self.update_display(show_hand=False)
        self.get_input('Press <ENTER> to continue')
        self.reset_display()

    def display_winner(self, winner):
        self.reset_display()
        self.current_display['header'] = self.create_header()
        self.update_display()

        # Show final scores
        self.print_line('')
        self.print_line(BOLD + 'Final Scores:' + RESET)
        for i in range(len(self.game.players)):
            self.print_line('  %s: %s' % (
                CYAN + self.game.players[i].name + RESET,
                YELLOW + str(self.score[i]) + RESET))
        self.print_line('')
        self.print_line(BOLD + GREEN + '%s wins!' % self.game.players[winner].name + RESET)
        self.get_input('Press <ENTER> to continue')
