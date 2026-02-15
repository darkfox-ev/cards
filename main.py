import sys
from crib import crib
from crib.ai_strategy import RandomStrategy, BasicStrategy, OptimizedStrategy, LLMStrategy
from interface import interface

if __name__ == '__main__':
    target_score = int(sys.argv[1]) if len(sys.argv) > 1 else 121

    strategies = [RandomStrategy(), BasicStrategy(), OptimizedStrategy(), LLMStrategy()]

    interf = interface.CribInterface()
    player_name = interf.welcome()
    strategy = interf.choose_ai(strategies)

    p1 = crib.HumanPlayer(player_name, interf)
    p2 = crib.AI_Player(strategy)

    g = crib.Game(2, [p1, p2], interf, target_score=target_score)
    interf.set_game(g)

    g.play()
