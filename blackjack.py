# Blackjack simulation

from dataclasses import dataclass, field
import copy
from enum import Enum, auto

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
