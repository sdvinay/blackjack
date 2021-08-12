# Blackjack simulation

from dataclasses import dataclass, field
from enum import Enum, auto
import copy
import random
from typing import Callable, List, NewType, Sequence, Tuple

# cards are numbers from 1 to 13
# the score is capped at 10
Card = NewType('Card', int)

@dataclass
class HandScore:
    """Class for representing the score of a blackjack hand."""
    points: int = 0
    soft: bool = False

    def __repr__(self) -> str:
        soft_indicator = 's' if self.soft else 'h'
        return(f'{soft_indicator}{self.points:02}')

    def add_card(self, card: Card) -> 'HandScore':
        return add_card(self, card)

def add_card(score: HandScore, card: Card) -> HandScore:
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
    cards: List[int] = field(default_factory=list)
    doubled: bool = False
    drawn: bool = False
    surrendered: bool = False

    def add_card(self, card: Card) -> 'Hand':
        self.score = add_card(self.score, card)
        self.cards += [card]
        return self

    def hit(self, card: Card) -> None:
        self.add_card(card)
        self.drawn = True
    
    def __copy__(self):
        cls = self.__class__
        c = cls.__new__(cls)
        c.__dict__.update(self.__dict__)
        c.cards = copy.copy(self.cards)
        return c

def make_hand(cards: Sequence[Card]) -> Hand:
    h = Hand()
    for c in cards:
        h = h.add_card(c)
    return h

def is_busted(hand: Hand) -> bool:
    return hand.score.points > 21

def is_blackjack(hand: Hand) -> bool:
    return hand.score.points==21 and not hand.drawn



# The Shoe holds the cards and deals them
# For now, just imagine an infinite shoe, where every card is equally likely
# In the future, we can implement specific shoes (e.g, 6-deck, 2-deck, etc)
class Shoe:
    def deal(self) -> Card:
        return Card(random.randrange(13)+1)

## Now define game play


class Action(Enum):
# the order of these doesn't really matter, but ordering from conservative 
# to aggressive works well for heatmaps and the like
    SURRENDER = auto()
    STAND = auto()
    HIT = auto()
    DOUBLE = auto()
    #SPLIT = auto()

DecFuncType = Callable[[HandScore, HandScore], Action]

class Strategy:
    def decide(self, score_p: HandScore, score_d: HandScore) -> Action:
        pass

    def __init__(self, name: str):
        self.__name__ = name
    
    def __repr__(self) -> str:
        return self.__name__

class Strategy_wrapper(Strategy):
    # Need to point to the decision func, so use a list to wrap it
    decision_func: List[DecFuncType] = field(default_factory=list)
    def decide(self, score_p: HandScore, score_d: HandScore) -> Action:
        return self.decision_func[0](score_p, score_d)
    
    def __init__(self, dec_func: DecFuncType):
        Strategy.__init__(self, dec_func.__name__)
        self.decision_func = [dec_func]
    
# Most simple/conservative strategy imaginable:
def strat_nobust_func(score_p: HandScore, _: HandScore) -> Action:
    if score_p.points > 11:
        return Action.STAND
    else:
        return Action.HIT
        
strat_nobust = Strategy_wrapper(strat_nobust_func)

# Dealer strategy
def strat_dealer_func(score_p: HandScore, _: HandScore) -> Action:
    if score_p.points < 17:
        return Action.HIT
    if score_p.points == 16 and score_p.soft:
        return Action.HIT
    else:
        return Action.STAND
    
strat_dealer = Strategy_wrapper(strat_dealer_func)
        
class HandOutcome(Enum):
    WIN = 1
    LOSE = -1
    WIN_DOUBLE = 2
    LOSE_DOUBLE = -2
    PUSH = 0
    BLACKJACK = 1.5
    SURRENDER = -.5

# return the final hand after playing
def player_play_hand(strategy: Strategy, hand_p: Hand, hand_d: Hand, shoe: Shoe) -> Hand:
    while True:
        decision = strategy.decide(hand_p.score, hand_d.score)
        if decision == Action.STAND:
            return hand_p
        if decision == Action.SURRENDER:
            hand_p.surrendered = True
            return hand_p
        if decision == Action.DOUBLE and not hand_p.drawn:
            hand_p.doubled = True
            hand_p.hit(shoe.deal())
            return hand_p
        if decision in [Action.HIT, Action.DOUBLE]:
            hand_p.hit(shoe.deal())
            if is_busted(hand_p):
                return hand_p

# First compute the initial outcome, then double it if necessary for a double-down
def __initial_outcome(player_hand: Hand, dealer_hand: Hand) -> HandOutcome:
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
    #if player_hand.score.points < dealer_hand.score.points:
    return HandOutcome.LOSE

__outcome_doubler = {HandOutcome.WIN: HandOutcome.WIN_DOUBLE, HandOutcome.LOSE: HandOutcome.LOSE_DOUBLE}


def player_hand_outcome(player_hand: Hand, dealer_hand: Hand) -> HandOutcome:
    # First compute the initial outcome, then double it if necessary for a double-down
    outcome = __initial_outcome(player_hand, dealer_hand)
    if player_hand.doubled:
        outcome = __outcome_doubler.get(outcome) or outcome

    return outcome
        
def get_strat_name(strat: Strategy) -> str:
    if hasattr(strat, '__name__'):
        return strat.__name__
    return repr(strat)
    
# Goal is to evaluate strategies, so make comparisons simple

# For each round:
# Multiple players all play with a copy of the same starting hand
# Each player has a strategy that they play
# Dealer plays dealer strategy

# For now, we're using an infinite deck and strategies without knowledge, so
# the interaction of players/strategies should be a wash

def deal_one_round(shoe: Shoe) -> Tuple[Hand, Hand, Card]:
    hand_p = Hand()
    hand_d = Hand()

    hand_p.add_card(shoe.deal())
    hand_d.add_card(shoe.deal())
    hand_p.add_card(shoe.deal())
    
    dealer_hole_card = shoe.deal()
    
    return hand_p, hand_d, dealer_hole_card

class StatefulShoe(Shoe):
    cards: List[Card]
    def deal(self) -> Card:
        return self.cards.pop()

    def __init__(self, cards: List[Card]) -> None:
        super().__init__()
        self.cards = cards
    
    def __copy__(self) -> 'StatefulShoe':
        cls = self.__class__
        c = cls.__new__(cls)
        c.__dict__.update(self.__dict__)
        c.cards = copy.copy(self.cards)
        return c

# Play multiple strategies on one starting point
def complete_one_round(strats: Sequence[Strategy], player_hand: Hand, dealer_hand: Hand, dealer_hole_card: Card, shoe: Shoe):
    hand_p = player_hand
    hand_d = copy.copy(dealer_hand)

    # represent each player as a hand and a strategy
    # each player gets the same set of cards to draw
    cards = [shoe.deal() for _ in range(10)]
    this_shoe = StatefulShoe(cards)
    players = [(player_play_hand(strat, copy.copy(hand_p), hand_d, copy.copy(this_shoe)), get_strat_name(strat)) for strat in strats]
    
    # dealer
    player_play_hand(strat_dealer, hand_d.add_card(dealer_hole_card), Hand(), shoe)
    
    return [(strat, hand_p, hand_d, player_hand_outcome(hand_p, hand_d)) for (hand_p, strat) in players]

    
def play_one_round(strats: Sequence[Strategy], shoe: Shoe = Shoe()):
    hand_p, hand_d, dealer_hole_card = deal_one_round(shoe)
    return complete_one_round(strats, hand_p, hand_d, dealer_hole_card, shoe)

