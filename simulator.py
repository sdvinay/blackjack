from typing import Dict, Sequence, Tuple
import pandas as pd

import blackjack as bj
from blackjack import Hand, HandOutcome, HandScore, Action, Strategy, make_hand


def generate_row_from_player(player: Tuple[Strategy, Hand, Hand, HandOutcome]) -> Dict:
    (strat, hand_p, hand_d, outcome) = player
    return {'strategy': strat, 'hand_start': hand_p.cards[:2], 'dealer_card': hand_d.cards[0], 'hand_end': hand_p.cards, 'dealer_hand': hand_d.cards, 'outcome': outcome}

def generate_rows_from_round(r):
    return [generate_row_from_player(player) for player in r]

def run_n_sim_trials(strats: Sequence[Strategy], n: int) -> pd.DataFrame:
    sims = [generate_rows_from_round(bj.play_one_round(strats, bj.Shoe())) for _ in range(n)]
    results = pd.DataFrame([player for round in sims for player in round])
    results['outcome_value'] = results['outcome'].apply(lambda x: x.value)
    results['outcome_name'] = results['outcome'].apply(lambda x: str(x)[12:])
    return results

# TODO reduce duplication with run_n_sim_trials
def run_n_sim_trials_from_state(strats: Sequence[Strategy], hand_p: Hand, hand_d: Hand, n: int) -> pd.DataFrame:
    sims = [generate_rows_from_round(bj.complete_one_round(strats, hand_p, hand_d, bj.Shoe().deal(), bj.Shoe())) for _ in range(n)]
    results = pd.DataFrame([player for round in sims for player in round])
    results['outcome_value'] = results['outcome'].apply(lambda x: x.value)
    results['outcome_name'] = results['outcome'].apply(lambda x: str(x)[12:])
    return results

def summarize_totals(sims: pd.DataFrame) -> pd.DataFrame:
    def outcome_name(x): return x.head(1) # The function name will be used as the column name
    outcome_counts = sims.groupby(['strategy', 'outcome_value'])['outcome_name'].agg([len, outcome_name])
    outcome_summary = outcome_counts.reset_index().set_index('strategy').drop(['outcome_value'], axis=1).pivot(columns=['outcome_name'])

    # The empty cells are NaNs; fill the NaNs and convert back to int
    for col in outcome_summary.columns:
        outcome_summary[col] = outcome_summary[col].fillna(0).apply(int)
        
    outcome_summary['mean_outcome'] = sims.groupby('strategy')['outcome_value'].mean()
    
    return outcome_summary

def generate_strat_conditional(strat_base: Strategy, conditions: Sequence) -> Strategy:
    def strat_cond(score_p, score_d):
        for (condition, action) in conditions:
            if condition(score_p, score_d): return action
        return strat_base.decide(score_p, score_d)
    strat_cond.__name__ = 'strat_cond'
    return bj.Strategy_wrapper(strat_cond)


def gen_cond_strategies(strat_base, condition, actions):
    def gen_strat_action(strat_base, condition, action):
        strat = generate_strat_conditional(strat_base, [(condition, action)])
        strat.__name__ = repr(action)
        return strat
    
    strats = [gen_strat_action(strat_base, condition, a) for a in actions]
    return strats


def strat_simple_func(score_p, score_d):
    if score_p.points == 11:  return Action.DOUBLE
    if score_p.points >= 17:  return Action.STAND
    if score_p.points <= 11:  return Action.HIT
    if score_d.points in (range(3,7)):  return Action.STAND
    else:  return Action.HIT
        
strat_simple = bj.Strategy_wrapper(strat_simple_func)

def test_cond(score_p, score_d, n, strat_base = strat_simple):
    def cond(p, d):
        return p == score_p and d == score_d
    strats = gen_cond_strategies(strat_base, cond, Action)
    hand_p = Hand(score_p) 
    hand_d = make_hand([score_d.points if score_d.points< 11 else 1])
    sims = run_n_sim_trials_from_state(strats, hand_p, hand_d, n)
    return cond, summarize_totals(sims)

def find_winning_action(score_p, score_d, n, strat_base = strat_simple):
    cond, summary = test_cond(score_p, score_d, n, strat_base)
    outcomes = summary['mean_outcome']
    # Find the winning strategy
    winner = outcomes[outcomes==outcomes.max()].index[0]
    winning_act = [a for a in Action if repr(a)==winner][0]

    # Convert results to a dict
    output = outcomes.to_dict()
    output['score_p'] = repr(score_p)
    output['score_d'] = repr(score_d)
    output['winning_act'] = winning_act
    output['winning_act_outcome'] = outcomes.max()

    return output

def compute_instructions(n, strat_base = strat_simple):
    all_scores = [HandScore(i, False) for i in range(0, 23)] + [HandScore(i, True) for i in range(11, 22)]
    return [find_winning_action(p, make_hand([d]).score, n, strat_base) for p in all_scores for d in range(1, 11) if p.points>=9]


