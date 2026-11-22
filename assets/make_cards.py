"""
카드 그림 만들기 (표현 담당)
assets/images/card_sheet.png (카드 9칸 시트)에서 카드를 잘라 assets/images/ 에 PNG 로 저장.
시트에 없는 카드(2칸 앞으로, 왼쪽/오른쪽 보기)는 빈 카드 틀에 시트의 그림을 옮겨 만듦.
시트를 바꾸면 다시 실행:  python assets/make_cards.py
"""
import os

import pygame

HERE = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(HERE, "images")
SCALE = 3                       # 3배로 키워서 작업 (글자를 또렷하게)

# 시트 안 카드 위치 (왼쪽 위 x, y), 카드 크기 79x110
COLS = [26, 127, 227]
ROWS = [19, 149, 281]
CARD_W, CARD_H = 79, 110
ART = pygame.Rect(5, 6, 69, 81)         # 카드 안 그림 칸 (원래 크기 기준)
LABEL = pygame.Rect(6, 92, 67, 13)      # 아래 이름 띠
BG = (245, 245, 245)                    # 시트 바탕색 → 투명으로
INK = (78, 58, 40)                      # 이름 글자색 (시트 글자와 비슷하게)
GOLD = (236, 170, 60)


def crop(sheet, col, row):
    """시트에서 카드 한 장을 잘라 3배로 키우고, 바깥 바탕을 투명하게."""
    card = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
    card.blit(sheet, (0, 0), (COLS[col], ROWS[row], CARD_W, CARD_H))
    for x in range(CARD_W):
        for y in range(CARD_H):
            r, g, b, _ = card.get_at((x, y))
            if r > 238 and g > 238 and b > 238:
                card.set_at((x, y), (0, 0, 0, 0))
    return pygame.transform.smoothscale(card, (CARD_W * SCALE, CARD_H * SCALE))


def big(rect):
    return pygame.Rect(rect.x * SCALE, rect.y * SCALE, rect.w * SCALE, rect.h * SCALE)


def relabel(card, blank, text):
    """이름 띠를 빈 카드의 띠로 덮고 새 이름 쓰기 (시트처럼 스몰 캡스: 단어 첫 글자만 크게)."""
    strip = big(LABEL)
    card.blit(blank, strip, strip)
    name = "palatinolinotype,georgia,timesnewroman"
    large, small = pygame.font.SysFont(name, 24), pygame.font.SysFont(name, 18)
    parts = []
    for word in text.split():
        parts.append(large.render(word[0], True, INK))
        if len(word) > 1:
            parts.append(small.render(word[1:], True, INK))
        parts.append(small.render(" ", True, INK))
    parts.pop()
    width = sum(p.get_width() for p in parts)
    x = strip.centerx - width // 2
    base = strip.centery + large.get_ascent() // 2 - 2
    for p in parts:
        card.blit(p, (x, base - p.get_height() + (4 if p.get_height() > 26 else 2)))
        x += p.get_width()


def arrow(card, left):
    """회전 방향 표시: 그림 칸 옆에 금색 화살촉."""
    art = big(ART)
    cy = art.centery - 12
    if left:
        pts = [(art.x + 10, cy), (art.x + 34, cy - 18), (art.x + 34, cy + 18)]
    else:
        pts = [(art.right - 10, cy), (art.right - 34, cy - 18), (art.right - 34, cy + 18)]
    pygame.draw.polygon(card, GOLD, pts)
    pygame.draw.polygon(card, INK, pts, 3)


def cut_out(card, blank):
    """그림 칸에서 바탕(빈 카드와 같은 색)을 지우고 그림만 남긴 투명 이미지."""
    art = big(ART).inflate(-30, -30)       # 그림 칸 테두리 선은 빼고 안쪽만
    out = pygame.Surface(art.size, pygame.SRCALPHA)
    for x in range(art.w):
        for y in range(art.h):
            c = card.get_at((art.x + x, art.y + y))
            bgc = blank.get_at((art.x + x, art.y + y))
            if sum(abs(c[i] - bgc[i]) for i in range(3)) > 60:
                out.set_at((x, y), c)
    return out


def main():
    pygame.init()
    pygame.display.set_mode((1, 1))
    sheet = pygame.image.load(os.path.join(IMG_DIR, "card_sheet.png")).convert_alpha()
    advance, retreat, fire = crop(sheet, 0, 0), crop(sheet, 1, 0), crop(sheet, 2, 0)
    slash, turn, reload_ = crop(sheet, 0, 1), crop(sheet, 1, 1), crop(sheet, 2, 1)
    blank = crop(sheet, 1, 2)
    art = big(ART)

    # 왼쪽/오른쪽 보기: TURN 그림을 그대로(오른쪽), 좌우로 뒤집어(왼쪽) 쓰고 이름만 바꿈
    turn_right = turn.copy()
    arrow(turn_right, left=False)
    relabel(turn_right, blank, "TURN RIGHT")
    turn_left = blank.copy()
    turn_left.blit(pygame.transform.flip(turn.subsurface(art), True, False), art)
    arrow(turn_left, left=True)
    relabel(turn_left, blank, "TURN LEFT")

    # 2칸 앞으로: ADVANCE 장화를 잘라내 두 번 겹쳐 그림 (뒤쪽은 반투명 잔상)
    boot = cut_out(advance, blank)
    small = pygame.transform.smoothscale(boot, (int(art.w * 0.82), int(art.h * 0.82)))
    dash = blank.copy()
    ghost = small.copy()
    ghost.set_alpha(110)
    dash.blit(ghost, (art.x - 6, art.y + art.h - small.get_height() + 4))
    dash.blit(small, (art.right - small.get_width() + 6, art.y - 4))
    relabel(dash, blank, "DASH")

    out = {
        "card_forward.png": advance, "card_back.png": retreat, "card_fire.png": fire,
        "card_reload.png": reload_, "card_turn_right.png": turn_right, "card_turn_left.png": turn_left,
        "card_dash.png": dash,
        "card_slash_left.png": slash,   # 지금 게임에는 없는 카드 (기획서의 '왼쪽 공격'용으로 보관)
        "card_blank.png": blank,
    }
    for name, img in out.items():
        pygame.image.save(img, os.path.join(IMG_DIR, name))
        print("저장:", name)


if __name__ == "__main__":
    main()
