"""
배경·양피지·토큰 그림 만들기 (표현 담당)
컨셉: 어두운 나무 탁자 위에 양피지 지도를 펼쳐 놓고 하는 중세 보드게임
  - bg_table.png      : 화면 전체 나무 탁자 (가장자리는 어둡고 가운데는 촛불 빛)
  - parchment.png     : 패널·버튼 뒤에 깔 양피지 무늬 (화면 크기)
  - board.png         : 격자를 담은 양피지 지도 (찢긴 가장자리, 잉크 격자, A~J / 1~10 좌표)
  - wall.png          : 돌 블록 토큰 (입체)
  - exit.png / exit_open.png : 출구 문 토큰 (닫힘 / 적을 다 잡아 열림)
  - flip.png          : 뒤집기 타일 (바닥에 박힌 놋쇠 판)
  - bullet_*.png      : 탄 보석 토큰 (화염 = 불꽃 모양 루비, 빙결 = 얼음 결정, 폭발 = 심지 달린 폭탄)
  - card_cover.png    : 카드 더미에 엎어 둔 카드 뒷면
다시 만들기:  python assets/make_theme.py   (numpy 필요, 게임 실행에는 필요 없음)
"""
import math
import os
import sys

import numpy as np
import pygame

HERE = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(HERE, "images")
sys.path.insert(0, os.path.dirname(HERE))
from settings import W, H, N, CELL, GRID_X, GRID_Y, BOARD_RECT  # noqa: E402

RNG = np.random.default_rng(7)
INK = (58, 38, 22)
T = 4                     # 토큰은 4배 크기로 그린 뒤 줄임
TS = CELL * 2 * T // 2    # 토큰 작업 크기 (칸 46px → 184px)


# ======================================================================
# 노이즈 도구
# ======================================================================
def to_surface(rgb, alpha=None):
    """(h, w, 3) 배열 → pygame Surface (alpha 가 있으면 투명도 포함)."""
    rgb = np.clip(rgb, 0, 255).astype(np.uint8)
    h, w = rgb.shape[:2]
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.surfarray.blit_array(surf, rgb.transpose(1, 0, 2))
    if alpha is not None:
        a = pygame.surfarray.pixels_alpha(surf)
        a[:] = np.clip(alpha, 0, 255).astype(np.uint8).T
        del a
    else:
        surf.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MAX)
    return surf


def smooth_noise(h, w, cells_y, cells_x):
    """cells 개수만큼의 무작위 값을 부드럽게 늘린 노이즈 (0~1)."""
    small = RNG.random((cells_y, cells_x))
    img = np.repeat(small[:, :, None], 3, axis=2) * 255
    s = to_surface(img)
    s = pygame.transform.smoothscale(s, (w, h))
    return pygame.surfarray.array3d(s)[:, :, 0].T / 255.0


def fbm(h, w, base=4, octaves=5):
    """여러 크기의 노이즈를 겹친 구름 무늬 (0~1)."""
    total = np.zeros((h, w))
    amp, norm = 1.0, 0.0
    for o in range(octaves):
        n = base * 2 ** o
        total += smooth_noise(h, w, max(2, int(n * h / max(h, w))) + 1, max(2, int(n * w / max(h, w))) + 1) * amp
        norm += amp
        amp *= 0.5
    return total / norm


