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
import pygame

import assets
import ui
from settings import (W, H, N, CELL, GRID_X, GRID_Y, INK, INK_LIGHT, CREAM, GOLD, WAX,
                      MAX_HP, QUEUE_SIZE, MAGAZINE_SIZE, STEP_DELAY, OP_SHOW_TIME,
                      MOVE_SPEED, SORT_DELAY)
from ui import label, font, Button
from battle import Battle
from board import EXIT
from stages import STAGE_NAMES, STAGE_DESC, STAGE_LEVEL, STAGES, stars

STAR = (196, 128, 30)   # 양피지 위 별 색 (진한 금)


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
        label(surf, W // 2, 150, "마법 학교 졸업 시험", 18, INK_LIGHT, width=500, max_lines=1)
        label(surf, W // 2, 228, "격자 사냥", 76, INK, serif=True, width=500, max_lines=1)
        pygame.draw.line(surf, INK_LIGHT, (W // 2 - 180, 290), (W // 2 + 180, 290), 2)
        pygame.draw.polygon(surf, INK, [(W // 2, 282), (W // 2 + 8, 290), (W // 2, 298), (W // 2 - 8, 290)])
        label(surf, W // 2, 343, "카드로 행동을 짜고, 탄창 하나로\n지하 미궁을 탈출하라", 20, INK, width=440, max_lines=2)
        self.start.draw(surf)


# ======================================================================
class HowToScene(Scene):
    """조작 설명 (기획서 4-4: 타이틀 → 조작 설명 → 1번 방)."""

    LINES = [
        "손에 든 카드 6장 중 최대 5장을 끌어다 오른쪽 행동 큐에 놓는다  (enqueue)",
        "실행 버튼(Enter)을 누르면 큐 맨 앞부터 하나씩 실행된다  (dequeue, 먼저 넣은 것이 먼저)",
        "실행이 끝나면 추적자가 머리 위 숫자만큼 최단 경로(BFS)로 다가온다 (멀면 빠르게)",
        "탄을 밟으면 탄창 맨 위에 쌓이고, 발사하면 맨 위 탄이 나간다  (push / pop, 5칸)",
        "재장전 카드: 탄을 다 꺼내 약한 순으로 정렬해 다시 넣는다 → 가장 센 탄이 맨 위",
        "적에게 부딪히면 체력 -1, 다음 행동이 버려지고 맨 뒤에 '기절'이 들어온다",
        "뒤집기 타일을 밟으면 남은 행동 순서가 거꾸로 바뀐다",
        "적을 모두 쓰러뜨리면 출구가 열린다. 출구에 서면 클리어, 적은 턴일수록 별이 많다",
    ]
    TAN = (("화염탄", "피해 2"), ("빙결탄", "피해 1 + 적이 멈춤"), ("폭발탄", "피해 1 + 앞의 벽을 부숨"))
    KEYS = "Enter 실행   ·   R 방 다시 시작   ·   ESC 일시정지"

    def __init__(self):
        self.next = Button((W // 2 - 110, 618, 220, 62), "시작하기", 24)

    def handle(self, event):
        if self.next.clicked(event) or (event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN):
            return "select"

    def draw(self, surf):
        ui.scroll(surf, (90, 34, W - 180, 560))
        label(surf, W // 2, 84, "조작 설명", 34, INK, serif=True, width=600, max_lines=1)
        pygame.draw.line(surf, INK_LIGHT, (W // 2 - 140, 110), (W // 2 + 140, 110), 2)
        # 규칙: 두루마리 안쪽 폭에 맞춰 줄바꿈, 줄 수에 따라 아래로 이어서 씀
        y = 132
        for i, line in enumerate(self.LINES):
            lines = ui.wrap(line, 17, 880)
            h = len(lines) * 22
            ui.seal(surf, (150, y + 11), str(i + 1), 13)
            label(surf, 176, y + h // 2, line, 17, INK, width=880, align="left")
            y += h + 18
        for k, (name, text) in enumerate(self.TAN):
            x = 160 + k * 300
            assets.draw_item(surf, pygame.Rect(x, 460, 54, 54), name)
            label(surf, x + 60, 474, name, 17, INK, width=220, max_lines=1, align="left")
            label(surf, x + 60, 498, text, 15, INK_LIGHT, width=220, max_lines=2, align="left")
        label(surf, W // 2, 552, self.KEYS, 16, INK, width=900, max_lines=1)
        self.next.draw(surf)


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
        if b.phase == "run" and not self.sort_frames:
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

        # 효과음
        for name in b.take_sounds():
            assets.play(name)

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
            label(surf, *rect.center, d["card"], 15, width=126, max_lines=2)

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
            rect = self.cell_rect(self.shown_pos(e))
            assets.draw_enemy(surf, rect, e.kind)
            if e.frozen > 0:
                self.badge(surf, rect, "얼음", (190, 225, 250))
            elif e.kind == "chaser":
                self.badge(surf, rect, str(e.steps), CREAM)

        # 플레이어
        p = board.player
        assets.draw_player(surf, self.cell_rect(self.shown_pos(p)), p.facing)

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
                label(surf, r.x + 87, r.centery, cards[i], 15, width=92, max_lines=2)
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
        ui.panel(surf, (W // 2 - 260, 190, 520, 310))
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
