"""
카드와 카드 더미 (담당: 기획 홍정현)
- 카드는 이름 문자열로 표현 (예: "앞으로 이동")
- 카드 더미와 버린 카드는 둘 다 Stack: 맨 위에서만 뽑고, 쓴 카드는 위에 쌓임
"""
import random

from structures import Stack

# 카드 6종 (기획서 4-2)
CARD_TYPES = ["앞으로 이동", "뒤로 이동", "왼쪽 보기", "오른쪽 보기", "발사", "재장전"]
COPIES = 3  # 종류마다 3장씩, 총 18장


class Deck:
    """카드 더미(draw_pile)와 버린 카드(discard), 두 개의 스택."""

    def __init__(self):
        self.draw_pile = Stack()
        self.discard = Stack()
        cards = CARD_TYPES * COPIES
        random.shuffle(cards)   # 섞기는 필수 알고리즘이 아니라 라이브러리 사용
        for card in cards:
            self.draw_pile.push(card)

    def draw(self, n):
        """카드 더미 맨 위에서 n장 뽑기. 더미가 비면 버린 카드를 섞어서 다시 더미로."""
        hand = []
        for _ in range(n):
            if self.draw_pile.is_empty():
                self.reshuffle()
            card = self.draw_pile.pop()
            if card is None:    # 더미와 버린 카드가 모두 비었을 때
                break
            hand.append(card)
        return hand

    def discard_cards(self, cards):
        """쓴 카드/남은 손패를 버린 카드 맨 위에 쌓기."""
        for card in cards:
            self.discard.push(card)

    def reshuffle(self):
        """버린 카드를 전부 꺼내 섞은 뒤 카드 더미에 다시 쌓기."""
        cards = []
        while not self.discard.is_empty():
            cards.append(self.discard.pop())
        random.shuffle(cards)
        for card in cards:
            self.draw_pile.push(card)
