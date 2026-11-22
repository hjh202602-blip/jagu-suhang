"""
유닛 그림 만들기 (표현 담당)
카드 그림과 어울리게 갈색 가죽·금색·양피지 색으로 플레이어, 추적자, 허수아비를 그림.
양피지 지도 위에 세워 둔 보드게임 말처럼 둥근 받침 위에 올림 (플레이어 = 놋쇠, 추적자 = 무쇠, 허수아비 = 나무).
4배 크기로 그린 뒤 줄여서 저장 (가장자리가 부드럽게) → assets/images/ 에 PNG
다시 만들기:  python assets/make_units.py
"""
import math
import os

import pygame

HERE = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(HERE, "images")
S = 184                     # 작업 크기 (칸 46px 의 4배)
OUT = 92                    # 저장 크기

# 카드 시트에서 따온 색
INK = (52, 34, 22)          # 테두리
GOLD = (236, 170, 60)
GOLD_DARK = (176, 112, 34)
LEATHER = (140, 86, 46)
LEATHER_DARK = (86, 50, 28)


def canvas():
    return pygame.Surface((S, S), pygame.SRCALPHA)


def gradient_fill(target, draw_mask, top, bottom, box=(0, 0, S, S)):
    """draw_mask(surf) 로 그린 모양 안을 위(top) → 아래(bottom) 색 그라데이션으로 채움."""
    mask = canvas()
    draw_mask(mask)
    grad = canvas()
    x, y, w, h = box
    for i in range(S):
        t = min(max((i - y) / max(h, 1), 0), 1)
        c = [int(top[k] + (bottom[k] - top[k]) * t) for k in range(3)]
        pygame.draw.line(grad, (*c, 255), (0, i), (S, i))
    grad.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    target.blit(grad, (0, 0))


def white(surf_fn):
    """모양 그리는 함수를 흰색 마스크용으로 감쌈."""
    return lambda m: surf_fn(m, (255, 255, 255, 255))


def glow(target, center, radius, color, strength=90):
    """부드러운 빛 (바깥으로 갈수록 투명)."""
    g = canvas()
    for r in range(radius, 0, -2):
        a = int(strength * (1 - r / radius) ** 1.6)
        pygame.draw.circle(g, (*color, a), center, r)
    target.blit(g, (0, 0))


