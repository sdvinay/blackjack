# Blackjack simulation

from dataclasses import dataclass, field
from enum import Enum, auto
import copy
import random

# cards are numbers from 1 to 13
# the score is capped at 10

@dataclass
class HandScore:
    """Class for representing the score of a blackjack hand."""
    points: int = 0
    soft: bool = False

    def __repr__(self):
        soft_indicator = 's' if self.soft else 'h'
        return(f'{soft_indicator}{self.points:02}')

    def add_card(self, card):
        return add_card(self, card)

def add_card(score, card):
    hand = score
    if card != 1:  
        if (not hand.soft) or (hand.points <= 11): # simple case
            new_score = HandScore(min(hand.points+min(10, card), 22), hand.soft) # cap busted hands at 22
        else: # make a soft hand hard
            new_score = HandScore(hand.points+min(10, card) - 10)
    else: # card is an ace
        if hand.points >= 11: # 11s and up count an ace as 1 (hard or soft)
            new_score = HandScore(min(hand.points+min(10, card), 22), hand.soft) # cap busted hands at 22
        else: # soft ace
            new_score = HandScore(hand.points+11, True)

    return new_score


@dataclass
class Hand:
    """Class for representing a blackjack hand."""
    score: HandScore = HandScore(0, False)
    cards: [int] = field(default_factory=list)
    doubled: bool = False
    drawn: bool = False
    surrendered: bool = False

    def add_card(self, card):
        self.score = add_card(self.score, card)
        self.cards += [card]
        return self
    
    def __copy__(self):
        cls = self.__class__
        c = cls.__new__(cls)
        c.__dict__.update(self.__dict__)
        c.cards = copy.copy(self.cards)
        return c

def make_hand(cards):
    h = Hand()
    for c in cards:
        h = h.add_card(c)
    return h

def is_busted(hand):
    return hand.score.points > 21

def is_blackjack(hand):
    return hand.score.points==21 and not hand.drawn


## Now define game play


# TODO I might want a Flag class later, to provide a set of possible Actions
class Action(Enum):
# the order of these doesn't really matter, but ordering from conservative 
# to aggressive works well for heatmaps and the like
    SURRENDER = auto()
    STAND = auto()
    HIT = auto()
    DOUBLE = auto()
    #SPLIT = auto()

class Strategy:
    def decide(self, score_p, score_d):
        pass

    name = ''

    def __init__(self, name):
        self.name = name

class Strategy_wrapper(Strategy):
    decision_func = None
    def decide(self, score_p, score_d):
        return self.decision_func(score_p, score_d)
    
    def __init__(self, dec_func):
        Strategy.__init__(self, dec_func.name)
        self.decision_func = dec_func
    
# Most simple/conservative strategy imaginable:
def strat_nobust_func(score_p, _):
    if score_p.points > 11:
        return Action.STAND
    else:
        return Action.HIT
        
strat_nobust_func.name = 'strat_nobust'

strat_nobust = Strategy_wrapper(strat_nobust_func)

# Dealer strategy
def strat_dealer_func(score_p, _):
    if score_p.points < 17:
        return Action.HIT
    if score_p.points == 16 and score_p.soft:
        return Action.HIT
    else:
        return Action.STAND
    
strat_dealer_func.name='strat_dealer'
        
class HandOutcome(Enum):
    WIN = 1
    LOSE = -1
    WIN_DOUBLE = 2
    LOSE_DOUBLE = -2
    PUSH = 0
    BLACKJACK = 1.5
    SURRENDER = -.5

strat_dealer = Strategy_wrapper(strat_dealer_func)

# Deck; completely random (i.e., infinite) for now

def deal_card():
    return random.randrange(13)+1

# return the final hand after playing
def player_play_hand(strategy, hand_p, hand_d, deck):
    while True:
        decision = strategy.decide(hand_p.score, hand_d.score)
        if decision == Action.STAND:
            return hand_p
        if decision == Action.SURRENDER:
            hand_p.surrendered = True
            return hand_p
        if decision == Action.DOUBLE and not hand_p.drawn:
            hand_p.doubled = True
            hand_p.add_card(deck())
            hand_p.drawn = True
            return hand_p
        if decision in [Action.HIT, Action.DOUBLE]:
            hand_p.add_card(deck())
            hand_p.drawn = True
            if is_busted(hand_p):
                return hand_p

# First compute the initial outcome, then double it if necessary for a double-down
def __initial_outcome(player_hand, dealer_hand):
    if is_blackjack(player_hand):
        if is_blackjack(dealer_hand):
            return HandOutcome.PUSH
        else:
            return HandOutcome.BLACKJACK
    if is_busted(player_hand) or is_blackjack(dealer_hand):
        return HandOutcome.LOSE
    if player_hand.surrendered:
        return HandOutcome.SURRENDER
    if is_busted(dealer_hand):
        return HandOutcome.WIN
    if player_hand.score.points > dealer_hand.score.points:
        return HandOutcome.WIN
    if player_hand.score.points == dealer_hand.score.points:
        return HandOutcome.PUSH
    if player_hand.score.points < dealer_hand.score.points:
        return HandOutcome.LOSE

__outcome_doubler = {HandOutcome.WIN: HandOutcome.WIN_DOUBLE, HandOutcome.LOSE: HandOutcome.LOSE_DOUBLE}


def player_hand_outcome(player_hand, dealer_hand):
    # First compute the initial outcome, then double it if necessary for a double-down
    outcome = __initial_outcome(player_hand, dealer_hand)
    if player_hand.doubled:
        outcome = __outcome_doubler.get(outcome) or outcome

    return outcome
        
def get_strat_name(strat):
    if hasattr(strat, 'name'):
        return strat.name
    return repr(strat)
    
# Goal is to evaluate strategies, so make comparisons simple

# For each round:
# Multiple players all play with a copy of the same starting hand
# Each player has a strategy that they play
# Dealer plays dealer strategy

# For now, we're using an infinite deck and strategies without knowledge, so
# the interaction of players/strategies should be a wash

def deal_one_round():
    hand_p = Hand()
    hand_d = Hand()

    hand_p.add_card(deal_card())
    hand_d.add_card(deal_card())
    hand_p.add_card(deal_card())
    
    dealer_hole_card = deal_card()
    
    return hand_p, hand_d, dealer_hole_card


# Play multiple strategies on one starting point
def complete_one_round(strats, player_hand, dealer_hand, dealer_hole_card):
    hand_p = player_hand
    hand_d = copy.copy(dealer_hand)
    
    # represent each player as a hand and a strategy
    players = [(player_play_hand(strat, copy.copy(hand_p), hand_d, deal_card), get_strat_name(strat)) for strat in strats]
    
    # dealer
    player_play_hand(strat_dealer, hand_d.add_card(dealer_hole_card), Hand(), deal_card)
    
    return [(strat, hand_p, hand_d, player_hand_outcome(hand_p, hand_d)) for (hand_p, strat) in players]

    
def play_one_round(strats):
    hand_p, hand_d, dealer_hole_card = deal_one_round()
    return complete_one_round(strats, hand_p, hand_d, dealer_hole_card)

