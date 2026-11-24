"""
화면(Scene) 모음 (담당: 표현 / 화면 전환 연결: 개발 담당)

화면 흐름 (기획서 4-4)
  타이틀 → 조작 설명 → 스테이지 선택 → 1층 → 2층 → 3층 → 결과 → 다시 하기
  플레이 중 ESC → 일시정지

모든 화면은 같은 세 함수를 가짐
  handle(event) : 입력 처리. 다른 화면으로 가야 하면 그 이름을 반환
  update(dt)    : 시간 흐름 처리 (dt = 지난 프레임 이후 ms)
  draw(surf)    : 그리기

격자·유닛·카드 그림은 assets.py 의 draw_... 함수를 부름 (그림 에셋은 assets.py 에서 교체)
"""
import math

import pygame

import assets
import ui
from settings import (W, H, N, CELL, GRID_X, GRID_Y, INK, INK_LIGHT, CREAM, GOLD, WAX,
                      MAX_HP, QUEUE_SIZE, MAGAZINE_SIZE, STEP_DELAY, OP_SHOW_TIME,
                      MOVE_SPEED, SORT_DELAY)
from ui import label, font, Button
from battle import Battle
from cards import card_en
from board import EXIT
from stages import STAGE_NAMES, STAGE_DESC, STAGE_LEVEL, STAGES, stars

STAR = (196, 128, 30)   # 양피지 위 별 색 (진한 금)
SHOT_MS_PER_CELL = 45   # 탄이 한 칸 날아가는 시간(ms)
_vignette = []


def _hurt_vignette():
    """화면 가장자리가 붉은 테두리 (플레이어 피격 때). 한 번 만들어 재사용."""
    if not _vignette:
        v = pygame.Surface((W, H), pygame.SRCALPHA)
        for i in range(60):
            a = int(110 * (1 - i / 60) ** 2)
            pygame.draw.rect(v, (190, 20, 16, a), (i * 2, i * 2, W - i * 4, H - i * 4), 2)
        _vignette.append(v)
    return _vignette[0]


class Scene:
    """모든 화면의 기본형. 필요한 함수만 덮어쓰면 됨."""

    def handle(self, event):
        return None

    def update(self, dt):
        return None

    def draw(self, surf):
        pass