def shadow(target, cx=92, cy=166, w=104, h=22):
    sh = canvas()
    pygame.draw.ellipse(sh, (0, 0, 0, 70), (cx - w // 2, cy - h // 2, w, h))
    target.blit(sh, (0, 0))


def star(cx, cy, r1, r2, n=5, rot=-90):
    pts = []
    for i in range(n * 2):
        r = r1 if i % 2 == 0 else r2
        a = math.radians(rot + i * 180 / n)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


# ======================================================================
def player():
    """견습 마법사: 가죽 마법사 모자 + 금색 띠, 갈색 망토, 금 브로치, 금빛 기운."""
    s = canvas()
    glow(s, (92, 92), 88, GOLD, 70)
    shadow(s)

    # 망토
    cloak = [(66, 96), (118, 96), (146, 164), (124, 170), (92, 160), (60, 170), (38, 164)]
    gradient_fill(s, white(lambda m, c: pygame.draw.polygon(m, c, cloak)), (150, 92, 50), LEATHER_DARK, (0, 96, S, 74))
    pygame.draw.polygon(s, INK, cloak, 5)
    pygame.draw.line(s, INK, (92, 112), (92, 160), 3)          # 망토 가운데 주름
    pygame.draw.circle(s, GOLD, (92, 106), 9)                    # 브로치
    pygame.draw.circle(s, INK, (92, 106), 9, 3)

    # 얼굴
    gradient_fill(s, white(lambda m, c: pygame.draw.circle(m, c, (92, 80), 25)), (246, 214, 176), (214, 168, 126), (0, 55, S, 50))
    pygame.draw.circle(s, INK, (92, 80), 25, 4)
    for ex in (83, 101):                                         # 눈
        pygame.draw.ellipse(s, INK, (ex - 4, 78, 8, 11))
        pygame.draw.circle(s, (255, 255, 255), (ex + 1, 81), 2)
    pygame.draw.arc(s, INK, (84, 88, 16, 10), math.pi * 1.15, math.pi * 1.85, 3)   # 입

    # 모자: 챙 + 고깔 + 금색 띠 + 별
    cone = [(58, 62), (126, 62), (112, 30), (100, 10), (128, 4), (96, 2), (84, 18), (72, 34)]
    gradient_fill(s, white(lambda m, c: pygame.draw.polygon(m, c, cone)), (166, 104, 58), LEATHER_DARK, (0, 0, S, 64))
    pygame.draw.polygon(s, INK, cone, 5)
    brim = (34, 52, 116, 24)
    gradient_fill(s, white(lambda m, c: pygame.draw.ellipse(m, c, brim)), (150, 92, 50), (96, 56, 30), (0, 52, S, 24))
    pygame.draw.ellipse(s, INK, brim, 5)
    band = [(64, 50), (120, 50), (124, 60), (60, 60)]
    pygame.draw.polygon(s, GOLD, band)
    pygame.draw.polygon(s, INK, band, 3)
    pygame.draw.polygon(s, GOLD, star(98, 34, 10, 4))
    pygame.draw.polygon(s, GOLD_DARK, star(98, 34, 10, 4), 2)
    return s


def chaser():
    """추적자: 뿔 달린 그림자 괴물, 주황빛 눈, 물결치는 아랫단."""
    s = canvas()
    shadow(s, w=116)
    glow(s, (92, 100), 80, (120, 60, 160), 60)

    body = [(40, 158), (36, 104), (44, 72), (50, 30), (70, 64), (92, 54), (114, 64), (134, 30),
            (140, 72), (148, 104), (144, 158), (128, 146), (114, 164), (100, 148), (86, 166), (72, 148), (56, 164)]
    gradient_fill(s, white(lambda m, c: pygame.draw.polygon(m, c, body)), (92, 72, 104), (34, 24, 40), (0, 40, S, 120))
    pygame.draw.polygon(s, INK, body, 5)
    # 몸 결 (어두운 줄)
    for x0 in (66, 92, 118):
        pygame.draw.line(s, (26, 18, 30), (x0, 130), (x0 + 4, 150), 3)

    # 눈: 빛나는 주황
    for ex in (72, 112):
        glow(s, (ex, 100), 26, (255, 140, 40), 160)
        pygame.draw.ellipse(s, (255, 168, 60), (ex - 11, 92, 22, 16))
        pygame.draw.ellipse(s, (255, 236, 150), (ex - 5, 96, 10, 8))
        pygame.draw.ellipse(s, INK, (ex - 11, 92, 22, 16), 3)
    # 이빨
    teeth = [(70, 124), (78, 134), (86, 124), (94, 134), (102, 124), (110, 134), (116, 124)]
    pygame.draw.lines(s, (240, 226, 200), False, teeth, 4)
    return s


def dummy():
    """허수아비: 나무 기둥과 가로대, 삼베 자루 머리(바느질 X 눈), 지푸라기, 과녁."""
    s = canvas()
    shadow(s, w=90)

    def wood(rect, horiz):
        gradient_fill(s, white(lambda m, c: pygame.draw.rect(m, c, rect, border_radius=5)),
                      (176, 124, 74), (110, 70, 38), rect if not horiz else (rect[0], rect[1], rect[2], rect[3]))
        pygame.draw.rect(s, INK, rect, 4, border_radius=5)

    wood((84, 86, 16, 86), False)                                # 기둥
    wood((30, 100, 124, 16), True)                               # 가로대
    for x, d in ((30, -1), (154, 1)):                            # 지푸라기
        for k in range(5):
            pygame.draw.line(s, (232, 196, 92), (x, 102 + k * 3), (x + d * (14 + k * 2), 96 + k * 6), 3)

    # 가슴의 과녁
    for r, col in ((20, (238, 226, 200)), (14, (196, 70, 50)), (8, (238, 226, 200)), (4, (196, 70, 50))):
        pygame.draw.circle(s, col, (92, 134), r)
    pygame.draw.circle(s, INK, (92, 134), 20, 3)

    # 삼베 자루 머리
    gradient_fill(s, white(lambda m, c: pygame.draw.circle(m, c, (92, 62), 30)), (222, 190, 132), (170, 130, 80), (0, 32, S, 60))
    pygame.draw.circle(s, INK, (92, 62), 30, 4)
    for ex in (80, 104):                                          # 바느질 X 눈
        pygame.draw.line(s, INK, (ex - 6, 54), (ex + 6, 66), 4)
        pygame.draw.line(s, INK, (ex + 6, 54), (ex - 6, 66), 4)
    for k in range(5):                                            # 바느질 입
        pygame.draw.line(s, INK, (78 + k * 7, 76), (82 + k * 7, 76), 3)
    pygame.draw.line(s, (120, 80, 40), (68, 88), (116, 88), 6)    # 목 끈
    # 머리 위 지푸라기
    for k in range(6):
        pygame.draw.line(s, (232, 196, 92), (80 + k * 5, 34), (74 + k * 7, 22), 3)
    return s


# 받침 색: (윗면, 옆면, 테두리 장식)
BASES = {
    "player": ((218, 170, 82), (150, 104, 40), (250, 214, 130)),    # 놋쇠
    "chaser": ((70, 64, 72), (36, 32, 40), (140, 96, 170)),          # 무쇠 + 보라 띠
    "dummy": ((168, 116, 66), (110, 70, 38), (206, 160, 104)),       # 나무
}


def piece(figure, kind):
    """보드게임 말: 그림자 + 둥근 받침(옆면·윗면) + 그 위에 선 그림(조금 작게)."""
    top, side, trim = BASES[kind]
    s = canvas()
    sh = canvas()
    pygame.draw.ellipse(sh, (20, 10, 0, 120), (26, 146, 140, 36))
    s.blit(pygame.transform.smoothscale(pygame.transform.smoothscale(sh, (23, 23)), (S, S)), (4, 2))
    base = pygame.Rect(28, 134, 128, 40)
    pygame.draw.ellipse(s, side, base.move(0, 10))                  # 옆면 (두께)
    pygame.draw.rect(s, side, (base.x, base.centery, base.w, 10))
    pygame.draw.ellipse(s, INK, base.move(0, 10), 4)
    pygame.draw.ellipse(s, top, base)                               # 윗면
    pygame.draw.ellipse(s, trim, base.inflate(-16, -10), 3)
    pygame.draw.ellipse(s, INK, base, 4)
    fig = pygame.transform.smoothscale(figure, (int(S * 0.8), int(S * 0.8)))
    s.blit(fig, ((S - fig.get_width()) // 2, 4))                    # 발이 받침 윗면에 오도록
    return s


def main():
    pygame.init()
    pygame.display.set_mode((1, 1))
    for name, fn in (("player", player), ("chaser", chaser), ("dummy", dummy)):
        img = pygame.transform.smoothscale(piece(fn(), name), (OUT, OUT))
        pygame.image.save(img, os.path.join(IMG_DIR, name + ".png"))
        print("저장:", name + ".png")


if __name__ == "__main__":
    main()
