from crib import crib
from interface import interface

if __name__ == '__main__':
    interf = interface.CribInterface()
    player_name = interf.welcome()
    
    p1 = crib.HumanPlayer(player_name, interf)
    p2 = crib.AI_Player()
    
    g = crib.Game(2, [p1, p2], interf)
    interf.set_game(g)
    
    g.play()
