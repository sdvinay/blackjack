import random
from typing import Sequence

import blackjack as bj


# Models a real-life multi-deck shoe, which is re-shuffled periodically
# Implemented by creating a DisposableShoe on every shuffle(), and dealing from that DisposableShoe
# For now, requires shuffle() to be called on it; there is no check on remaining cards implemented

class StatefulShoe(bj.Shoe):
    num_decks = 8
    __shoe: bj.DisposableShoe
    def __init__(self) -> None:
        super().__init__()
        self.shuffle()

    def shuffle(self) -> None:
        cards = list(range(1, 14))*4*self.num_decks
        random.shuffle(cards)
        self.__shoe = bj.DisposableShoe(cards)

    def deal(self) -> bj.Card:
        return self.__shoe.deal()

    def cards(self) -> Sequence[bj.Card]:
        return self.__shoe.cards