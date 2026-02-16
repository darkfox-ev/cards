import sys
import sqlite3
from dotenv import load_dotenv
from crib import crib
from crib.ai_strategy import RandomStrategy, BasicStrategy, OptimizedStrategy, get_llm_strategies
from interface import interface
from logger.logger import create_simulation, complete_simulation

if __name__ == '__main__':
    load_dotenv()
    target_score = int(sys.argv[1]) if len(sys.argv) > 1 else 121

    strategies = [RandomStrategy(), BasicStrategy(), OptimizedStrategy()]

    llm_strategies, llm_error = get_llm_strategies()
    strategies.extend(llm_strategies)

    interf = interface.CribInterface()
    try:
        player_name = interf.welcome()
        if llm_error:
            interf.print_line(llm_error)

        mode = interf.choose_mode()

        if mode == 'play':
            strategy = interf.choose_ai(strategies)

            p1 = crib.HumanPlayer(player_name, interf)
            p2 = crib.AI_Player(strategy)

            g = crib.Game(2, [p1, p2], interf, target_score=target_score)
            interf.set_game(g)

            g.play()

        elif mode == 'simulate':
            config = interf.setup_simulation(strategies)
            num_games = config['num_games']
            sim_target = config['target_score']
            p1_strategy = config['p1_strategy']
            p2_strategy = config['p2_strategy']

            db_path = 'cribbage_log.db'
            conn, sim_id = create_simulation(
                db_path, config['name'], config['description'],
                num_games, p1_strategy.name, p2_strategy.name, sim_target
            )
            conn.close()

            results = {
                'p1_name': p1_strategy.name,
                'p2_name': p2_strategy.name,
                'p1_wins': 0,
                'p2_wins': 0,
                'total': num_games,
            }

            headless_interf = interface.Interface()

            for i in range(1, num_games + 1):
                p1 = crib.AI_Player(p1_strategy, simulate=True)
                p2 = crib.AI_Player(p2_strategy, simulate=True)

                g = crib.Game(2, [p1, p2], headless_interf, target_score=sim_target,
                              simulation_id=sim_id)
                g.play()

                winner = g.score.index(max(g.score))
                if winner == 0:
                    results['p1_wins'] += 1
                else:
                    results['p2_wins'] += 1

                interf.show_simulation_progress(i, num_games, results)

            conn_final = sqlite3.connect(db_path)
            complete_simulation(conn_final, sim_id)

            interf.show_simulation_results(results)

    except interface.GameQuitException:
        pass
