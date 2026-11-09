"""
그림 에셋 (담당: 표현 주서연)

지금은 pygame 도형으로 그린 기본 그림을 씀. 더 좋은 그림으로 바꾸는 방법은 두 가지:
    1) 쉬운 방법: assets/images/ 폴더에 아래 IMAGE_FILES 이름대로 PNG 를 넣기
       → 파일이 있으면 자동으로 그 그림을 씀 (칸 크기 46x46 에 맞춰 늘리거나 줄임)
    2) 직접 그리기: 아래 draw_... 함수 안의 pygame.draw 부분을 고치기
효과음도 assets/sounds/<이름>.wav 를 넣으면 코드로 만든 소리 대신 그 파일을 씀

scenes.py 는 격자·카드를 그릴 때 이 파일의 draw_... 함수만 부름.
그래서 여기만 고치면 게임 전체 그림이 바뀜. 함수 이름과 매개변수는 그대로 둘 것.
"""
import array
import math
import os
import random

import pygame

from settings import WALL_COLOR, FLIP_COLOR, DIRS, BLACK, WHITE
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
# 그림 파일이 없을 때 쓰는 기본 그림 (흰 바탕 + 검은 선, 기획서 아트 방향)
# PNG 를 assets/images/ 에 넣으면 그쪽이 먼저 쓰임
# ======================================================================

BULLET_COLOR = {"화염탄": (240, 120, 70), "빙결탄": (120, 190, 240), "폭발탄": (170, 170, 170)}


