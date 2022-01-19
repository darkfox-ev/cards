import sys, os, colorama, time, random

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


    def text_blit(self, text, x=1, y=None, fore_colour=None, back_colour=None):
        fc = u'\u001b[3' + str(COLORS[fore_colour]) + 'm' if fore_colour else ''
        bc = u'\u001b[4' + str(COLORS[back_colour]) + 'm' if back_colour else ''
        
        if y is None:
            y = self.current_row
            self.current_row += 1

        sys.stdout.write(u'\u001b[{};{}H{}{}{}'.format(y, x, fc, bc, text))


    def get_input(self, msg):
        self.text_blit(msg, x=1, y=self.height -1)
        self.text_blit(">>> ", x=1, y=self.height)
        
        msg_response = input()


class Interface:
    def __init__(self):
        self.terminal = Terminal()
        self.terminal.clear_screen()
        

    def print_line(self, text):
        self.terminal.text_blit(text)

    