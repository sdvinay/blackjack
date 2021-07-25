import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

import blackjack as bj
import simulator as sim

def run_iteration(n, strat_base, previous_instructions):
    comput = sim.compute_instructions(n, strat_base)
    outputs = pd.DataFrame(comput).set_index(['score_p', 'score_d'])
    
    instructions = {(output['score_p'], output['score_d']): output['winning_act'] for output in comput}
    
    fig = plt.figure()
    # Visualize the winning action by starting condition
    sns.heatmap(outputs['winning_act'].apply(lambda x: x.value).unstack(), ax=fig.add_subplot(1, 2, 1))
    
    # Visualize the average outcome by starting condition
    sns.heatmap(outputs['winning_act_outcome'].unstack(), ax=fig.add_subplot(1, 2, 2))
    
    if previous_instructions:
        for k in instructions:
            if instructions[k] != previous_instructions[k]:
                print(k, instructions[k], previous_instructions[k])
    
    return instructions

# Memoized strategy
# Rather than generic conditions, just use an array indexed on player and dealer scores
# Since that's how we're generating our strategy anyway (one square at a time)

class Strat_memoized(bj.Strategy):
    instructions = None
    strat_base = None

    def decide(self, score_p, score_d):
        k = (repr(score_p), repr(score_d))
        if k in self.instructions:
            return self.instructions[k]
        else:
            return self.strat_base.decide(score_p, score_d)

    def __init__(self, strat_base, instructions):
        bj.Strategy.__init__(self, 'memoized')
        self.strat_base = strat_base
        self.instructions = instructions

def gen_strat_memoized(instructions, strat_base):
    return Strat_memoized(strat_base, instructions)

def derive_iterative_strategies(strat_base, iterations):
    n = 50
    previous_instructions = None
    strategies = [strat_base]

    for i in range(iterations):
        print(i)
        instructions = run_iteration(n, strat_base, previous_instructions)
        strat_new  = gen_strat_memoized(instructions, strat_base)
        strat_new.name = f'iter({i+1})'
        strategies.append(strat_new)
        previous_instructions = instructions
        strat_base = strat_new
        n = n*3

    return strategies
