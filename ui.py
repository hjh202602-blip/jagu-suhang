"""
그리기 도구 (담당: 표현)
- 화면마다 반복해서 쓰는 배경, 양피지 패널, 칸, 버튼, 글자를 모아 둠
- 모든 화면은 이 함수들로 그림 → 디자인을 바꿀 때 여기만 고치면 전체가 바뀜
- 컨셉: 나무 탁자 위에 펼친 양피지 보드게임 (그림은 assets/make_theme.py 로 만듦)
"""
import math
import os

import pygame

from settings import (W, H, FONT_NAME, INK, INK_LIGHT, PARCHMENT, CREAM, GOLD, WAX,
                      BOARD_RECT, ARCANE, ARCANE_LIGHT)

IMAGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "images")
SERIF = "notoserifkr,batang,applemyungjo,nanummyeongjo"   # 제목용 명조체
BIG_SERIF = 999         # 명조체는 붓글씨처럼 보여서 쓰지 않음 (제목도 굵은 고딕 + 금빛·보랏빛)
MIN_SIZE = 10           # 글자를 줄여서 맞출 때 최소 크기

_fonts = {}    # (크기, 명조, 굵게) → 폰트 (매 프레임 새로 만들지 않도록)
_images = {}   # 파일 이름 → 그림
_cache = {}    # 패널·버튼처럼 크기별로 한 번 만들어 두는 그림


def font(size, serif=False, bold=True):
    """
    글자 모양. 작은 글자가 뭉개지지 않도록 전부 굵은 맑은 고딕을 쓰고,
    명조체는 큰 제목(BIG_SERIF 이상)에만 씀. bold 는 예전 코드와 맞추려고 남겨 둔 매개변수.
    """
    serif = serif and size >= BIG_SERIF
    key = (size, serif)
    if key not in _fonts:
        _fonts[key] = pygame.font.SysFont(SERIF if serif else FONT_NAME, size, bold=True)
    return _fonts[key]


FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "fonts")


def deco(size):
    """카드 이름용 장식 글꼴 (Cinzel Decorative Bold, assets/fonts, SIL OFL). 영어만 씀."""
    key = ("deco", size)
    if key not in _fonts:
        path = os.path.join(FONT_DIR, "CinzelDecorative-Bold.ttf")
        _fonts[key] = pygame.font.Font(path, size) if os.path.isfile(path) else font(size, serif=True)
    return _fonts[key]


def deco_label(surf, x, y, text, size, color=INK, width=None):
    """장식 글꼴 한 줄 (width 안에 들어가게 크기를 줄임)."""
    if width:
        while size > MIN_SIZE and deco(size).size(text)[0] > width:
            size -= 1
    img = deco(size).render(text, True, color)
    surf.blit(img, img.get_rect(center=(x, y)))


def _image(name):
    """assets/images 의 그림 (없으면 None)."""
    if name not in _images:
        path = os.path.join(IMAGE_DIR, name)
        _images[name] = pygame.image.load(path).convert_alpha() if os.path.isfile(path) else None
    return _images[name]


# ======================================================================
# 글자
# ======================================================================
def label(surf, x, y, text, size=20, color=INK, serif=False, bold=True, width=None, max_lines=None,
          align="center"):
    """
    글자 쓰기. (x, y) = 글자 덩어리의 가운데 (align="left" 면 x 는 왼쪽 끝).
    width 를 주면 그 폭 안에서 다음 줄로 넘기고, max_lines 보다 줄이 많으면 글자를 줄여서 맞춤.
    """
    if width is None:
        img = font(size, serif).render(text, True, color)
        rect = img.get_rect(midleft=(x, y)) if align == "left" else img.get_rect(center=(x, y))
        surf.blit(img, rect)
        return
    while True:
        lines = wrap(text, size, width, serif)
        if max_lines is None or len(lines) <= max_lines or size <= MIN_SIZE:
            break
        size -= 1
    if max_lines is not None:
        lines = lines[:max_lines]
    gap = int(size * 1.3)
    top = y - gap * (len(lines) - 1) / 2
    for k, line in enumerate(lines):
        img = font(size, serif).render(line, True, color)
        cy = int(top + k * gap)
        rect = img.get_rect(midleft=(x, cy)) if align == "left" else img.get_rect(center=(x, cy))
        surf.blit(img, rect)


