"""
공용 자료구조: 큐(Queue)와 스택(Stack)

★ 팀원이 채울 부분 ★  (각 함수 안의 todo(...) 를 지우고 직접 구현)
  - Queue : 기획 홍정현
  - Stack : 표현 주서연  (카드 더미에서 홍정현도 같이 사용)

규칙 (기획서)
  - collections.deque, queue 모듈 같은 라이브러리 금지 → 파이썬 리스트로 직접 구현
  - 다 채웠으면 터미널에서  python check.py  로 맞게 했는지 확인

이 클래스를 가져다 쓰는 곳 (여기만 채우면 아래는 자동으로 동작)
  - Queue : battle.py (행동 큐), algorithms.py (BFS)
  - Stack : cards.py (카드 더미, 버린 카드), magazine.py (마법 탄창), algorithms.py (큐 뒤집기)
"""
from todo import todo

WHO_QUEUE = "기획 홍정현"
WHO_STACK = "표현 주서연"


class Queue:
    """
    선입선출(FIFO) 큐: 먼저 넣은 것이 먼저 나옴.

    사용 예
        q = Queue(5)              # 최대 5칸
        q.enqueue("앞으로 이동")
        q.enqueue("발사")
        q.dequeue()               # → "앞으로 이동"
        q.to_list()               # → ["발사"]
    """

    def __init__(self, capacity=None):
        self.capacity = capacity  # 최대 개수. None 이면 제한 없음
        # TODO(기획 홍정현): 데이터를 담을 변수 만들기 (예: self.items = [])

    def enqueue(self, item):
        """맨 뒤에 넣기. 꽉 찼으면 넣지 않고 False, 넣었으면 True 반환."""
        todo("Queue.enqueue", WHO_QUEUE)

    def dequeue(self):
        """맨 앞에서 꺼내 반환. 비어 있으면 None 반환."""
        todo("Queue.dequeue", WHO_QUEUE)

    def peek(self):
        """맨 앞 값을 꺼내지 않고 반환. 비어 있으면 None."""
        todo("Queue.peek", WHO_QUEUE)

    def remove_at(self, index):
        """앞에서 index 번째(0부터) 값을 빼서 반환. 계획 중 카드 되돌리기에 씀."""
        todo("Queue.remove_at", WHO_QUEUE)

    def clear(self):
        """전부 비우기."""
        todo("Queue.clear", WHO_QUEUE)

    def is_empty(self):
        """비어 있으면 True."""
        todo("Queue.is_empty", WHO_QUEUE)

    def is_full(self):
        """capacity 만큼 차 있으면 True. capacity 가 None 이면 항상 False."""
        todo("Queue.is_full", WHO_QUEUE)

    def to_list(self):
        """화면 표시용: 앞(front) → 뒤(rear) 순서의 새 리스트 반환."""
        todo("Queue.to_list", WHO_QUEUE)

    def __len__(self):
        """len(q) 로 들어 있는 개수를 알 수 있게."""
        todo("Queue.__len__", WHO_QUEUE)


class Stack:
    """
    후입선출(LIFO) 스택: 마지막에 넣은 것이 먼저 나옴.

    사용 예
        s = Stack(5)              # 최대 5칸 (마법 탄창)
        s.push("화염탄")
        s.push("빙결탄")
        s.pop()                   # → "빙결탄"
        s.to_list()               # → ["화염탄"]
    """

    def __init__(self, capacity=None):
        self.capacity = capacity  # 최대 개수. None 이면 제한 없음
        # TODO(표현 주서연): 데이터를 담을 변수 만들기 (예: self.items = [])

    def push(self, item):
        """맨 위에 올리기. 꽉 찼으면(오버플로) 올리지 않고 False, 올렸으면 True 반환."""
        todo("Stack.push", WHO_STACK)

    def pop(self):
        """맨 위에서 꺼내 반환. 비어 있으면 None 반환."""
        todo("Stack.pop", WHO_STACK)

    def peek(self):
        """맨 위 값을 꺼내지 않고 반환. 비어 있으면 None."""
        todo("Stack.peek", WHO_STACK)

    def clear(self):
        """전부 비우기."""
        todo("Stack.clear", WHO_STACK)

    def is_empty(self):
        """비어 있으면 True."""
        todo("Stack.is_empty", WHO_STACK)

    def is_full(self):
        """capacity 만큼 차 있으면 True. capacity 가 None 이면 항상 False."""
        todo("Stack.is_full", WHO_STACK)

    def to_list(self):
        """화면 표시용: 바닥(bottom) → 맨 위(top) 순서의 새 리스트 반환."""
        todo("Stack.to_list", WHO_STACK)

    def __len__(self):
        """len(s) 로 들어 있는 개수를 알 수 있게."""
        todo("Stack.__len__", WHO_STACK)
