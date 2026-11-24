"""
카드와 카드 더미 (담당: 기획)
- 카드는 이름 문자열로 표현 (예: "앞으로 이동")
- 카드 더미와 버린 카드는 둘 다 Stack: 맨 위에서만 뽑고, 쓴 카드는 위에 쌓임
- 매 턴 손패 = 기본 카드 2장(앞으로 이동 + 회전 1장) + 더미에서 뽑은 4장
  기본 카드는 더미 밖에서 매번 새로 받는 카드라 다 쓰면 사라짐 (버린 카드로 안 감)
"""
import random

from structures import Stack

# 카드 종류와 더미에 들어가는 장수 (총 15장)
# 앞으로 이동 + 회전 카드 1장은 매 턴 '기본 카드'로 따로 받으므로, 더미에서 뽑히는 장수만 적음
# 뒤로 이동, 재장전은 자주 나오면 답답해서 1장씩만
CARD_COUNTS = {
    "앞으로 이동": 3,
    "2칸 앞으로": 2,     # 가끔 나오는 강한 이동 카드
    "왼쪽 보기": 2,
    "오른쪽 보기": 2,
    "발사": 4,
    "뒤로 이동": 1,
    "재장전": 1,
}
CARD_TYPES = list(CARD_COUNTS)
TURN_CARDS = ["왼쪽 보기", "오른쪽 보기"]

# 카드에 적는 영어 이름 (중세 보드게임 느낌, Cinzel Decorative 글꼴로 씀)
CARD_EN = {
    "앞으로 이동": "Advance", "2칸 앞으로": "Dash", "왼쪽 보기": "Turn Left", "오른쪽 보기": "Turn Right",
    "발사": "Fire", "뒤로 이동": "Retreat", "재장전": "Reload", "기절": "Stunned",
}


def card_en(name):
    """카드 이름(한글) → 카드에 적는 영어 이름."""
    return CARD_EN.get(name, name)


class Deck:
    """카드 더미(draw_pile)와 버린 카드(discard), 두 개의 스택."""

    def __init__(self):
        self.draw_pile = Stack()
        self.discard = Stack()
        cards = []
        for name, count in CARD_COUNTS.items():
            cards += [name] * count
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
