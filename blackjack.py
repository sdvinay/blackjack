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

    def add_card(self, card):
        self.score = add_card(self.score, card)
        self.cards += [card]
        return self

def make_hand(cards):
    h = Hand()
    for c in cards:
        h = h.add_card(c)
    return h

def is_busted(hand):
    return hand.score.points > 21

def is_blackjack(hand):
    return hand.score.points==21 and len(hand.cards)==2


## Now define game play


# TODO I might want a Flag class later, to provide a set of possible Actions
class Action(Enum):
    STAND = auto()
    HIT = auto()
    DOUBLE = auto()
    #SPLIT = auto()
    
# Most simple/conservative strategy imaginable:
def strat_nobust(score_p, _):
    if score_p.points > 11:
        return Action.STAND
    else:
        return Action.HIT
        
strat_nobust.name = 'strat_nobust'

# Dealer strategy
def strat_dealer(score_p, _):
    if score_p.points < 17:
        return Action.HIT
    if score_p.points == 16 and score_p.soft:
        return Action.HIT
    else:
        return Action.STAND
    
strat_dealer.name='strat_dealer'
        
class HandOutcome(Enum):
    WIN = 1
    LOSE = -1
    WIN_DOUBLE = 2
    LOSE_DOUBLE = -2
    PUSH = 0
    BLACKJACK = 1.5


# Deck; completely random (i.e., infinite) for now

def deal_card():
    return random.randrange(13)+1

# return the final hand after playing
def player_play_hand(strategy, hand_p, hand_d, deck):
    while True:
        decision = strategy(hand_p.score, hand_d.score)
        if decision == Action.STAND:
            return hand_p
        if decision == Action.HIT:
            hand_p.add_card(deck())
            if is_busted(hand_p):
                return hand_p
        if decision == Action.DOUBLE:
            hand_p.doubled = True
            hand_p.add_card(deck())
            return hand_p


def player_hand_outcome(player_hand, dealer_hand):
    # First compute the initial outcome, then double it if necessary for a double-down
    def initial_outcome():
        if is_blackjack(player_hand):
            if is_blackjack(dealer_hand):
                return HandOutcome.PUSH
            else:
                return HandOutcome.BLACKJACK
        if is_busted(player_hand) or is_blackjack(dealer_hand):
            return HandOutcome.LOSE
        if is_busted(dealer_hand):
            return HandOutcome.WIN
        if player_hand.score.points > dealer_hand.score.points:
            return HandOutcome.WIN
        if player_hand.score.points == dealer_hand.score.points:
            return HandOutcome.PUSH
        if player_hand.score.points < dealer_hand.score.points:
            return HandOutcome.LOSE

    outcome = initial_outcome()

    outcome_doubler = {HandOutcome.WIN: HandOutcome.WIN_DOUBLE, HandOutcome.LOSE: HandOutcome.LOSE_DOUBLE}

    if player_hand.doubled:
        outcome = outcome_doubler.get(outcome) or outcome
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
    hand_p = copy.deepcopy(player_hand)
    hand_d = copy.deepcopy(dealer_hand)
    
    # represent each player as a hand and a strategy
    players = [(player_play_hand(strat, copy.deepcopy(hand_p), hand_d, deal_card), get_strat_name(strat)) for strat in strats]
    
    # dealer
    player_play_hand(strat_dealer, hand_d.add_card(dealer_hole_card), Hand(), deal_card)
    
    return [(strat, hand_p, hand_d, player_hand_outcome(hand_p, hand_d)) for (hand_p, strat) in players]

    
def play_one_round(strats):
    hand_p, hand_d, dealer_hole_card = deal_one_round()
    return complete_one_round(strats, hand_p, hand_d, dealer_hole_card)

