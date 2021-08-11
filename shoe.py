import blackjack as bj
import random

# Models a real-life multi-deck shoe, which is re-shuffled periodically
# Implemented by creating a DisposableShoe on every shuffle(), and dealing from that DisposableShoe
# For now, requires shuffle() to be called on it; there is no check on remaining cards implemented

class StatefulShoe(bj.Shoe):
    num_decks = 8
    shoe: bj.DisposableShoe
    def __init__(self) -> None:
        super().__init__()
        self.shuffle()

    def shuffle(self) -> None:
        cards = list(range(1, 14))*4*self.num_decks
        random.shuffle(cards)
        self.shoe = bj.DisposableShoe(cards)

    def deal(self) -> bj.Card:
        return self.shoe.deal()