# ======================================================================
class TitleScene(Scene):
    """타이틀: 탁자 위 두루마리 + 흩어 놓은 카드와 말."""

    def __init__(self):
        self.start = Button((W // 2 - 120, 468, 240, 66), "게임 시작", 26)

    def handle(self, event):
        if self.start.clicked(event):
            return "howto"

    def draw(self, surf):
        # 왼쪽: 부채꼴로 펼친 카드, 오른쪽: 세워 둔 말과 탄 보석
        for k, (name, ang, pos) in enumerate((("발사", 18, (150, 470)), ("재장전", 4, (200, 450)),
                                               ("앞으로 이동", -12, (250, 462)))):
            assets.draw_card_rotated(surf, name, pos, ang, 1.5)
        assets.draw_piece(surf, "chaser", (1010, 430), 130)
        assets.draw_piece(surf, "player", (900, 470), 120)
        assets.draw_piece(surf, "dummy", (1090, 520), 96)
        for k, b in enumerate(("화염탄", "빙결탄", "폭발탄")):
            assets.draw_item(surf, pygame.Rect(930 + k * 54, 600, 56, 56), b)

        ui.scroll(surf, (W // 2 - 290, 96, 580, 320))
        label(surf, W // 2, 146, "마법 학교 졸업 시험", 17, INK_LIGHT, width=500, max_lines=1)
        ui.title(surf, W // 2, 210, "Grid Hunt", 70, deco_font=True)
        label(surf, W // 2, 268, "격 자 사 냥", 30, INK, width=500, max_lines=1)
        pygame.draw.line(surf, INK_LIGHT, (W // 2 - 180, 298), (W // 2 + 180, 298), 2)
        ui.gem(surf, (W // 2, 298), 6)
        label(surf, W // 2, 346, "카드로 주문 순서를 짜고, 마법 탄창 하나로\n지하 미궁을 탈출하라", 19, INK, width=440, max_lines=2)
        self.start.draw(surf)


# ======================================================================
class HowToScene(Scene):
    """조작 설명 (기획서 4-4: 타이틀 → 조작 설명 → 1번 방). 규칙마다 게임 그림으로 만든 작은 그림 + 짧은 설명."""

    RULES = [
        "카드를 끌어다 행동 큐에 놓는다 (최대 5장, enqueue)",
        "Enter: 큐 맨 앞부터 하나씩 실행 (dequeue, 먼저 넣은 것이 먼저)",
        "실행이 끝나면 추적자가 머리 위 숫자만큼 최단 경로(BFS)로 다가온다",
        "탄을 밟으면 탄창 맨 위에 쌓이고, 발사하면 맨 위 탄이 나간다 (push / pop)",
        "재장전: 탄을 다 꺼내 약한 순으로 정렬해 다시 넣는다 → 센 탄이 맨 위",
        "적과 부딪히면 체력 -1, 다음 행동이 버려지고 맨 뒤에 기절",
        "뒤집기 타일을 밟으면 남은 행동 순서가 거꾸로",
        "적을 모두 잡으면 출구가 열린다. 적은 턴일수록 별이 많다",
    ]
    KEYS = "Enter 실행   ·   R 방 다시 시작   ·   ESC 일시정지"

    def __init__(self):
        self.next = Button((W // 2 - 110, 618, 220, 62), "시작하기", 24)

    def handle(self, event):
        if self.next.clicked(event) or (event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN):
            return "select"

    def draw(self, surf):
        ui.scroll(surf, (90, 34, W - 180, 560))
        label(surf, W // 2, 76, "조작 설명", 32, INK, serif=True, width=600, max_lines=1)
        pygame.draw.line(surf, INK_LIGHT, (W // 2 - 140, 100), (W // 2 + 140, 100), 2)
        pics = [self.pic_drag, self.pic_run, self.pic_chase, self.pic_pickup,
                self.pic_reload, self.pic_hurt, self.pic_flip, self.pic_exit]
        for i, (text, pic) in enumerate(zip(self.RULES, pics)):
            box = pygame.Rect(122 + (i % 4) * 242, 114 + (i // 4) * 218, 228, 206)
            ui.slot(surf, box)
            ui.seal(surf, (box.x + 18, box.y + 18), str(i + 1), 13)
            pic(surf, box.centerx, box.y + 72)
            label(surf, box.centerx, box.y + 164, text, 14, INK, width=box.w - 22, max_lines=3)
        label(surf, W // 2, 566, self.KEYS, 16, INK, width=900, max_lines=1)
        self.next.draw(surf)

    # ---------- 작은 그림들 (게임 그림을 그대로 작게 써서 실제 화면과 같아 보이게) ----------
    def arrow(self, surf, a, b, color=INK):
        pygame.draw.line(surf, color, a, b, 3)
        ang = math.atan2(b[1] - a[1], b[0] - a[0])
        for d in (2.6, -2.6):
            pygame.draw.line(surf, color, b, (b[0] + 9 * math.cos(ang + d), b[1] + 9 * math.sin(ang + d)), 3)

    def mini_slot(self, surf, rect, n, name, gold=False):
        ui.slot(surf, rect, highlight=gold)
        ui.seal(surf, (rect.x + 13, rect.centery), str(n), 10)
        ui.deco_label(surf, (rect.x + 28 + rect.right - 4) // 2, rect.centery + 1, card_en(name), 12, INK, rect.w - 34)

    def mini_grid(self, surf, x, y, cols, rows, c=36):
        for k in range(cols + 1):
            pygame.draw.line(surf, INK_LIGHT, (x + k * c, y), (x + k * c, y + rows * c), 1)
        for k in range(rows + 1):
            pygame.draw.line(surf, INK_LIGHT, (x, y + k * c), (x + cols * c, y + k * c), 1)
        return lambda col, row: pygame.Rect(x + col * c, y + row * c, c, c)

    def pic_drag(self, surf, cx, cy):
        assets.draw_card(surf, pygame.Rect(cx - 96, cy - 34, 52, 66), "앞으로 이동")
        self.arrow(surf, (cx - 36, cy), (cx - 6, cy))
        self.mini_slot(surf, pygame.Rect(cx, cy - 18, 96, 36), 1, "앞으로 이동", gold=True)

    def pic_run(self, surf, cx, cy):
        self.mini_slot(surf, pygame.Rect(cx - 100, cy - 40, 96, 34), 1, "발사", gold=True)
        self.mini_slot(surf, pygame.Rect(cx - 100, cy + 4, 96, 34), 2, "앞으로 이동")
        self.arrow(surf, (cx, cy - 23), (cx + 34, cy - 4))
        assets.draw_player(surf, pygame.Rect(cx + 44, cy - 24, 46, 46), 1)

    def pic_chase(self, surf, cx, cy):
        cell = self.mini_grid(surf, cx - 72, cy - 36, 4, 2)
        for col, row in ((1, 0), (2, 0), (2, 1)):
            pygame.draw.circle(surf, WAX, cell(col, row).center, 4)
        e = cell(0, 0)
        assets.draw_enemy(surf, e, "chaser")
        img = font(11).render("2", True, INK)
        b = img.get_rect().inflate(8, 2)
        b.width = b.height
        b.topright = (e.right, e.y)
        pygame.draw.rect(surf, CREAM, b, border_radius=7)
        pygame.draw.rect(surf, INK, b, 2, border_radius=7)
        surf.blit(img, img.get_rect(center=b.center))
        assets.draw_player(surf, cell(3, 1), 3)

    def pic_pickup(self, surf, cx, cy):
        for k, name in enumerate(("화염탄", "빙결탄", "폭발탄")):
            assets.draw_item(surf, pygame.Rect(cx - 104 + k * 30, cy - 18, 36, 36), name)
        self.arrow(surf, (cx - 10, cy), (cx + 18, cy))
        for k, name in enumerate(("화염탄", "빙결탄", "폭발탄")):          # 아래부터 쌓임 → 마지막에 주운 게 맨 위
            r = pygame.Rect(cx + 26, cy + 22 - k * 26, 64, 24)
            ui.slot(surf, r, highlight=(k == 2))
            assets.draw_item(surf, pygame.Rect(r.x + 20, r.y - 4, 30, 30), name)
        label(surf, cx + 104, cy - 32, "top", 11, WAX)

    def pic_reload(self, surf, cx, cy):
        for side, order in ((-1, ("폭발탄", "화염탄", "빙결탄")), (1, ("빙결탄", "화염탄", "폭발탄"))):
            x = cx + side * 56 - 28
            for k, name in enumerate(order):
                r = pygame.Rect(x, cy + 22 - k * 26, 56, 24)
                ui.slot(surf, r, highlight=(k == 2 and side == 1))
                assets.draw_item(surf, pygame.Rect(r.x + 13, r.y - 4, 30, 30), name)
        self.arrow(surf, (cx - 18, cy), (cx + 18, cy))
        label(surf, cx, cy - 36, "정렬", 12, INK_LIGHT)

    def pic_hurt(self, surf, cx, cy):
        p = pygame.Rect(cx - 96, cy - 26, 46, 46)
        red = pygame.Surface((46, 46), pygame.SRCALPHA)
        pygame.draw.circle(red, (220, 40, 30, 120), (23, 23), 23)
        assets.draw_player(surf, p, 1)
        surf.blit(red, p)
        assets.draw_enemy(surf, p.move(42, 0), "chaser")
        label(surf, p.centerx, p.y - 6, "-1", 16, WAX)
        self.mini_slot(surf, pygame.Rect(cx + 6, cy - 16, 96, 34), 5, "기절")

    def pic_flip(self, surf, cx, cy):
        assets.draw_tile(surf, pygame.Rect(cx - 23, cy - 23, 46, 46), "R")
        for k in range(3):
            ui.seal(surf, (cx - 78, cy - 26 + k * 26), str(k + 1), 10)
            ui.seal(surf, (cx + 78, cy - 26 + k * 26), str(3 - k), 10)
        self.arrow(surf, (cx - 60, cy), (cx - 30, cy))
        self.arrow(surf, (cx + 30, cy), (cx + 60, cy))

    def pic_exit(self, surf, cx, cy):
        assets.draw_tile(surf, pygame.Rect(cx - 96, cy - 30, 50, 50), "X")
        self.arrow(surf, (cx - 38, cy - 5), (cx - 8, cy - 5))
        assets.draw_tile(surf, pygame.Rect(cx, cy - 30, 50, 50), "X_open")
        label(surf, cx + 76, cy - 6, "★★★", 16, STAR)


# ======================================================================
class SelectScene(Scene):
    """스테이지 선택: 방마다 양피지 지도 한 장 (미리보기 + 난이도). 고른 방부터 시작."""

    def __init__(self, game):
        self.game = game
        self.cards = [pygame.Rect(W // 2 - 375 + i * 260, 150, 230, 440) for i in range(len(STAGE_NAMES))]

    def handle(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, r in enumerate(self.cards):
                if r.collidepoint(event.pos):
                    assets.play("click")
                    self.game.start_from(i + 1)
                    return "play"

    def draw(self, surf):
        ui.title(surf, W // 2, 82, "스테이지 선택", 44)
        mouse = pygame.mouse.get_pos()
        for i, r in enumerate(self.cards):
            hover = r.collidepoint(mouse)
            rr = r.move(0, -8) if hover else r                # 마우스를 올리면 살짝 들림
            ui.panel(surf, rr)
            if hover:
                pygame.draw.rect(surf, GOLD, rr.inflate(6, 6), 4, border_radius=12)
            label(surf, rr.centerx, rr.y + 36, STAGE_NAMES[i], 24, INK, width=196, max_lines=1)
            lv = STAGE_LEVEL[i]
            label(surf, rr.centerx, rr.y + 70, "★" * lv + "☆" * (5 - lv), 20, STAR)
            self.minimap(surf, STAGES[i], pygame.Rect(rr.centerx - 90, rr.y + 92, 180, 180))
            label(surf, rr.centerx, rr.y + 306, STAGE_DESC[i], 16, INK, width=196, max_lines=2)
            ui.seal(surf, (rr.centerx, rr.y + 360), str(i + 1), 22)
            label(surf, rr.centerx, rr.y + 404, "눌러서 시작", 14, INK_LIGHT, width=196, max_lines=1)

    def minimap(self, surf, stage_map, rect):
        """맵 미리보기: 잉크로 그린 작은 지도 (벽, 출구, 플레이어, 적, 탄)."""
        c = rect.w // N
        pygame.draw.rect(surf, INK, rect.inflate(6, 6), 2)
        for r, row in enumerate(stage_map):
            for col, ch in enumerate(row):
                cell = pygame.Rect(rect.x + col * c, rect.y + r * c, c, c)
                pygame.draw.rect(surf, INK_LIGHT, cell, 1)
                ctr = cell.center
                if ch == "#":
                    pygame.draw.rect(surf, (110, 100, 88), cell.inflate(-2, -2))
                elif ch == "X":
                    pygame.draw.rect(surf, (138, 86, 46), cell.inflate(-5, -3), border_radius=4)
                elif ch == "R":
                    pygame.draw.circle(surf, GOLD, ctr, c // 2 - 2)
                elif ch == "P":
                    pygame.draw.circle(surf, GOLD, ctr, c // 2 - 2)
                    pygame.draw.circle(surf, INK, ctr, c // 2 - 2, 2)
                elif ch == "E":
                    pygame.draw.circle(surf, (70, 52, 92), ctr, c // 2 - 2)
                elif ch == "D":
                    pygame.draw.circle(surf, (168, 116, 66), ctr, c // 2 - 3)
                elif ch in "fib":
                    col_ = assets.BULLET_COLOR[{"f": "화염탄", "i": "빙결탄", "b": "폭발탄"}[ch]]
                    pygame.draw.circle(surf, col_, ctr, c // 2 - 4)


# ======================================================================
class PlayScene(Scene):
    """
    메인 플레이 화면. 규칙은 Battle 이 처리하고, 여기서는 입력 전달과 그리기만 함.
    배치: 왼쪽 카드 더미·버린 카드·탄창 / 가운데 격자 / 오른쪽 행동 큐 / 아래 손패
    """

    def __init__(self, game):
        self.game = game
        self.battle = Battle(game.stage)
        self.timer = 0  # 실행 중 다음 행동까지 남은 시간 계산용
        self.floats = []  # 화면에 떠 있는 자료구조 연산 글자 [where, 글자, 지난 시간(ms)]
        self.reset_anim()

        # 클릭·드롭 영역
        self.run_button = Button((W - 190, 545, 140, 55), "실행", 20)
        self.hand_rects = [pygame.Rect(280 + i * 112, 560, 100, 115) for i in range(6)]
        self.queue_rects = [pygame.Rect(W - 190, 105 + i * 68, 140, 55) for i in range(QUEUE_SIZE)]
        self.queue_panel = pygame.Rect(W - 210, 30, 180, 490)   # 손패 카드를 여기 놓으면 큐에 들어감
        self.hand_panel = pygame.Rect(260, 520, W - 490, 170)    # 큐 카드를 여기 놓으면 손패로 돌아감
        self.drag = None   # 끌고 있는 카드 {"src": "hand"/"queue", "index", "card", "pos", "grab"}

    # ---------- 입력 ----------
    def handle(self, event):
        b = self.battle
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "pause"
            if event.key == pygame.K_r:                 # 이 스테이지 처음부터
                self.battle = Battle(self.game.stage)
                self.floats = []
                self.drag = None
                self.reset_anim()
                return None
            if event.key == pygame.K_RETURN:
                b.start_run()
        if self.run_button.clicked(event):
            b.start_run()

        # 드래그 앤 드롭: 누르면 집고, 움직이면 따라오고, 떼면 놓은 곳에 따라 처리 (계획 중에만)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and b.phase == "plan":
            for i, r in enumerate(self.hand_rects):
                if i < len(b.hand) and r.collidepoint(event.pos):
                    self.start_drag("hand", i, b.hand[i], r, event.pos)
                    return None
            cards = b.queue.to_list()
            for i, r in enumerate(self.queue_rects):
                if i < len(cards) and r.collidepoint(event.pos):
                    self.start_drag("queue", i, cards[i], r, event.pos)
                    return None
        elif event.type == pygame.MOUSEMOTION and self.drag:
            self.drag["pos"] = event.pos
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.drag:
            d, self.drag = self.drag, None
            before = len(b.queue)
            if d["src"] == "hand" and self.queue_panel.collidepoint(event.pos):
                b.queue_card(d["index"])            # 큐 맨 뒤에 enqueue
            elif d["src"] == "queue" and not self.queue_panel.collidepoint(event.pos):
                b.unqueue_card(d["index"])          # 큐 밖에 놓으면 손패로
            if len(b.queue) != before:              # 실제로 카드가 옮겨졌을 때만 '착'
                assets.play("card")
        return None

    def start_drag(self, src, index, card, rect, mouse):
        """카드 집기. grab = 카드 왼쪽 위에서 마우스까지 거리 (집은 자리 그대로 따라오게)."""
        self.drag = {"src": src, "index": index, "card": card, "pos": mouse,
                     "grab": (mouse[0] - rect.x, mouse[1] - rect.y)}

    # ---------- 애니메이션 ----------
    def reset_anim(self):
        """애니메이션 상태 초기화 (새 판, R 다시 시작)."""
        self.moving = {}       # id(유닛) → {"at": 지금 그려지는 (c, r) 실수 좌표, "goal": 목표 칸, "path": 남은 칸들}
        self.sort_frames = []  # 재장전 정렬 과정: 화면에 차례로 보여줄 탄창 상태들
        self.sort_timer = 0
        self.seen_reload = self.battle.magazine.reload_count
        self.effects = []      # 진행 중인 연출 (발사 탄, 터짐, 적 맞음, 플레이어 맞음). 't' = 지난 시간(ms)

    # ---------- 발사·피격 연출 ----------
    def add_effects(self, events):
        """Battle 이 남긴 연출 기록을 받아 시간 정보를 붙임. 적이 맞는 연출은 탄이 도착한 뒤에 시작."""
        delay = 0
        for f in events:
            f = dict(f)
            if f["kind"] == "shot":
                dist = abs(f["end"][0] - f["start"][0]) + abs(f["end"][1] - f["start"][1])
                f["dur"] = max(140, SHOT_MS_PER_CELL * dist)
                f["t"] = 0
                delay = f["dur"]
            elif f["kind"] == "enemy_hit":
                f["dur"], f["t"] = 520, -delay          # 음수 = 아직 탄이 날아가는 중
            elif f["kind"] == "hurt":
                f["dur"], f["t"] = 560, 0
            self.effects.append(f)

    def update_effects(self, dt):
        for f in self.effects:
            before = f["t"]
            f["t"] += dt
            if f["kind"] == "shot" and before < f["dur"] <= f["t"]:      # 도착 → 터짐
                self.effects.append({"kind": "burst", "pos": f["end"], "bullet": f["bullet"],
                                     "big": f["stop"] != "miss", "t": f["t"] - f["dur"], "dur": 380})
        self.effects = [f for f in self.effects if f["t"] < f["dur"]]

    def shot_flying(self):
        """탄이 날아가는 중이면 True (그동안은 다음 행동을 멈춤)."""
        return any(f["kind"] == "shot" for f in self.effects)

    def cell_center(self, pos):
        c, r = pos
        return (GRID_X + c * CELL + CELL / 2, GRID_Y + r * CELL + CELL / 2)

    def shake(self, kind, pos):
        """맞은 유닛을 좌우로 흔드는 양 (px)."""
        dx = 0.0
        for f in self.effects:
            if f["kind"] == kind and f["pos"] == pos and 0 <= f["t"] < 260:
                k = 1 - f["t"] / 260
                dx += math.sin(f["t"] * 0.09) * 6 * k
        return int(dx), 0

    def draw_effects(self, surf):
        """날아가는 탄, 터짐, 맞은 적 번쩍임·숫자·사라짐, 플레이어 피격."""
        for f in self.effects:
            kind, t = f["kind"], f["t"]
            if kind == "shot":
                self.draw_shot(surf, f)
            elif kind == "burst":
                self.draw_burst(surf, f)
            elif kind == "enemy_hit":
                self.draw_enemy_hit(surf, f)
            elif kind == "hurt":
                self.draw_hurt(surf, f)

    def draw_shot(self, surf, f):
        """탄: 빛나는 구슬 + 꼬리. 탄 색은 탄 종류 색."""
        color = assets.BULLET_COLOR[f["bullet"]]
        (x0, y0), (x1, y1) = self.cell_center(f["start"]), self.cell_center(f["end"])
        if f["stop"] != "enemy":                 # 벽·바깥이면 칸 가장자리에서 멈춤
            x1, y1 = x1 - (x1 - x0) / max(1, abs(x1 - x0) + abs(y1 - y0)) * CELL / 2, \
                     y1 - (y1 - y0) / max(1, abs(x1 - x0) + abs(y1 - y0)) * CELL / 2
        k = min(1.0, f["t"] / f["dur"])
        glow = pygame.Surface((W, H), pygame.SRCALPHA)
        for i in range(6, 0, -1):                # 꼬리: 지나온 자리에 흐려지는 구슬
            kk = max(0.0, k - i * 0.05)
            x, y = x0 + (x1 - x0) * kk, y0 + (y1 - y0) * kk
            pygame.draw.circle(glow, (*color, 26 * (7 - i)), (x, y), 9 - i)
        x, y = x0 + (x1 - x0) * k, y0 + (y1 - y0) * k
        pygame.draw.circle(glow, (*color, 90), (x, y), 15)
        surf.blit(glow, (0, 0))
        pygame.draw.circle(surf, color, (x, y), 8)
        pygame.draw.circle(surf, CREAM, (x - 2, y - 2), 3)
        pygame.draw.circle(surf, INK, (x, y), 8, 2)

    def draw_burst(self, surf, f):
        """도착한 자리에서 퍼지는 고리 + 파편."""
        t, dur = max(0, f["t"]), f["dur"]
        k = t / dur
        cx, cy = self.cell_center(f["pos"])
        color = assets.BULLET_COLOR[f["bullet"]]
        big = 1.6 if f["bullet"] == "폭발탄" else 1.0
        layer = pygame.Surface((W, H), pygame.SRCALPHA)
        a = int(220 * (1 - k))
        pygame.draw.circle(layer, (*color, a), (cx, cy), int((6 + 22 * k) * big), 4)
        pygame.draw.circle(layer, (*CREAM, int(a * 0.8)), (cx, cy), int((4 + 10 * (1 - k)) * big))
        for i in range(8):
            ang = i * math.pi / 4 + 0.3
            d = (8 + 24 * k) * big
            pygame.draw.circle(layer, (*color, a), (cx + math.cos(ang) * d, cy + math.sin(ang) * d), max(1, int(4 * (1 - k))))
        surf.blit(layer, (0, 0))

    def draw_enemy_hit(self, surf, f):
        """적이 맞음: 흰 번쩍임 + 빨간 피해 숫자. 쓰러졌으면 흐려지며 위로 사라짐."""
        t = f["t"]
        rect = self.cell_rect(f["pos"])
        if f["killed"]:                           # 판에서는 이미 지워졌으니 여기서 그림
            fade = 1.0 if t < 0 else max(0.0, 1 - t / 420)
            if fade > 0:
                ghost = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
                assets.draw_enemy(ghost, pygame.Rect(0, 0, CELL, CELL), f["enemy_kind"])
                ghost.set_alpha(int(255 * fade))
                surf.blit(ghost, rect.move(self.shake("enemy_hit", f["pos"])[0], -int(max(0, t) / 25)))
        if t < 0:
            return
        if t < 160:                               # 번쩍
            flash = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
            pygame.draw.circle(flash, (255, 250, 230, int(200 * (1 - t / 160))), (CELL // 2, CELL // 2), CELL // 2)
            surf.blit(flash, rect)
        rise = int(t / 18)
        alpha = 255 if t < 300 else int(255 * (1 - (t - 300) / 220))
        text = ui.font(22).render(f"-{f['damage']}", True, WAX)
        outline = ui.font(22).render(f"-{f['damage']}", True, CREAM)
        tag = pygame.Surface((text.get_width() + 4, text.get_height() + 4), pygame.SRCALPHA)
        for ox, oy in ((0, 2), (4, 2), (2, 0), (2, 4)):
            tag.blit(outline, (ox, oy))
        tag.blit(text, (2, 2))
        tag.set_alpha(max(0, alpha))
        surf.blit(tag, tag.get_rect(center=(rect.centerx, rect.y - 4 - rise)))

    def draw_hurt(self, surf, f):
        """플레이어가 맞음: 화면 가장자리 붉은 빛 + 칸 붉은 번쩍임 + '-1'."""
        t, dur = f["t"], f["dur"]
        k = 1 - t / dur
        vign = _hurt_vignette()
        vign.set_alpha(int(230 * k))
        surf.blit(vign, (0, 0))
        rect = self.cell_rect(f["pos"])
        if t < 220:
            red = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
            pygame.draw.circle(red, (220, 40, 30, int(170 * (1 - t / 220))), (CELL // 2, CELL // 2), CELL // 2)
            surf.blit(red, rect)
        text = ui.font(22).render("-1", True, (200, 30, 24))
        text.set_alpha(int(255 * k))
        surf.blit(text, text.get_rect(center=(rect.centerx, rect.y - 6 - int(t / 20))))

    def track(self, unit, trail):
        """유닛의 칸이 바뀌었으면 지나간 칸(trail)을 따라 미끄러지도록 등록."""
        m = self.moving.get(id(unit))
        if m is None:
            self.moving[id(unit)] = {"at": unit.pos, "goal": unit.pos, "path": []}
            return
        if m["goal"] != unit.pos:
            m["path"] += trail if trail and trail[-1] == unit.pos else [unit.pos]
            m["goal"] = unit.pos

    def slide(self, dt):
        """등록된 경로를 따라 한 칸씩 이동 (MOVE_SPEED 칸/ms)."""
        for m in self.moving.values():
            budget = MOVE_SPEED * dt
            while m["path"] and budget > 0:
                (x, y), (tx, ty) = m["at"], m["path"][0]
                dist = abs(tx - x) + abs(ty - y)
                if dist <= budget:
                    m["at"] = m["path"].pop(0)
                    budget -= dist
                else:
                    m["at"] = (x + (tx - x) * budget / dist, y + (ty - y) * budget / dist)
                    budget = 0

    def shown_pos(self, unit):
        """화면에 그릴 위치 (움직이는 중이면 칸 사이)."""
        m = self.moving.get(id(unit))
        return m["at"] if m else unit.pos

    # ---------- 시간 ----------
    def update(self, dt):
        b = self.battle

        # 재장전 정렬 애니메이션: 새 재장전이 일어났으면 정렬 단계를 차례로 보여 줌
        if b.magazine.reload_count != self.seen_reload:
            self.seen_reload = b.magazine.reload_count
            self.sort_frames = [b.magazine.last_before] + b.magazine.last_sort_steps
            self.sort_total = len(self.sort_frames)
            self.sort_timer = 0
        if self.sort_frames:
            self.sort_timer += dt
            if self.sort_timer >= SORT_DELAY:
                self.sort_timer = 0
                self.sort_frames.pop(0)

        # 실행 중이면 STEP_DELAY 마다 행동 하나씩 처리 (정렬 애니메이션 중에는 잠깐 멈춤)
        if b.phase == "run" and not self.sort_frames and not self.shot_flying():
            self.timer += dt
            if self.timer >= STEP_DELAY:
                self.timer = 0
                b.step()

        # 자료구조 연산 글자: 새로 생긴 것은 추가, 오래된 것은 지움
        for where, text in b.take_ops():
            self.floats.append([where, text, 0])
        for f in self.floats:
            f[2] += dt
        self.floats = [f for f in self.floats if f[2] < OP_SHOW_TIME]

        # 이동 애니메이션
        self.track(b.board.player, None)
        for e in b.board.enemies:
            self.track(e, e.trail)
        self.slide(dt)

        # 효과음 + 발사·피격 연출
        for name in b.take_sounds():
            assets.play(name)
        self.add_effects(b.take_fx())
        self.update_effects(dt)

        # 스테이지가 끝났으면 다음 화면으로
        if b.state == "clear":
            return self.game.stage_cleared(b.turn)
        if b.state == "fail":
            return self.game.stage_failed(b.turn)
        return None

    # ---------- 그리기 ----------
    def cell_rect(self, pos):
        c, r = pos
        return pygame.Rect(round(GRID_X + c * CELL), round(GRID_Y + r * CELL), CELL, CELL)

    def draw(self, surf):
        ui.board(surf)
        self.draw_grid(surf)
        self.draw_left(surf)
        self.draw_info(surf)
        self.draw_queue(surf)
        self.draw_hand(surf)
        self.draw_effects(surf)
        self.draw_ops(surf)
        self.draw_drag(surf)

    def draw_drag(self, surf):
        """끌고 있는 카드를 마우스 위치에 그리고, 놓을 수 있는 곳을 금색으로 표시."""
        d = self.drag
        if not d:
            return
        target = self.queue_panel if d["src"] == "hand" else self.hand_panel
        pygame.draw.rect(surf, GOLD, target.inflate(8, 8), 4, border_radius=14)
        mx, my = d["pos"]
        gx, gy = d["grab"]
        if d["src"] == "hand":
            assets.draw_card(surf, pygame.Rect(mx - gx, my - gy, 100, 115), d["card"])
        else:                                       # 큐 칸 모양 그대로
            rect = pygame.Rect(mx - gx, my - gy, 140, 55)
            ui.slot(surf, rect, highlight=True)
            ui.deco_label(surf, rect.centerx, rect.centery + 1, card_en(d["card"]), 16, INK, width=126)

    # 연산 글자를 띄울 위치 (영역별 기준점)
    OP_POS = {
        "deck": (131, 194),          # 카드 더미 아래
        "magazine": (131, 372),      # 마법 탄창 제목 위
        "queue": (W - 120, 496),     # 행동 큐 아래
        "grid": (891, 176),          # 오른쪽 상황판 (BFS)
    }
    # 연산 글자가 나가면 안 되는 가로 범위 (패널 안쪽)
    OP_AREA = {"deck": (32, 230), "magazine": (32, 230), "queue": (998, 1162), "grid": (814, 968)}

    def draw_ops(self, surf):
        """pop(), enqueue() 같은 연산 이름을 잠깐 띄웠다가 흐려지며 사라지게 (기획서 독창 요소 ③)."""
        shown = {}  # 영역별로 이미 그린 줄 수
        for where, text, age in reversed(self.floats):    # 최신 것부터
            k = shown.get(where, 0)
            if k >= 1:                                    # 영역마다 가장 최근 것 하나만 (다른 글자를 가리지 않게)
                continue
            shown[where] = k + 1
            x, y = self.OP_POS[where]
            left, right = self.OP_AREA[where]
            size = ui.fit_size(text, 13, right - left - 12)
            lines = ui.wrap(text, size, right - left - 12)       # 그래도 길면 다음 줄로
            imgs = [font(size).render(line, True, INK) for line in lines]
            w = max(i.get_width() for i in imgs) + 10
            h = sum(i.get_height() for i in imgs) + 4
            chip = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.rect(chip, (*CREAM, 235), chip.get_rect(), border_radius=5)
            pygame.draw.rect(chip, (*INK_LIGHT, 255), chip.get_rect(), 1, border_radius=5)
            cy = 2
            for img in imgs:
                chip.blit(img, ((w - img.get_width()) // 2, cy))
                cy += img.get_height()
            chip.set_alpha(int(255 * (1 - age / OP_SHOW_TIME)))
            rect = chip.get_rect(center=(x, y - k * (h + 2) - age // 160))   # 위로 살짝 떠오름
            rect.left = max(rect.left, left)                    # 패널 밖으로 안 나가게
            rect.right = min(rect.right, right)
            surf.blit(chip, rect)

    def draw_left(self, surf):
        """왼쪽 양피지: 카드 더미(뒷면), 버린 카드(맨 위 카드), 마법 탄창."""
        deck = self.battle.deck
        cx = 131
        ui.panel(surf, (24, 18, 214, 684))

        # 카드 더미: 엎어 둔 뒷면이 남은 장수만큼 겹쳐 쌓임 (최대 3장)
        label(surf, cx, 42, "카드 더미", 17, width=190, max_lines=1)
        n = len(deck.draw_pile)
        for k in range(min(3, n)):
            r = pygame.Rect(0, 0, 74, 103)
            r.center = (cx - 4 + k * 4, 122 - k * 4)
            assets.draw_cover(surf, r)
        if n == 0:
            ui.slot(surf, pygame.Rect(cx - 37, 70, 74, 103))
        label(surf, cx + 72, 122, f"{n}장", 14, INK_LIGHT, width=50, max_lines=1)

        # 버린 카드: 맨 위(가장 최근에 버린) 카드만 앞면으로 보임 = 스택의 top
        label(surf, cx, 222, "버린 카드", 17, width=190, max_lines=1)
        r = pygame.Rect(0, 0, 74, 103)
        r.center = (cx, 296)
        top = deck.discard.peek()
        if top:
            if len(deck.discard) > 1:
                assets.draw_cover(surf, r.move(4, 3))
            assets.draw_card(surf, r, top)
        else:
            ui.slot(surf, r)
        label(surf, cx + 72, 296, f"{len(deck.discard)}장", 14, INK_LIGHT, width=50, max_lines=1)

        # 마법 탄창: 아래 칸이 바닥(bottom), 채워진 가장 위 칸이 top (다음에 나갈 탄)
        bullets = self.battle.magazine.to_list()
        title = "마법 탄창"
        if self.sort_frames:                       # 재장전 중: 정렬 단계를 하나씩 보여 줌
            bullets = self.sort_frames[0]
            step = self.sort_total - len(self.sort_frames)
            title = f"선택 정렬 {step}/{self.sort_total - 1}" if self.sort_total > 1 else "이미 정렬됨"
        label(surf, cx, 394, title, 17, width=190, max_lines=1)
        for i in range(MAGAZINE_SIZE):
            y = 414 + (MAGAZINE_SIZE - 1 - i) * 54          # i=0 이 맨 아래 칸
            rect = pygame.Rect(44, y, 174, 48)
            is_top = i == len(bullets) - 1
            ui.slot(surf, rect, highlight=is_top)
            if i < len(bullets):
                assets.draw_item(surf, pygame.Rect(48, y + 1, 46, 46), bullets[i])
                label(surf, 138, y + 24, bullets[i], 15, width=74, max_lines=1)
            if is_top:
                label(surf, 196, y + 24, "다음", 12, WAX, width=36, max_lines=1)

    def draw_grid(self, surf):
        """가운데: 양피지 지도 위의 토큰과 말. 칸·탄·적·플레이어 그림은 assets.py 가 그림."""
        board = self.battle.board
        for r in range(N):
            for c in range(N):
                kind = board.tile((c, r))
                if kind == EXIT and not board.enemies:      # 적을 다 잡으면 출구가 열림
                    kind = "X_open"
                assets.draw_tile(surf, self.cell_rect((c, r)), kind)

        self.draw_range(surf)

        # 바닥의 탄
        for pos, bullet in board.items.items():
            assets.draw_item(surf, self.cell_rect(pos), bullet)

        # 적 + 머리 위 정보(이번 턴 이동 칸 수, 얼어 있으면 '얼음')
        for e in board.enemies:
            rect = self.cell_rect(self.shown_pos(e)).move(self.shake("enemy_hit", e.pos))
            assets.draw_enemy(surf, rect, e.kind)
            if e.frozen > 0:
                self.badge(surf, rect, "얼음", (190, 225, 250))
            elif e.kind == "chaser":
                self.badge(surf, rect, str(e.steps), CREAM)

        # 플레이어
        p = board.player
        assets.draw_player(surf, self.cell_rect(self.shown_pos(p)).move(self.shake("hurt", p.pos)), p.facing)

    def draw_range(self, surf):
        """
        공격 범위: 지금 발사하면 탄창 맨 위 탄이 날아갈 칸을 옅게 칠함.
        맞는 적 칸은 굵은 테두리, 폭발탄이면 부서질 벽에 X 표시. 탄창이 비면 잉크 점만.
        """
        b = self.battle
        cells, stop = b.fire_line()
        top = b.magazine.peek()
        if top is None:                     # 탄이 없으면 쏠 수 없음 → 점으로만 방향 표시
            for pos in cells:
                pygame.draw.circle(surf, INK_LIGHT, self.cell_rect(pos).center, 3)
            return
        color = assets.BULLET_COLOR[top]
        shade = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
        shade.fill((*color, 80))
        for pos in cells:
            surf.blit(shade, self.cell_rect(pos))
        if stop:
            rect = self.cell_rect(stop)
            if b.board.enemy_at(stop):
                pygame.draw.rect(surf, color, rect.inflate(-4, -4), 4, border_radius=6)
            elif top == "폭발탄":
                pygame.draw.line(surf, color, rect.topleft, rect.bottomright, 4)
                pygame.draw.line(surf, color, rect.topright, rect.bottomleft, 4)

    def badge(self, surf, rect, text, color):
        """적 머리 위(칸 오른쪽 위) 작은 표: 이번 턴 이동 칸 수 또는 '얼음'."""
        img = font(12, bold=True).render(text, True, INK)
        box_rect = img.get_rect().inflate(8, 2)
        box_rect.width = max(box_rect.width, box_rect.height)
        box_rect.topright = (rect.right - 1, rect.y + 1)
        pygame.draw.rect(surf, color, box_rect, border_radius=7)
        pygame.draw.rect(surf, INK, box_rect, 2, border_radius=7)
        surf.blit(img, img.get_rect(center=box_rect.center))

    def draw_info(self, surf):
        """지도 오른쪽 상황판: 방 이름, 턴, 체력, 남은 적, 최근 사건, 탄 설명."""
        b = self.battle
        x0, cx = 806, 891
        ui.panel(surf, (x0, 18, 170, 484))
        label(surf, cx, 44, STAGE_NAMES[b.stage_no - 1], 19, width=146, max_lines=1)
        label(surf, cx, 72, f"{b.turn} 턴", 16, width=146, max_lines=1)
        hp = b.board.player.hp
        hearts = font(20).render("♥" * hp, True, WAX)
        empty = font(20).render("♡" * (MAX_HP - hp), True, INK_LIGHT)
        x = cx - (hearts.get_width() + empty.get_width()) // 2
        surf.blit(hearts, (x, 88))
        surf.blit(empty, (x + hearts.get_width(), 88))
        chasers = sum(1 for e in b.board.enemies if e.kind == "chaser")
        dummies = len(b.board.enemies) - chasers
        parts = ([f"추적자 {chasers}"] if chasers else []) + ([f"허수아비 {dummies}"] if dummies else [])
        left = "남은 적  " + " · ".join(parts)
        label(surf, cx, 132, left if b.board.enemies else "적 전멸! 출구로", 13, INK if b.board.enemies else WAX,
              width=146, max_lines=2)
        pygame.draw.line(surf, INK_LIGHT, (x0 + 18, 152), (x0 + 152, 152), 1)

        # 최근 사건 (여러 줄)
        label(surf, cx, 206, "최근 사건", 14, INK_LIGHT, width=146, max_lines=1)
        ui.slot(surf, (x0 + 12, 220, 146, 120))
        label(surf, cx, 280, b.message or "-", 14, width=124, max_lines=5)

        # 탄 설명
        label(surf, cx, 364, "탄 종류", 14, INK_LIGHT, width=146, max_lines=1)
        for k, (name, text) in enumerate((("화염탄", "피해 2"), ("빙결탄", "피해 1 · 멈춤"), ("폭발탄", "피해 1 · 벽 부숨"))):
            y = 380 + k * 38
            assets.draw_item(surf, pygame.Rect(x0 + 10, y - 4, 40, 40), name)
            label(surf, x0 + 106, y + 16, text, 13, width=104, max_lines=2)

    def draw_queue(self, surf):
        """오른쪽: 행동 큐 (위가 먼저 실행되는 front) + 실행 버튼."""
        b = self.battle
        ui.panel(surf, self.queue_panel, "행동 큐")
        label(surf, W - 120, 87, "▲ 먼저 실행 (front)", 13, INK_LIGHT, width=156, max_lines=1)
        cards = b.queue.to_list()
        for i, r in enumerate(self.queue_rects):
            ui.slot(surf, r, highlight=(i == 0 and b.phase == "run" and bool(cards)))
            if i < len(cards) and not self.dragging("queue", i):
                ui.seal(surf, (r.x + 20, r.centery), str(i + 1))
                ui.deco_label(surf, r.x + 87, r.centery + 1, card_en(cards[i]), 16, INK, width=92)
        label(surf, W - 120, 452, "▼ 새 카드 (rear)", 13, INK_LIGHT, width=156, max_lines=1)
        if b.phase == "run":
            label(surf, *self.run_button.rect.center, "실행 중...", 19, CREAM, width=136, max_lines=1)
        else:
            self.run_button.draw(surf)

    def draw_hand(self, surf):
        """아래: 이번 턴에 뽑은 카드 (가죽 매트 위)."""
        b = self.battle
        ui.mat(surf, self.hand_panel)
        label(surf, self.hand_panel.centerx, 538, "손에 든 카드  ·  끌어서 행동 큐에 놓기  ·  큐 카드를 여기로 끌면 되돌리기", 14, CREAM,
              width=self.hand_panel.w - 40, max_lines=1)
        for i, r in enumerate(self.hand_rects):
            if i < len(b.hand) and not self.dragging("hand", i):
                assets.draw_card(surf, r, b.hand[i])

    def dragging(self, src, i):
        """그 카드를 지금 끌고 있으면 True (원래 자리에는 안 그림)."""
        return self.drag is not None and self.drag["src"] == src and self.drag["index"] == i


# ======================================================================
class PauseScene(Scene):
    """일시정지: 하던 판을 어둡게 깔고 그 위에 양피지 한 장."""

    def __init__(self, game=None):
        self.game = game
        self.resume = Button((W // 2 - 110, 342, 220, 58), "계속하기", 22)
        self.quit = Button((W // 2 - 110, 414, 220, 58), "타이틀로", 22)

    def handle(self, event):
        if self.resume.clicked(event) or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            return "resume"
        if self.quit.clicked(event):
            return "title"

    def draw(self, surf):
        if self.game and self.game.play:
            self.game.play.draw(surf)
            dim = pygame.Surface((W, H), pygame.SRCALPHA)
            dim.fill((10, 5, 0, 200))
            surf.blit(dim, (0, 0))
        ui.scroll(surf, (W // 2 - 260, 190, 520, 310))
        label(surf, W // 2, 238, "일시정지", 36, INK, serif=True, width=460, max_lines=1)
        label(surf, W // 2, 290, "카드 끌어 놓기 · Enter 실행 · R 다시 시작 · ESC 계속", 15, INK_LIGHT, width=460, max_lines=2)
        self.resume.draw(surf)
        self.quit.draw(surf)


# ======================================================================
class TodoScene(Scene):
    """팀원이 아직 채우지 않은 함수가 불렸을 때 보여 주는 안내 화면."""

    def __init__(self, err):
        self.err = err   # todo.NotDone (어디, 담당)
        self.back = Button((W // 2 - 110, 470, 220, 58), "타이틀로", 22)

    def handle(self, event):
        if self.back.clicked(event):
            return "title"

    def draw(self, surf):
        ui.panel(surf, (W // 2 - 360, 140, 720, 300))
        label(surf, W // 2, 200, "아직 구현되지 않은 부분이 있어요", 32, INK, serif=True, width=660, max_lines=1)
        label(surf, W // 2, 270, f"{self.err.where}", 24, WAX, width=660, max_lines=2)
        label(surf, W // 2, 318, f"담당: {self.err.who}", 20, width=660, max_lines=1)
        label(surf, W // 2, 384, "구현한 뒤 터미널에서  python check.py  로 확인하세요", 17, INK_LIGHT, width=660, max_lines=2)
        self.back.draw(surf)


# ======================================================================
class ResultScene(Scene):
    """결과: 두루마리에 성공/실패, 방별 턴 수와 별, 전체 합계."""

    def __init__(self, game):
        self.game = game
        self.retry = Button((W // 2 - 120, 580, 240, 64), "다시 하기", 24)

    def handle(self, event):
        if self.retry.clicked(event):
            return "select"

    def draw(self, surf):
        g = self.game
        ui.scroll(surf, (W // 2 - 300, 70, 600, 470))
        if g.cleared:
            label(surf, W // 2, 140, "탈출 성공!", 50, INK, serif=True, width=540, max_lines=1)
            label(surf, W // 2, 190, "견습생은 무사히 미궁을 빠져나왔다", 17, INK_LIGHT, width=540, max_lines=1)
        else:
            label(surf, W // 2, 140, "실패...", 50, WAX, serif=True, width=540, max_lines=1)
            label(surf, W // 2, 190, "미궁의 그림자에 붙잡혔다", 17, INK_LIGHT, width=540, max_lines=1)
        pygame.draw.line(surf, INK_LIGHT, (W // 2 - 200, 220), (W // 2 + 200, 220), 2)

        total_stars = 0
        y = 262
        for i, turns in enumerate(g.records):
            stage_no = g.first_stage + i
            n = stars(stage_no, turns)
            total_stars += n
            label(surf, W // 2 - 130, y, STAGE_NAMES[stage_no - 1], 22, width=170, max_lines=1)
            label(surf, W // 2 + 20, y, f"{turns}턴", 22, width=100, max_lines=1)
            label(surf, W // 2 + 150, y, ui.stars_text(n), 24, STAR, width=110, max_lines=1)
            y += 50
        if not g.cleared:
            label(surf, W // 2, y, f"{STAGE_NAMES[g.stage - 1]} : {g.failed_turns}턴째에 쓰러짐", 22, WAX, width=520, max_lines=2)
        elif g.records:
            pygame.draw.line(surf, INK_LIGHT, (W // 2 - 200, y - 12), (W // 2 + 200, y - 12), 1)
            label(surf, W // 2, y + 24, f"전체 {sum(g.records)}턴   ·   별 {total_stars} / {len(g.records) * 3}", 24,
                  width=520, max_lines=1)
        self.retry.draw(surf)
