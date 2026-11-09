"""
마법 탄창 (담당: 표현 주서연)
- 최대 5칸짜리 Stack: 탄을 주우면 push, 발사하면 pop (마지막에 주운 탄이 먼저 나감)
- 재장전: 탄을 전부 pop → algorithms.selection_sort → 다시 push
- Stack 과 selection_sort 는 주서연이 채울 부분 (structures.py, algorithms.py)
"""
import algorithms
from settings import MAGAZINE_SIZE
from structures import Stack
from todo import NotDone

# 탄 세기 (재장전 정렬 기준, 클수록 셈) - TODO(기획 홍정현): 순서 확정
POWER = {"빙결탄": 1, "화염탄": 2, "폭발탄": 3}


class Magazine(Stack):
    """마법총의 탄창. Stack 을 그대로 물려받고 재장전 기능만 추가."""

    def __init__(self):
        super().__init__(MAGAZINE_SIZE)
        self.last_before = []       # 마지막 재장전에서 정렬하기 전 순서 (바닥 → 맨 위)
        self.last_sort_steps = []   # 마지막 재장전의 정렬 단계 (화면의 정렬 애니메이션에 사용)
        self.reload_count = 0       # 재장전 횟수 (화면이 새 재장전을 알아채는 용도)

    def reload(self):
        """
        재장전: 전부 꺼내서 약한 순으로 정렬 후 다시 넣음.
        약한 탄부터 넣으므로 가장 센 탄이 맨 위 → 다음 발사 때 가장 먼저 나감.
        반환: 정렬했으면 True, selection_sort 가 아직 없으면 False (탄창은 그대로)
        """
        bullets = []
        while not self.is_empty():
            bullets.append(self.pop())          # 맨 위부터 꺼냄
        bullets.reverse()                       # 바닥 → 맨 위 순서로 되돌려 둠

        self.last_before = list(bullets)
        done = True
        try:
            self.last_sort_steps = algorithms.selection_sort(bullets, key=lambda b: POWER[b])
        except NotDone:
            done = False                        # 정렬 미구현: 원래 순서 그대로 다시 넣음

        for b in bullets:
            self.push(b)
        if done:
            self.reload_count += 1
        return done