def fit_size(text, size, width, serif=False):
    """한 줄로 width 안에 들어가는 가장 큰 글자 크기 (MIN_SIZE 까지 줄임)."""
    while size > MIN_SIZE and font(size, serif).size(text)[0] > width:
        size -= 1
    return size


def glow_text(img, color, radius=6, strength=170):
    """글자 모양을 흐리게 번지게 한 빛 (마법 빛남)."""
    w, h = img.get_size()
    pad = radius * 2
    base = pygame.Surface((w + pad * 2, h + pad * 2), pygame.SRCALPHA)
    tint = img.copy()
    tint.fill((*color, 255), special_flags=pygame.BLEND_RGBA_MIN)
    base.blit(tint, (pad, pad))
    small = pygame.transform.smoothscale(base, (max(1, base.get_width() // radius), max(1, base.get_height() // radius)))
    glow = pygame.transform.smoothscale(small, base.get_size())
    glow.set_alpha(strength)
    return glow, pad


def title(surf, x, y, text, size=40, color=GOLD, outline=INK, glow=ARCANE, deco_font=False):
    """빛나는 큰 제목: 보랏빛 번짐 + 진한 테두리 + 금색 글자. deco_font=True 면 영어 장식 글꼴."""
    f = (lambda s: deco(s)) if deco_font else (lambda s: font(s))
    img = f(size).render(text, True, color)
    rect = img.get_rect(center=(x, y))
    g, pad = glow_text(img, glow, max(4, size // 6))
    surf.blit(g, (rect.x - pad, rect.y - pad))
    edge = f(size).render(text, True, outline)
    for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2), (1, 3)):
        surf.blit(edge, rect.move(dx, dy))
    surf.blit(img, rect)


def wrap(text, size, width, serif=False):
    """
    글자를 width 안에 들어가게 여러 줄로 나눔. 줄바꿈 문자는 그 자리에서 줄바꿈,
    띄어쓰기 단위로 끊고, 한 단어가 너무 길면 글자 단위로.
    """
    if "\n" in text:
        return [line for part in text.split("\n") for line in wrap(part, size, width, serif)]
    f = font(size, serif)
    lines, line = [], ""
    for word in text.split(" "):
        cand = (line + " " + word) if line else word
        if f.size(cand)[0] <= width:
            line = cand
            continue
        if line:
            lines.append(line)
        line = ""
        for ch in word:                       # 단어 자체가 폭보다 길면 글자 단위로 자름
            if f.size(line + ch)[0] > width and line:
                lines.append(line)
                line = ch
            else:
                line += ch
    if line:
        lines.append(line)
    return lines or [""]


# ======================================================================
# 배경 · 양피지
# ======================================================================
def background(surf):
    """화면 전체: 마법진이 새겨진 나무 탁자 + 떠다니는 마력 불빛."""
    bg = _image("bg_table.png")
    if bg:
        surf.blit(bg, (0, 0))
    else:
        surf.fill((70, 44, 26))
    sparkles(surf)


_motes = []


def sparkles(surf):
    """천천히 위로 떠오르며 깜빡이는 작은 마력 불빛 (보라·하늘·금). 시간에 따라 움직임."""
    if not _motes:
        import random
        rng = random.Random(11)
        for _ in range(46):
            _motes.append((rng.uniform(0, W), rng.uniform(0, H), rng.uniform(8, 26), rng.uniform(0, 6.28),
                           rng.choice([ARCANE_LIGHT, (150, 210, 255), GOLD]), rng.uniform(1.5, 3.2)))
    t = pygame.time.get_ticks() / 1000
    key = ("mote", 0)
    if key not in _cache:
        dot = pygame.Surface((24, 24), pygame.SRCALPHA)
        for r in range(12, 0, -1):
            pygame.draw.circle(dot, (255, 255, 255, int(90 * (1 - r / 12) ** 1.5)), (12, 12), r)
        _cache[key] = dot
    for x0, y0, speed, phase, color, size in _motes:
        y = (y0 - t * speed) % (H + 40) - 20
        x = x0 + math.sin(t * 0.6 + phase) * 14
        twinkle = 0.45 + 0.55 * (0.5 + 0.5 * math.sin(t * 2.2 + phase * 3))
        ck = ("mote", color)
        if ck not in _cache:
            d = _cache[key].copy()
            d.fill((*color, 255), special_flags=pygame.BLEND_RGBA_MULT)
            _cache[ck] = d
        d = _cache[ck]
        d.set_alpha(int(255 * twinkle))
        surf.blit(d, (x - 12, y - 12))
        pygame.draw.circle(surf, color, (x, y), max(1, int(size * twinkle * 0.6)))


def board(surf):
    """격자를 담은 양피지 지도 (그림자·찢긴 가장자리 포함, 바깥 여백 20px)."""
    img = _image("board.png")
    if img:
        surf.blit(img, (BOARD_RECT[0] - 20, BOARD_RECT[1] - 20))
    else:
        pygame.draw.rect(surf, PARCHMENT, BOARD_RECT)


def _shadow(size, radius):
    key = ("shadow", size, radius)
    if key not in _cache:
        w, h = size
        s = pygame.Surface((w + 40, h + 40), pygame.SRCALPHA)
        pygame.draw.rect(s, (15, 8, 2, 150), (20, 20, w, h), border_radius=radius + 4)
        small = pygame.transform.smoothscale(s, (max(1, (w + 40) // 8), max(1, (h + 40) // 8)))
        _cache[key] = pygame.transform.smoothscale(small, (w + 40, h + 40))
    return _cache[key]


def _parchment(size, radius, tint=None, burn=10):
    """양피지 무늬를 잘라 둥근 모서리로 + 가장자리를 burn 픽셀만큼 조금 어둡게."""
    key = ("parch", size, radius, tint, burn)
    if key not in _cache:
        w, h = size
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        tex = _image("parchment.png")
        if tex:
            # 패널마다 다른 부분을 잘라 써서 무늬가 반복돼 보이지 않게
            ox, oy = (w * 7 + h * 3) % max(1, W - w), (w * 5 + h * 11) % max(1, H - h)
            s.blit(tex, (0, 0), (ox, oy, w, h))
        else:
            s.fill(PARCHMENT)
        if tint:
            s.fill(tint, special_flags=pygame.BLEND_RGB_MULT)
        # 가장자리 그을림
        for i in range(burn):
            a = int(30 * (1 - i / burn))
            pygame.draw.rect(s, (90, 56, 28, a), (i, i, w - 2 * i, h - 2 * i), 1, border_radius=radius)
        mask = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, w, h), border_radius=radius)
        s.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        _cache[key] = s
    return _cache[key]


def panel(surf, rect, title_text=None, radius=10):
    """탁자 위에 놓인 양피지 한 장 (그림자 + 잉크 두 줄 테두리). title_text 가 있으면 위에 제목."""
    rect = pygame.Rect(rect)
    surf.blit(_shadow(rect.size, radius), (rect.x - 20 + 4, rect.y - 20 + 6))
    surf.blit(_parchment(rect.size, radius), rect)
    pygame.draw.rect(surf, (*INK,), rect, 2, border_radius=radius)
    pygame.draw.rect(surf, INK_LIGHT, rect.inflate(-10, -10), 1, border_radius=max(0, radius - 4))
    if title_text:
        label(surf, rect.centerx, rect.y + 24, title_text, 19, width=rect.w - 24, max_lines=1)
        pygame.draw.line(surf, INK_LIGHT, (rect.x + 24, rect.y + 42), (rect.right - 24, rect.y + 42), 1)


def slot(surf, rect, highlight=False):
    """양피지 위의 움푹한 칸 (큐 칸, 탄창 칸)."""
    rect = pygame.Rect(rect)
    surf.blit(_parchment(rect.size, 6, (222, 210, 186), burn=4), rect)
    pygame.draw.line(surf, (120, 86, 52), rect.topleft, rect.topright, 2)      # 위쪽 그늘 (움푹)
    pygame.draw.rect(surf, GOLD if highlight else INK_LIGHT, rect, 3 if highlight else 1, border_radius=6)


def mat(surf, rect):
    """카드를 펼쳐 두는 가죽 매트 (바느질 테두리)."""
    rect = pygame.Rect(rect)
    key = ("mat", rect.size)
    if key not in _cache:
        s = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(s, (74, 42, 22, 235), (0, 0, *rect.size), border_radius=14)
        for i in range(rect.h):
            a = int(40 * (1 - i / rect.h))
            pygame.draw.line(s, (140, 90, 50, a), (6, i), (rect.w - 6, i))
        inner = pygame.Rect(0, 0, *rect.size).inflate(-14, -14)
        for x in range(inner.x, inner.right, 12):                    # 바느질
            pygame.draw.line(s, (196, 150, 90), (x, inner.y), (x + 6, inner.y), 2)
            pygame.draw.line(s, (196, 150, 90), (x, inner.bottom), (x + 6, inner.bottom), 2)
        for y in range(inner.y, inner.bottom, 12):
            pygame.draw.line(s, (196, 150, 90), (inner.x, y), (inner.x, y + 6), 2)
            pygame.draw.line(s, (196, 150, 90), (inner.right, y), (inner.right, y + 6), 2)
        _cache[key] = s
    surf.blit(_shadow(rect.size, 14), (rect.x - 16, rect.y - 14))
    surf.blit(_cache[key], rect)


def scroll(surf, rect):
    """마법서 한 장: 보랏빛 마력이 번지는 양피지 + 금색 모서리 장식 + 위쪽 가운데 보석."""
    rect = pygame.Rect(rect)
    key = ("aura", rect.size)
    if key not in _cache:
        a = pygame.Surface((rect.w + 80, rect.h + 80), pygame.SRCALPHA)
        pygame.draw.rect(a, (*ARCANE, 150), (40, 40, rect.w, rect.h), border_radius=18)
        small = pygame.transform.smoothscale(a, (max(1, a.get_width() // 14), max(1, a.get_height() // 14)))
        _cache[key] = pygame.transform.smoothscale(small, a.get_size())
    surf.blit(_cache[key], (rect.x - 40, rect.y - 40))
    panel(surf, rect, radius=8)
    pygame.draw.rect(surf, GOLD, rect.inflate(-14, -14), 2, border_radius=6)
    for sx, sy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):           # 모서리 금장식 (꺾쇠 + 작은 원)
        cx = rect.x + 7 if sx > 0 else rect.right - 8
        cy = rect.y + 7 if sy > 0 else rect.bottom - 8
        pygame.draw.lines(surf, GOLD, False, [(cx, cy + sy * 46), (cx, cy), (cx + sx * 46, cy)], 5)
        pygame.draw.lines(surf, INK, False, [(cx, cy + sy * 46), (cx, cy), (cx + sx * 46, cy)], 1)
        pygame.draw.circle(surf, GOLD, (cx + sx * 14, cy + sy * 14), 6)
        pygame.draw.circle(surf, ARCANE, (cx + sx * 14, cy + sy * 14), 3)
    gem(surf, (rect.centerx, rect.y + 7), 11)


def gem(surf, center, r):
    """마름모 보석 (보라) + 금 테."""
    cx, cy = center
    pts = [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]
    pygame.draw.polygon(surf, GOLD, [(cx, cy - r - 4), (cx + r + 4, cy), (cx, cy + r + 4), (cx - r - 4, cy)])
    pygame.draw.polygon(surf, ARCANE, pts)
    pygame.draw.polygon(surf, ARCANE_LIGHT, [(cx, cy - r), (cx + r // 2, cy - r // 3), (cx - r // 2, cy - r // 3)])
    pygame.draw.polygon(surf, INK, [(cx, cy - r - 4), (cx + r + 4, cy), (cx, cy + r + 4), (cx - r - 4, cy)], 2)


def seal(surf, center, text, radius=14):
    """룬 돌: 보랏빛으로 빛나는 짙은 원판 + 금 테 + 번호 (행동 큐 순서 등)."""
    key = ("rune", radius)
    if key not in _cache:
        size = radius * 2 + 16
        s = pygame.Surface((size, size), pygame.SRCALPHA)
        c = size // 2
        for r in range(radius + 8, radius, -1):                 # 바깥 빛
            pygame.draw.circle(s, (*ARCANE, int(70 * (1 - (r - radius) / 8))), (c, c), r)
        pygame.draw.circle(s, (46, 30, 70), (c, c), radius)
        pygame.draw.circle(s, (78, 54, 120), (c - radius // 4, c - radius // 4), radius // 2)
        pygame.draw.circle(s, GOLD, (c, c), radius, 2)
        pygame.draw.circle(s, ARCANE_LIGHT, (c, c), radius - 4, 1)
        _cache[key] = s
    img = _cache[key]
    surf.blit(img, img.get_rect(center=center))
    deco_label(surf, center[0], center[1] + 1, text, max(10, radius), ARCANE_LIGHT)


def stars_text(n, total=3):
    return "★" * n + "☆" * (total - n)


def box(surf, rect, width=3, color=INK):
    """잉크 테두리 사각형. rect = (x, y, 너비, 높이)"""
    pygame.draw.rect(surf, color, rect, width)


# ======================================================================
# 버튼
# ======================================================================
def _plaque(size, hover):
    """가죽 명판: 위→아래 그라데이션 + 금색 안쪽 선."""
    key = ("plaque", size, hover)
    if key not in _cache:
        w, h = size
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        top = (150, 92, 50) if hover else (128, 76, 40)
        bottom = (96, 56, 28) if hover else (80, 44, 22)
        for y in range(h):
            t = y / max(1, h - 1)
            c = [int(top[k] + (bottom[k] - top[k]) * t) for k in range(3)]
            pygame.draw.line(s, c, (0, y), (w, y))
        mask = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, w, h), border_radius=10)
        s.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        pygame.draw.rect(s, (40, 24, 12), (0, 0, w, h), 3, border_radius=10)
        pygame.draw.rect(s, GOLD if hover else (196, 150, 70), (5, 5, w - 10, h - 10), 2, border_radius=7)
        for x, y in ((10, 10), (w - 11, 10), (10, h - 11), (w - 11, h - 11)):   # 모서리 보랏빛 보석 못
            pygame.draw.circle(s, GOLD, (x, y), 4)
            pygame.draw.circle(s, ARCANE_LIGHT if hover else ARCANE, (x, y), 2)
        _cache[key] = s
    return _cache[key]


class Button:
    """가죽 명판 버튼. 마우스를 올리면 밝아지고 금색 테두리가 빛남."""

    def __init__(self, rect, text, size=20):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.size = size

    def draw(self, surf):
        hover = self.rect.collidepoint(pygame.mouse.get_pos())
        surf.blit(_shadow(self.rect.size, 10), (self.rect.x - 20 + 3, self.rect.y - 20 + 5))
        if hover:                                                   # 마우스를 올리면 보랏빛 마력이 번짐
            key = ("btnglow", self.rect.size)
            if key not in _cache:
                gsurf = pygame.Surface((self.rect.w + 40, self.rect.h + 40), pygame.SRCALPHA)
                pygame.draw.rect(gsurf, (*ARCANE, 200), (20, 20, *self.rect.size), border_radius=12)
                small = pygame.transform.smoothscale(gsurf, (max(1, gsurf.get_width() // 8), max(1, gsurf.get_height() // 8)))
                _cache[key] = pygame.transform.smoothscale(small, gsurf.get_size())
            surf.blit(_cache[key], (self.rect.x - 20, self.rect.y - 20))
        surf.blit(_plaque(self.rect.size, hover), self.rect)
        cx, cy = self.rect.center
        size = fit_size(self.text, self.size, self.rect.w - 24)         # 명판 안에 들어가게
        label(surf, cx + 1, cy + 2, self.text, size, (30, 16, 8))
        label(surf, cx, cy, self.text, size, GOLD if hover else CREAM)

    def clicked(self, event):
        """이 이벤트가 버튼 위에서 왼쪽 클릭이면 True (누르는 소리도 냄)."""
        hit = (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
               and self.rect.collidepoint(event.pos))
        if hit:
            import assets              # assets 가 ui 를 불러 쓰므로 여기서 늦게 불러옴
            assets.play("click")
        return hit
