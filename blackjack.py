# Blackjack simulation

from dataclasses import dataclass, field
import copy
from enum import Enum, auto

# cards are numbers from 1 to 13
# the score is capped at 10

@dataclass
class Hand:
    """Class for representing a blackjack hand."""
    score: int = 0
    soft: bool = False
    cards: [int] = field(default_factory=list)
    doubled: bool = False

    def add_card(self, card):
        hand = self
        if card != 1:  
            if (not hand.soft) or (hand.score <= 11): # simple case
                new_score = min(hand.score+min(10, card), 22) # cap busted hands at 22
            else: # make a soft hand hard
                new_score = hand.score+min(10, card) - 10 
                hand.soft = False
        else: # card is an ace
            if hand.score >= 11: # 11s and up count an ace as 1 (hard or soft)
                new_score = min(hand.score+min(10, card), 22) # cap busted hands at 22
            else: # soft ace
                new_score = hand.score+11
                hand.soft = True

        hand.score = new_score
        hand.cards += [card]
        return hand

def make_hand(cards):
    h = Hand()
    for c in cards:
        h = h.add_card(c)
    return h

def is_busted(hand):
    return hand.score > 21

def is_blackjack(hand):
    return hand.score==21 and len(hand.cards)==2
