"""
공용 자료구조: 큐(Queue)와 스택(Stack)
  - Queue : 기획 홍정현
  - Stack : 표현 주서연  (카드 더미에서 홍정현도 같이 사용)

규칙 (기획서)
  - collections.deque, queue 모듈 같은 라이브러리 금지 → 파이썬 리스트로 직접 구현
  - 고쳤으면 터미널에서  python check.py  로 확인

이 클래스를 가져다 쓰는 곳
  - Queue : battle.py (행동 큐), algorithms.py (BFS)
  - Stack : cards.py (카드 더미, 버린 카드), magazine.py (마법 탄창), algorithms.py (큐 뒤집기)
"""

WHO_QUEUE = "기획 홍정현"
WHO_STACK = "표현 주서연"


class Queue:
    """
    선입선출(FIFO) 큐: 먼저 넣은 것이 먼저 나옴.
    """

    def __init__(self, capacity=None):
        self.capacity = capacity
        self.items = []

    def enqueue(self, item):
        """맨 뒤에 넣기. 꽉 찼으면 False, 넣었으면 True 반환."""
        if self.is_full():
            return False

        self.items.append(item)
        return True

    def dequeue(self):
        """맨 앞에서 꺼내 반환. 비어 있으면 None 반환."""
        if self.is_empty():
            return None

        return self.items.pop(0)

    def peek(self):
        """맨 앞 값을 꺼내지 않고 반환. 비어 있으면 None."""
        if self.is_empty():
            return None

        return self.items[0]

    def remove_at(self, index):
        """앞에서 index 번째(0부터) 값을 빼서 반환."""
        if index < 0 or index >= len(self.items):
            return None

        return self.items.pop(index)

    def clear(self):
        """전부 비우기."""
        self.items.clear()

    def is_empty(self):
        """비어 있으면 True."""
        return len(self.items) == 0

    def is_full(self):
        """capacity 만큼 차 있으면 True."""
        if self.capacity is None:
            return False

        return len(self.items) >= self.capacity

    def to_list(self):
        """화면 표시용: 앞(front) → 뒤(rear) 순서의 새 리스트 반환."""
        return self.items.copy()

    def __len__(self):
        """len(q) 로 들어 있는 개수를 알 수 있게."""
        return len(self.items)


class Stack:
    """
    후입선출(LIFO) 스택: 마지막에 넣은 것이 먼저 나옴.
    """

    def __init__(self, capacity=None):
        self.capacity = capacity
        self.items = []

    def push(self, item):
        """맨 위에 올리기. 꽉 찼으면 False, 올렸으면 True 반환."""
        if self.is_full():
            return False

        self.items.append(item)
        return True

    def pop(self):
        """맨 위에서 꺼내 반환. 비어 있으면 None 반환."""
        if self.is_empty():
            return None

        return self.items.pop()

    def peek(self):
        """맨 위 값을 꺼내지 않고 반환. 비어 있으면 None."""
        if self.is_empty():
            return None

        return self.items[-1]

    def clear(self):
        """전부 비우기."""
        self.items.clear()

    def is_empty(self):
        """비어 있으면 True."""
        return len(self.items) == 0

    def is_full(self):
        """capacity 만큼 차 있으면 True."""
        if self.capacity is None:
            return False

        return len(self.items) >= self.capacity

    def to_list(self):
        """화면 표시용: 바닥(bottom) → 맨 위(top) 순서의 새 리스트 반환."""
        return self.items.copy()

    def __len__(self):
        """len(s) 로 들어 있는 개수를 알 수 있게."""
        return len(self.items)
