"""
그림 에셋 (담당: 표현 주서연)

★ 팀원이 채울 부분 ★
  지금은 글자로 된 임시 그림. 진짜 그림으로 바꾸는 방법은 두 가지:
    1) 쉬운 방법: assets/images/ 폴더에 아래 IMAGE_FILES 이름대로 PNG 를 넣기
       → 파일이 있으면 자동으로 그 그림을 씀 (칸 크기 46x46 에 맞춰 늘리거나 줄임)
    2) 직접 그리기: 아래 draw_... 함수 안의 "임시 그림" 부분을 pygame.draw 로 바꾸기

scenes.py 는 격자·카드를 그릴 때 이 파일의 draw_... 함수만 부름.
그래서 여기만 고치면 게임 전체 그림이 바뀜. 함수 이름과 매개변수는 그대로 둘 것.
"""
import os

import pygame

from settings import WALL_COLOR, FLIP_COLOR, DIR_ARROWS
from ui import box, label

IMAGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "images")

# 그림 이름 → 파일 이름. 이 이름으로 assets/images/ 에 넣으면 자동 적용
IMAGE_FILES = {
    # 타일
    "wall": "wall.png",
    "exit": "exit.png",
    "flip": "flip.png",
    # 유닛 (player.png 는 '위를 보는' 그림으로. 방향에 따라 자동으로 돌려서 씀)
    "player": "player.png",
    "chaser": "chaser.png",
    "dummy": "dummy.png",
    # 바닥의 탄
    "화염탄": "bullet_fire.png",
    "빙결탄": "bullet_ice.png",
    "폭발탄": "bullet_bomb.png",
    # 카드 (카드 크기 100x115)
    "앞으로 이동": "card_forward.png",
    "뒤로 이동": "card_back.png",
    "왼쪽 보기": "card_turn_left.png",
    "오른쪽 보기": "card_turn_right.png",
    "발사": "card_fire.png",
    "재장전": "card_reload.png",
}

_cache = {}  # (이름, 크기) → 불러온 그림. 없는 파일은 None 으로 기억


def image(name, size):
    """assets/images 에서 그림을 불러와 size 로 맞춰 반환. 파일이 없으면 None."""
    key = (name, size)
    if key not in _cache:
        path = os.path.join(IMAGE_DIR, IMAGE_FILES.get(name, ""))
        if name in IMAGE_FILES and os.path.isfile(path):
            img = pygame.image.load(path).convert_alpha()
            _cache[key] = pygame.transform.smoothscale(img, size)
        else:
            _cache[key] = None
    return _cache[key]


def _blit(surf, name, rect, angle=0):
    """그림 파일이 있으면 rect 에 그리고 True, 없으면 False (→ 임시 그림을 그림)."""
    img = image(name, rect.size)
    if img is None:
        return False
    if angle:
        img = pygame.transform.rotate(img, angle)
    surf.blit(img, img.get_rect(center=rect.center))
    return True


# ======================================================================
# 아래 함수들의 "임시 그림" 부분이 주서연이 바꿀 곳
# TODO(표현 주서연): 그림 에셋 만들기 (PNG 를 넣거나 임시 그림을 고치기)
# ======================================================================

def draw_tile(surf, rect, kind):
    """격자 한 칸의 바닥. kind: '.' 바닥, '#' 벽, 'X' 출구, 'R' 뒤집기 타일."""
    if kind == "#":
        if not _blit(surf, "wall", rect):
            pygame.draw.rect(surf, WALL_COLOR, rect)                 # 임시 그림
    elif kind == "X":
        if not _blit(surf, "exit", rect):
            label(surf, *rect.center, "출구", 13)                    # 임시 그림
    elif kind == "R":
        if not _blit(surf, "flip", rect):
            pygame.draw.rect(surf, FLIP_COLOR, rect)                 # 임시 그림
            label(surf, *rect.center, "뒤집기", 11)


def draw_item(surf, rect, bullet):
    """바닥에 놓인 탄. bullet: '화염탄' / '빙결탄' / '폭발탄'."""
    if not _blit(surf, bullet, rect):
        label(surf, *rect.center, bullet[0], 16)                     # 임시 그림: 첫 글자


def draw_enemy(surf, rect, kind):
    """적. kind: 'chaser'(추적자) / 'dummy'(허수아비). 머리 위 숫자는 scenes.py 가 그림."""
    if not _blit(surf, kind, rect):
        label(surf, rect.centerx, rect.centery + 5, "적" if kind == "chaser" else "허", 18)  # 임시 그림


def draw_player(surf, rect, facing):
    """플레이어. facing: 0 위, 1 오른쪽, 2 아래, 3 왼쪽."""
    if not _blit(surf, "player", rect, angle=-90 * facing):       # 시계 방향으로 회전
        label(surf, *rect.center, "나" + DIR_ARROWS[facing], 15)     # 임시 그림


def draw_card(surf, rect, name):
    """카드 한 장 (손패). name: 카드 이름."""
    if not _blit(surf, name, rect):
        box(surf, rect, 2)                                           # 임시 그림: 테두리 + 이름
        label(surf, *rect.center, name, 14)


# TODO(표현 주서연): 이동 애니메이션 - 칸 사이를 미끄러지듯 움직이기
# TODO(표현 주서연): 재장전 애니메이션 - magazine.last_sort_steps 를 한 단계씩 보여주기
# TODO(표현 주서연): 효과음 (jsfxr) - assets/sounds/ 에 넣고 pygame.mixer.Sound 로 재생
