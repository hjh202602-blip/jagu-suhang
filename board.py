"""
격자 맵과 유닛 (담당: 개발 김보민)
- 10x10 격자를 2차원 리스트(tiles[r][c])로 관리
- 플레이어, 적, 바닥에 놓인 탄의 위치를 들고 있음
- 적 추격 경로는 algorithms.bfs_path 에 맡김 (← 김보민이 채울 부분)
좌표는 항상 (c, r) = (가로 칸, 세로 칸) 순서
"""
import random

import algorithms
from settings import N, MAX_HP

# 타일 종류 (stages.py 맵 문자와 같음)
FLOOR, WALL, EXIT, FLIP = ".", "#", "X", "R"
# 맵 문자 → 탄 이름
ITEM_CHARS = {"f": "화염탄", "i": "빙결탄", "b": "폭발탄"}


class Player:
    """주인공(견습 마법사). 바라보는 방향으로만 쏠 수 있음."""

    def __init__(self, pos):
        self.pos = pos
        self.facing = 0     # settings.DIRS 인덱스 (0 위, 1 오른쪽, 2 아래, 3 왼쪽)
        self.hp = MAX_HP


class Enemy:
    """적. kind 가 'chaser' 면 BFS로 추격, 'dummy'(허수아비) 면 제자리."""

    def __init__(self, pos, kind):
        self.pos = pos
        self.kind = kind
        self.hp = 2 if kind == "chaser" else 1
        self.frozen = 0     # 빙결탄에 맞으면 남은 정지 턴 수
        self.steps = 0      # 이번 턴에 다가올 칸 수 (머리 위 숫자)
        self.trail = []     # 지난 적 차례에 지나간 칸들 (이동 애니메이션용)

    def roll_steps(self):
        """턴 시작마다 이동 칸 수를 1~3 중 랜덤으로 정함. 허수아비나 얼어 있는 적은 0."""
        if self.kind == "dummy" or self.frozen > 0:
            self.steps = 0
        else:
            self.steps = random.randint(1, 3)


class Board:
    """한 스테이지의 격자 상태."""

    def __init__(self, stage_map):
        self.tiles = []     # tiles[r][c] : FLOOR / WALL / EXIT / FLIP
        self.items = {}     # (c, r) → 바닥에 놓인 탄 이름
        self.enemies = []
        self.player = None

        # 맵 문자열을 읽어 타일과 유닛으로 나눔
        for r, row in enumerate(stage_map):
            tile_row = []
            for c, ch in enumerate(row):
                pos = (c, r)
                if ch == "P":
                    self.player = Player(pos)
                elif ch == "E":
                    self.enemies.append(Enemy(pos, "chaser"))
                elif ch == "D":
                    self.enemies.append(Enemy(pos, "dummy"))
                elif ch in ITEM_CHARS:
                    self.items[pos] = ITEM_CHARS[ch]
                # 유닛과 탄이 있던 칸은 바닥으로 취급
                tile_row.append(ch if ch in (WALL, EXIT, FLIP) else FLOOR)
            self.tiles.append(tile_row)

    # ---------- 칸 조회 ----------
    def in_bounds(self, pos):
        c, r = pos
        return 0 <= c < N and 0 <= r < N

    def tile(self, pos):
        c, r = pos
        return self.tiles[r][c]

    def set_tile(self, pos, kind):
        c, r = pos
        self.tiles[r][c] = kind

    def is_wall(self, pos):
        return self.tile(pos) == WALL

    def enemy_at(self, pos):
        """그 칸에 있는 적을 반환, 없으면 None."""
        for e in self.enemies:
            if e.pos == pos:
                return e
        return None

    def remove_dead(self):
        """체력이 0 이하인 적을 격자에서 제거."""
        self.enemies = [e for e in self.enemies if e.hp > 0]

    # ---------- 탐색 ----------
    def bfs_path(self, start, goal, blocked=()):
        """
        적 추격용 최단 경로. "지나갈 수 있는 칸" 규칙만 정해서 algorithms.bfs_path 에 넘김.
        blocked: 다른 적 위치처럼 이번에만 막힌 칸들
        """
        def can_pass(pos):
            return self.in_bounds(pos) and not self.is_wall(pos) and pos not in blocked

        return algorithms.bfs_path(start, goal, can_pass)