def blur(surf, k=8):
    """줄였다 키워서 흐리게."""
    w, h = surf.get_size()
    small = pygame.transform.smoothscale(surf, (max(1, w // k), max(1, h // k)))
    return pygame.transform.smoothscale(small, (w, h))


# ======================================================================
# 나무 탁자
# ======================================================================
def table():
    h, w = H, W
    y = np.arange(h)[:, None] * np.ones((1, w))
    x = np.ones((h, 1)) * np.arange(w)[None, :]
    plank_h = 96
    plank = (y // plank_h).astype(int)
    tone = RNG.uniform(0.85, 1.12, plank.max() + 2)[plank]

    warp = fbm(h, w, base=3, octaves=4) * 60
    grain = np.sin((y + warp + plank * 37) * 0.45 + fbm(h, w, 6, 3) * 8) * 0.5 + 0.5
    streak = smooth_noise(h, w, h // 3, 12)                     # 가로로 긴 결
    shade = 0.72 + 0.18 * grain + 0.22 * streak
    base = np.array([96, 60, 34])
    rgb = base[None, None, :] * (shade * tone)[:, :, None]

    # 옹이
    for _ in range(9):
        kx, ky = RNG.uniform(0, w), RNG.uniform(0, h)
        d = np.sqrt(((x - kx) / 2.6) ** 2 + (y - ky) ** 2)
        ring = (np.sin(d * 0.9) * 0.5 + 0.5) * np.exp(-d / 26)
        rgb *= (1 - 0.35 * ring)[:, :, None]

    # 판자 이음새 (어두운 줄 + 밝은 줄)
    seam = (y % plank_h)
    rgb[seam < 2] *= 0.35
    rgb[(seam >= 2) & (seam < 3)] *= 1.25

    # 촛불 빛은 가운데만 따뜻하게, 가장자리는 보랏빛 마력 안개로 어둡게
    cx, cy = w * 0.5, h * 0.42
    r = np.sqrt(((x - cx) / w) ** 2 + ((y - cy) / h) ** 2)
    light = np.clip(1.2 - r * 1.7, 0.22, 1.2)
    rgb = rgb * light[:, :, None]
    fog = np.clip(r * 1.6 - 0.25, 0, 1) * (0.6 + 0.4 * fbm(h, w, base=3, octaves=3))
    rgb[:, :, 0] += 26 * fog
    rgb[:, :, 2] += 58 * fog
    surf = to_surface(rgb)
    magic_circle(surf, (w // 2, h // 2), 330)
    return surf


def rune(surf, center, size, seed, color):
    """선으로 그린 룬 글자 하나 (세로 줄기 + 가지 몇 개). seed 마다 모양이 다름."""
    rng = np.random.default_rng(seed)
    cx, cy = center
    h = size
    pygame.draw.line(surf, color, (cx, cy - h / 2), (cx, cy + h / 2), 2)
    for _ in range(int(rng.integers(1, 4))):
        y0 = cy + rng.uniform(-h / 2, h / 4)
        side = rng.choice([-1, 1])
        y1 = y0 + rng.choice([-1, 1]) * h * 0.35
        pygame.draw.line(surf, color, (cx, y0), (cx + side * h * 0.35, y1), 2)


def magic_circle(surf, center, radius):
    """탁자에 새겨진 마법진: 원 여러 개 + 팔각별(사각형 두 개) + 룬 고리 + 은은한 보랏빛."""
    w, h = surf.get_size()
    lines = pygame.Surface((w, h), pygame.SRCALPHA)
    col = (180, 140, 250, 85)
    cx, cy = center
    for rr, width in ((radius, 3), (radius - 12, 1), (radius - 64, 2), (radius * 0.4, 2), (radius * 0.4 - 8, 1)):
        pygame.draw.circle(lines, col, center, int(rr), width)
    inner = radius - 64
    for k in range(2):                                           # 팔각별: 45도 엇갈린 사각형 두 개
        pts = [(cx + inner * math.cos(math.radians(k * 45 + i * 90)),
                cy + inner * math.sin(math.radians(k * 45 + i * 90))) for i in range(4)]
        pygame.draw.polygon(lines, col, pts, 2)
    n = 28
    for i in range(n):                                           # 바깥 고리의 룬
        a = math.radians(i * 360 / n)
        r = radius - 38
        glyph = pygame.Surface((30, 30), pygame.SRCALPHA)
        rune(glyph, (15, 15), 20, i, (205, 175, 255, 150))
        glyph = pygame.transform.rotate(glyph, -math.degrees(a) - 90)
        lines.blit(glyph, glyph.get_rect(center=(cx + r * math.cos(a), cy + r * math.sin(a))))
    for i in range(8):                                           # 팔각별 꼭짓점의 작은 원
        a = math.radians(i * 45)
        pygame.draw.circle(lines, col, (cx + inner * math.cos(a), cy + inner * math.sin(a)), 9, 2)
    glow = blur(lines, 5)
    glow.set_alpha(150)
    surf.blit(glow, (0, 0))
    surf.blit(lines, (0, 0))


# ======================================================================
# 양피지
# ======================================================================
def parchment_rgb(h, w):
    cloud = fbm(h, w, base=3, octaves=6)
    blot = fbm(h, w, base=8, octaves=3)
    base = np.array([236, 216, 174], dtype=float)
    shade = 0.84 + 0.2 * cloud - 0.1 * np.clip(blot - 0.55, 0, 1) * 3
    rgb = base[None, None, :] * shade[:, :, None]
    rgb[:, :, 2] -= 12 * (1 - cloud)          # 누렇게 바랜 느낌
    return rgb


def add_fibers(surf, count):
    """양피지 결: 짧은 옅은 선들."""
    w, h = surf.get_size()
    layer = pygame.Surface((w, h), pygame.SRCALPHA)
    for _ in range(count):
        x, y = RNG.uniform(0, w), RNG.uniform(0, h)
        a = RNG.uniform(0, math.pi)
        ln = RNG.uniform(6, 22)
        c = (120, 90, 55, int(RNG.uniform(12, 34)))
        pygame.draw.line(layer, c, (x, y), (x + math.cos(a) * ln, y + math.sin(a) * ln), 1)
    for _ in range(count // 40):                # 얼룩 점
        x, y = RNG.uniform(0, w), RNG.uniform(0, h)
        pygame.draw.circle(layer, (110, 70, 40, int(RNG.uniform(10, 30))), (x, y), RNG.uniform(1, 4))
    surf.blit(layer, (0, 0))


def parchment_texture():
    s = to_surface(parchment_rgb(H, W))
    add_fibers(s, 2600)
    return s


def torn_sheet(w, h, burn=18, pad=20):
    """찢긴 가장자리 + 그을린 테두리 + 그림자가 있는 양피지 한 장 (pad 만큼 바깥 여백 포함)."""
    W2, H2 = w + pad * 2, h + pad * 2
    rgb = np.zeros((H2, W2, 3))
    rgb[pad:pad + h, pad:pad + w] = parchment_rgb(h, w)
    yy = np.arange(H2)[:, None] * np.ones((1, W2))
    xx = np.ones((H2, 1)) * np.arange(W2)[None, :]
    # 가장자리까지 거리 (+ 노이즈로 울퉁불퉁)
    edge = np.minimum.reduce([xx - pad, (pad + w - 1) - xx, yy - pad, (pad + h - 1) - yy])
    edge = edge + (fbm(H2, W2, base=14, octaves=3) - 0.5) * 14
    alpha = np.clip(edge * 60, 0, 255)
    # 그을림: 가장자리 근처 어둡게
    burn_k = np.clip(1 - edge / burn, 0, 1) ** 1.6
    rgb = rgb * (1 - 0.55 * burn_k)[:, :, None]
    rgb[:, :, 2] *= (1 - 0.25 * burn_k)
    sheet = to_surface(rgb, alpha)
    add_fibers(sheet, int(w * h / 160))
    # 그림자 (오른쪽 아래로 살짝)
    shadow_a = np.clip(edge * 40, 0, 255) * 0.65
    shadow = to_surface(np.zeros((H2, W2, 3)), shadow_a)
    shadow = blur(shadow, 10)
    out = pygame.Surface((W2, H2), pygame.SRCALPHA)
    out.blit(shadow, (6, 9))
    out.blit(sheet, (0, 0))
    return out


def board():
    """지도: 찢긴 양피지 + 잉크 격자 + 테두리 장식 + 좌표."""
    bx, by, bw, bh = BOARD_RECT
    pad = 20
    sheet = torn_sheet(bw, bh, burn=22, pad=pad)
    ox, oy = pad - bx, pad - by          # 화면 좌표 → 이 그림 좌표
    ink = pygame.Surface(sheet.get_size(), pygame.SRCALPHA)
    gx, gy, size = GRID_X + ox, GRID_Y + oy, N * CELL
    # 칸 선 (옅은 잉크)
    for i in range(N + 1):
        pygame.draw.line(ink, (*INK, 110), (gx + i * CELL, gy), (gx + i * CELL, gy + size), 1)
        pygame.draw.line(ink, (*INK, 110), (gx, gy + i * CELL), (gx + size, gy + i * CELL), 1)
    # 두 줄 테두리 + 모서리 마름모
    pygame.draw.rect(ink, (*INK, 230), (gx - 3, gy - 3, size + 6, size + 6), 2)
    pygame.draw.rect(ink, (*INK, 180), (gx - 7, gy - 7, size + 14, size + 14), 1)
    for cx, cy in ((gx - 7, gy - 7), (gx + size + 7, gy - 7), (gx - 7, gy + size + 7), (gx + size + 7, gy + size + 7)):
        pygame.draw.polygon(ink, (*INK, 230), [(cx, cy - 6), (cx + 6, cy), (cx, cy + 6), (cx - 6, cy)])
    # 좌표 (위: A~J, 왼쪽: 1~10)
    f = pygame.font.SysFont("notoserifkr,batang,georgia", 12, bold=True)
    for i in range(N):
        t = f.render("ABCDEFGHIJ"[i], True, INK)
        t.set_alpha(200)
        ink.blit(t, t.get_rect(center=(gx + i * CELL + CELL // 2, gy - 15)))
        t = f.render(str(i + 1), True, INK)
        t.set_alpha(200)
        ink.blit(t, t.get_rect(center=(gx - 17, gy + i * CELL + CELL // 2)))
    sheet.blit(ink, (0, 0))
    return sheet


# ======================================================================
# 토큰 (4배로 그린 뒤 92px 로 저장 → 게임에서 46px 로 그림)
# ======================================================================
def canvas():
    return pygame.Surface((TS, TS), pygame.SRCALPHA)


def soft_shadow(s, rect, alpha=110, k=6):
    sh = canvas()
    pygame.draw.ellipse(sh, (20, 10, 0, alpha), rect)
    s.blit(blur(sh, k), (0, 0))


def noisy_fill(s, rect, base, amount=26, radius=10):
    """돌 질감: 기본색 + 노이즈 (rect 안, 모서리 둥글게)."""
    x, y, w, h = rect
    n = fbm(h, w, base=5, octaves=4)
    rgb = np.array(base, dtype=float)[None, None, :] + (n[:, :, None] - 0.5) * amount * 2
    tex = to_surface(rgb)
    mask = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, w, h), border_radius=radius)
    tex.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    s.blit(tex, (x, y))


def wall_token():
    """돌 블록: 윗면 + 앞면(입체) + 그림자."""
    s = canvas()
    soft_shadow(s, (22, 120, 160, 60), 120)
    front = (12, 118, 160, 56)
    noisy_fill(s, front, (78, 70, 62), 18, 14)                 # 앞면 (어둡게)
    noisy_fill(s, (12, 8, 160, 128), (150, 140, 124), 22, 14)  # 윗면
    pygame.draw.rect(s, INK, (12, 8, 160, 166), 5, border_radius=14)
    pygame.draw.line(s, INK, (14, 134), (170, 134), 4)          # 윗면/앞면 경계
    pygame.draw.line(s, (196, 186, 168), (24, 18), (160, 18), 4)   # 윗면 밝은 모서리
    pygame.draw.line(s, (196, 186, 168), (22, 20), (22, 124), 3)
    # 금 간 자국
    pygame.draw.lines(s, (92, 84, 74), False, [(60, 30), (72, 58), (66, 80), (82, 104)], 3)
    pygame.draw.lines(s, (92, 84, 74), False, [(128, 70), (114, 88), (120, 112)], 3)
    # 앞면 벽돌 줄눈
    pygame.draw.line(s, (52, 46, 40), (92, 136), (92, 170), 3)
    return s


def exit_token(opened):
    """출구: 돌 아치 문. 닫힘 = 나무 문, 열림 = 안쪽에서 빛."""
    s = canvas()
    soft_shadow(s, (20, 138, 150, 40), 120)
    # 돌 아치
    arch = pygame.Rect(28, 14, 128, 156)
    pygame.draw.rect(s, (128, 118, 104), arch, border_top_left_radius=64, border_top_right_radius=64)
    pygame.draw.rect(s, INK, arch, 5, border_top_left_radius=64, border_top_right_radius=64)
    inner = arch.inflate(-30, -24).move(0, 12)
    if opened:
        glow = canvas()
        for r in range(70, 0, -4):
            pygame.draw.circle(glow, (255, 200, 90, int(60 * (1 - r / 70))), inner.center, r)
        pygame.draw.rect(s, (40, 26, 16), inner, border_top_left_radius=48, border_top_right_radius=48)
        pygame.draw.rect(s, (255, 214, 120), inner.inflate(-26, -30).move(0, 10),
                         border_top_left_radius=34, border_top_right_radius=34)
        s.blit(glow, (0, 0))
        pygame.draw.polygon(s, (150, 96, 52), [(inner.right - 4, inner.y + 20), (inner.right + 16, inner.y + 6),
                                               (inner.right + 16, inner.bottom + 6), (inner.right - 4, inner.bottom)])
        pygame.draw.polygon(s, INK, [(inner.right - 4, inner.y + 20), (inner.right + 16, inner.y + 6),
                                     (inner.right + 16, inner.bottom + 6), (inner.right - 4, inner.bottom)], 3)
    else:
        pygame.draw.rect(s, (138, 86, 46), inner, border_top_left_radius=48, border_top_right_radius=48)
        for k in range(1, 4):                                   # 나무 판자
            x = inner.x + inner.w * k // 4
            pygame.draw.line(s, (92, 56, 30), (x, inner.y + 8), (x, inner.bottom - 2), 3)
        for yb in (inner.y + 40, inner.bottom - 26):            # 쇠 띠
            pygame.draw.line(s, (60, 56, 54), (inner.x + 2, yb), (inner.right - 2, yb), 7)
        pygame.draw.circle(s, (214, 168, 70), (inner.right - 18, inner.centery + 10), 7, 3)   # 문고리
    pygame.draw.rect(s, INK, inner, 4, border_top_left_radius=48, border_top_right_radius=48)
    return s


def flip_token():
    """뒤집기 타일: 바닥에 박힌 놋쇠 원판 + 위아래 화살표 각인."""
    s = canvas()
    soft_shadow(s, (24, 32, 140, 140), 80)
    c = (92, 88)
    for r, col in ((70, (120, 84, 36)), (64, (204, 156, 70)), (52, (230, 186, 96)), (46, (196, 146, 62))):
        pygame.draw.circle(s, col, c, r)
    pygame.draw.circle(s, INK, c, 70, 4)
    pygame.draw.circle(s, (120, 84, 36), c, 52, 2)
    for k in range(12):                                          # 테두리 리벳
        a = k * math.pi / 6
        pygame.draw.circle(s, (130, 92, 40), (c[0] + math.cos(a) * 58, c[1] + math.sin(a) * 58), 3)
    ink = (92, 56, 24)
    pygame.draw.line(s, ink, (76, 56), (76, 118), 7)             # ↑
    pygame.draw.polygon(s, ink, [(76, 44), (62, 66), (90, 66)])
    pygame.draw.line(s, ink, (108, 58), (108, 120), 7)           # ↓
    pygame.draw.polygon(s, ink, [(108, 132), (94, 110), (122, 110)])
    return s


def gem(points, colors, s, facets):
    """보석: 바깥 모양 + 면(facets) 색 + 하이라이트."""
    pygame.draw.polygon(s, colors[0], points)
    for poly, col in facets:
        pygame.draw.polygon(s, col, poly)
    pygame.draw.polygon(s, INK, points, 5)


def bullet_fire():
    s = canvas()
    soft_shadow(s, (44, 140, 96, 30), 110)
    glow = canvas()
    for r in range(64, 0, -4):
        pygame.draw.circle(glow, (255, 120, 40, int(70 * (1 - r / 64))), (92, 96), r)
    s.blit(glow, (0, 0))
    outer = [(92, 20), (122, 70), (130, 108), (112, 142), (92, 150), (72, 142), (54, 108), (62, 70)]
    gem(outer, [(206, 44, 30)], s, [
        ([(92, 20), (122, 70), (92, 92), (62, 70)], (238, 96, 52)),
        ([(62, 70), (92, 92), (72, 142), (54, 108)], (178, 34, 26)),
        ([(122, 70), (130, 108), (112, 142), (92, 92)], (214, 58, 34)),
        ([(92, 92), (112, 142), (92, 150), (72, 142)], (150, 26, 22)),
    ])
    pygame.draw.polygon(s, (255, 214, 170), [(84, 40), (96, 46), (80, 74)])
    return s


def bullet_ice():
    s = canvas()
    soft_shadow(s, (44, 140, 96, 30), 110)
    shards = [
        ([(92, 14), (116, 60), (104, 148), (80, 148), (68, 60)], (150, 210, 245)),
        ([(56, 70), (76, 92), (72, 146), (52, 146), (42, 96)], (110, 180, 230)),
        ([(128, 64), (142, 98), (130, 146), (110, 146), (112, 90)], (124, 192, 238)),
    ]
    for pts, col in shards:
        pygame.draw.polygon(s, col, pts)
        mid_top = pts[0]
        pygame.draw.line(s, (226, 246, 255), mid_top, ((pts[2][0] + pts[3][0]) / 2, pts[2][1]), 4)
        pygame.draw.polygon(s, (40, 70, 110), pts, 4)
    pygame.draw.polygon(s, (240, 252, 255), [(88, 30), (96, 36), (84, 70)])
    return s


def bullet_bomb():
    s = canvas()
    soft_shadow(s, (40, 140, 104, 30), 120)
    c = (92, 104)
    pygame.draw.circle(s, (70, 52, 92), c, 44)
    pygame.draw.circle(s, (104, 78, 136), (80, 92), 26)
    pygame.draw.circle(s, (150, 120, 190), (72, 84), 9)
    pygame.draw.circle(s, INK, c, 44, 5)
    pygame.draw.rect(s, (196, 150, 64), (78, 52, 28, 16), border_radius=4)   # 놋쇠 마개
    pygame.draw.rect(s, INK, (78, 52, 28, 16), 3, border_radius=4)
    pygame.draw.lines(s, (120, 90, 56), False, [(92, 52), (98, 36), (112, 28), (122, 30)], 5)   # 심지
    for k in range(8):                                           # 불똥
        a = k * math.pi / 4
        pygame.draw.line(s, (255, 214, 90), (124, 28), (124 + math.cos(a) * 14, 28 + math.sin(a) * 14), 3)
    pygame.draw.circle(s, (255, 250, 210), (124, 28), 6)
    return s


def card_cover():
    """카드 뒷면: 카드 시트와 같은 크기(237x330), 가죽 + 금색 테두리 + 나침반 별."""
    w, h = 237, 330
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(s, (70, 46, 28), (0, 0, w, h), border_radius=18)
    n = fbm(h - 36, w - 36, base=4, octaves=4)
    leather = to_surface(np.array([122, 70, 38])[None, None, :] * (0.8 + 0.35 * n)[:, :, None])
    s.blit(leather, (18, 18))
    pygame.draw.rect(s, (206, 160, 76), (28, 28, w - 56, h - 56), 4, border_radius=10)
    pygame.draw.rect(s, (206, 160, 76), (38, 38, w - 76, h - 76), 2, border_radius=8)
    cx, cy = w // 2, h // 2
    pts = []
    for i in range(16):
        r = 62 if i % 4 == 0 else (30 if i % 2 == 0 else 16)
        a = math.radians(-90 + i * 22.5)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    pygame.draw.polygon(s, (226, 178, 84), pts)
    pygame.draw.polygon(s, (90, 56, 28), pts, 3)
    pygame.draw.circle(s, (226, 178, 84), (cx, cy), 14)
    pygame.draw.circle(s, (90, 56, 28), (cx, cy), 14, 3)
    pygame.draw.rect(s, (40, 26, 16), (0, 0, w, h), 6, border_radius=18)
    return s


def save(img, name, size=None):
    if size:
        img = pygame.transform.smoothscale(img, size)
    pygame.image.save(img, os.path.join(IMG_DIR, name))
    print("저장:", name)


def main():
    pygame.init()
    pygame.display.set_mode((1, 1))
    save(table(), "bg_table.png")
    save(parchment_texture(), "parchment.png")
    save(board(), "board.png")
    tok = (CELL * 2, CELL * 2)
    save(wall_token(), "wall.png", tok)
    save(exit_token(False), "exit.png", tok)
    save(exit_token(True), "exit_open.png", tok)
    save(flip_token(), "flip.png", tok)
    save(bullet_fire(), "bullet_fire.png", tok)
    save(bullet_ice(), "bullet_ice.png", tok)
    save(bullet_bomb(), "bullet_bomb.png", tok)
    save(card_cover(), "card_cover.png")


if __name__ == "__main__":
    main()