def draw_tile(surf, rect, kind):
    """격자 한 칸의 바닥. kind: '.' 바닥, '#' 벽, 'X' 출구, 'R' 뒤집기 타일."""
    if kind == "#":
        if not _blit(surf, "wall", rect):
            pygame.draw.rect(surf, WALL_COLOR, rect)
            # 벽돌 줄무늬
            for i in range(1, 3):
                y = rect.y + rect.h * i // 3
                pygame.draw.line(surf, BLACK, (rect.x, y), (rect.right, y), 1)
            pygame.draw.line(surf, BLACK, (rect.centerx, rect.y), (rect.centerx, rect.y + rect.h // 3), 1)
            pygame.draw.line(surf, BLACK, (rect.centerx, rect.bottom - rect.h // 3), (rect.centerx, rect.bottom), 1)
    elif kind == "X":
        if not _blit(surf, "exit", rect):
            door = pygame.Rect(rect.x + 12, rect.y + 4, rect.w - 24, rect.h - 20)
            pygame.draw.rect(surf, BLACK, door, 2, border_top_left_radius=9, border_top_right_radius=9)
            pygame.draw.circle(surf, BLACK, (door.right - 5, door.centery + 2), 2)
            label(surf, rect.centerx, rect.bottom - 8, "출구", 10)
    elif kind == "R":
        if not _blit(surf, "flip", rect):
            pygame.draw.rect(surf, FLIP_COLOR, rect)
            # 위아래 화살표: 순서가 뒤집힘
            cx, cy = rect.center
            pygame.draw.polygon(surf, BLACK, [(cx - 8, cy - 4), (cx - 3, cy - 13), (cx + 2, cy - 4)])
            pygame.draw.line(surf, BLACK, (cx - 3, cy - 4), (cx - 3, cy + 12), 2)
            pygame.draw.polygon(surf, BLACK, [(cx - 2, cy + 4), (cx + 3, cy + 13), (cx + 8, cy + 4)])
            pygame.draw.line(surf, BLACK, (cx + 3, cy - 12), (cx + 3, cy + 4), 2)


def draw_item(surf, rect, bullet):
    """바닥에 놓인 탄. bullet: '화염탄' / '빙결탄' / '폭발탄'."""
    if not _blit(surf, bullet, rect):
        cx, cy = rect.center
        pygame.draw.circle(surf, BULLET_COLOR[bullet], (cx, cy), 13)
        pygame.draw.circle(surf, BLACK, (cx, cy), 13, 2)
        label(surf, cx, cy, bullet[0], 13)


def draw_enemy(surf, rect, kind):
    """적. kind: 'chaser'(추적자) / 'dummy'(허수아비). 머리 위 숫자는 scenes.py 가 그림."""
    if _blit(surf, kind, rect):
        return
    cx, cy = rect.centerx, rect.centery + 5
    if kind == "chaser":
        # 뾰족한 머리의 그림자 괴물 + 흰 눈
        pygame.draw.polygon(surf, (40, 40, 40), [(cx - 13, cy + 13), (cx - 13, cy - 3), (cx - 7, cy - 10),
                                                 (cx, cy - 4), (cx + 7, cy - 10), (cx + 13, cy - 3), (cx + 13, cy + 13)])
        pygame.draw.circle(surf, WHITE, (cx - 5, cy + 2), 3)
        pygame.draw.circle(surf, WHITE, (cx + 5, cy + 2), 3)
    else:
        # 허수아비: 막대 + 팔 + 둥근 머리
        pygame.draw.line(surf, BLACK, (cx, cy - 6), (cx, cy + 14), 3)
        pygame.draw.line(surf, BLACK, (cx - 12, cy), (cx + 12, cy), 3)
        pygame.draw.circle(surf, WHITE, (cx, cy - 9), 6)
        pygame.draw.circle(surf, BLACK, (cx, cy - 9), 6, 2)


def draw_player(surf, rect, facing):
    """플레이어. facing: 0 위, 1 오른쪽, 2 아래, 3 왼쪽."""
    if _blit(surf, "player", rect, angle=-90 * facing):       # 시계 방향으로 회전
        return
    cx, cy = rect.center
    dx, dy = DIRS[facing]
    # 몸: 흰 원 + 굵은 테두리, 바라보는 쪽에 지팡이(삼각형)
    pygame.draw.circle(surf, WHITE, (cx, cy), 13)
    pygame.draw.circle(surf, BLACK, (cx, cy), 13, 3)
    tip = (cx + dx * 21, cy + dy * 21)
    side = (-dy * 6, dx * 6)
    base = (cx + dx * 11, cy + dy * 11)
    pygame.draw.polygon(surf, BLACK, [tip, (base[0] + side[0], base[1] + side[1]),
                                      (base[0] - side[0], base[1] - side[1])])


def draw_card(surf, rect, name):
    """카드 한 장 (손패). name: 카드 이름."""
    if not _blit(surf, name, rect):
        pygame.draw.rect(surf, WHITE, rect)
        box(surf, rect, 2)
        label(surf, rect.centerx, rect.y + 40, CARD_ICONS.get(name, ""), 30)
        label(surf, rect.centerx, rect.bottom - 25, name, 14)


# 맑은 고딕에 있는 기호만 사용 (없는 기호는 네모로 깨져 보임)
CARD_ICONS = {"앞으로 이동": "↑", "뒤로 이동": "↓", "왼쪽 보기": "◀", "오른쪽 보기": "▶",
              "발사": "★", "재장전": "▲▼", "기절": "×"}


# ======================================================================
# 효과음: 파일 없이 코드로 짧은 소리를 만들어 씀 (assets/sounds/<이름>.wav 가 있으면 그 파일 사용)
# ======================================================================

SOUND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "sounds")

# 이름 → (시작 음높이 Hz, 끝 음높이 Hz, 길이 ms, 소리 모양)
SOUND_SHAPES = {
    "fire":   (900, 300, 120, "square"),
    "hit":    (220, 90, 140, "noise"),
    "hurt":   (180, 120, 220, "square"),
    "pickup": (500, 1000, 90, "square"),
    "reload": (300, 700, 220, "square"),
    "flip":   (700, 300, 200, "sine"),
    "clear":  (500, 1100, 400, "sine"),
    "fail":   (300, 100, 500, "sine"),
}
_sounds = {}


def _make_sound(name):
    """SOUND_SHAPES 의 값으로 짧은 효과음 만들기 (음높이가 시작 → 끝으로 미끄러짐)."""
    path = os.path.join(SOUND_DIR, name + ".wav")
    if os.path.isfile(path):
        return pygame.mixer.Sound(path)
    rate, _, channels = pygame.mixer.get_init()
    f0, f1, ms, shape = SOUND_SHAPES[name]
    n = rate * ms // 1000
    data = array.array("h")
    phase = 0.0
    for i in range(n):
        t = i / n
        phase += (f0 + (f1 - f0) * t) / rate
        if shape == "square":
            v = 1.0 if phase % 1 < 0.5 else -1.0
        elif shape == "noise":
            v = random.uniform(-1, 1)
        else:
            v = math.sin(2 * math.pi * phase)
        sample = int(v * (1 - t) * 6000)       # 뒤로 갈수록 작아짐
        for _ in range(channels):
            data.append(sample)
    return pygame.mixer.Sound(buffer=data.tobytes())


def play(name):
    """효과음 재생. 소리 장치가 없으면 조용히 넘어감."""
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        if name not in _sounds:
            _sounds[name] = _make_sound(name)
        _sounds[name].play()
    except (pygame.error, KeyError):
        pass
