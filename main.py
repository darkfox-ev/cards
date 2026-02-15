import sys
from crib import crib
from crib.ai_strategy import RandomStrategy, BasicStrategy, OptimizedStrategy, get_llm_strategies
from interface import interface

if __name__ == '__main__':
    target_score = int(sys.argv[1]) if len(sys.argv) > 1 else 121

    strategies = [RandomStrategy(), BasicStrategy(), OptimizedStrategy()]

    llm_strategies, llm_error = get_llm_strategies()
    strategies.extend(llm_strategies)

    interf = interface.CribInterface()
    try:
        player_name = interf.welcome()
        if llm_error:
            interf.print_line(llm_error)
        strategy = interf.choose_ai(strategies)

        p1 = crib.HumanPlayer(player_name, interf)
        p2 = crib.AI_Player(strategy)

        g = crib.Game(2, [p1, p2], interf, target_score=target_score)
        interf.set_game(g)

        g.play()
    except interface.GameQuitException:
        pass
