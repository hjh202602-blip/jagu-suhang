"""
화면(Scene) 모음 (담당: 표현 주서연 / 화면 전환 연결: 개발 김보민)

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
from settings import (W, H, N, CELL, GRID_X, GRID_Y, BLACK, WHITE,
                      MAX_HP, QUEUE_SIZE, MAGAZINE_SIZE, STEP_DELAY, OP_SHOW_TIME)
from ui import box, label, font, Button
from battle import Battle
from stages import STAGE_NAMES, stars


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
    def __init__(self):
        self.start = Button((W // 2 - 100, 420, 200, 60), "게임 시작", 24)

    def handle(self, event):
        if self.start.clicked(event):
            return "howto"

    def draw(self, surf):
        label(surf, W // 2, 220, "격자 사냥", 64)
        label(surf, W // 2, 300, "마법 학교 견습생, 탄창 하나로 미궁을 탈출하라", 20)
        self.start.draw(surf)


# ======================================================================
class HowToScene(Scene):
    """조작 설명 (기획서 4-4: 타이틀 → 조작 설명 → 1번 방)."""

    LINES = [
        "1. 손에 뽑은 카드 6장 중 최대 5장을 눌러 오른쪽 행동 큐에 넣는다  (enqueue)",
        "2. 실행 버튼(Enter)을 누르면 큐 맨 앞부터 하나씩 실행된다  (dequeue, 먼저 넣은 것이 먼저)",
        "3. 실행이 끝나면 추적자가 머리 위 숫자만큼 최단 경로(BFS)로 다가온다",
        "4. 탄을 밟으면 탄창 맨 위에 쌓이고, 발사하면 맨 위 탄이 나간다  (push / pop, 5칸)",
        "5. 재장전 카드: 탄을 다 꺼내 약한 순으로 정렬해 다시 넣는다 → 가장 센 탄이 맨 위",
        "6. 적에게 부딪히면 체력 -1, 다음 행동이 버려지고 맨 뒤에 '기절'이 들어온다",
        "7. 뒤집기 타일을 밟으면 남은 행동 순서가 거꾸로 바뀐다",
        "8. 적을 모두 쓰러뜨리고 출구에 서면 클리어. 적은 턴으로 깰수록 별이 많다",
    ]
    TAN = "탄:  화염탄 피해 2  /  빙결탄 피해 1 + 적이 멈춤  /  폭발탄 피해 1 + 앞의 벽을 부숨"
    KEYS = "Enter 실행   R 방 다시 시작   ESC 일시정지"

    def __init__(self):
        self.next = Button((W // 2 - 100, 590, 200, 60), "시작하기", 24)

    def handle(self, event):
        if self.next.clicked(event) or (event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN):
            return "select"

    def draw(self, surf):
        label(surf, W // 2, 80, "조작 설명", 40)
        for i, line in enumerate(self.LINES):
            img = font(18).render(line, True, BLACK)
            surf.blit(img, (170, 140 + i * 40))
        label(surf, W // 2, 490, self.TAN, 17)
        label(surf, W // 2, 530, self.KEYS, 17)
        self.next.draw(surf)


# ======================================================================
class SelectScene(Scene):
    """스테이지 선택. 고른 스테이지부터 시작."""

    def __init__(self, game):
        self.game = game
        self.buttons = [Button((W // 2 - 330 + i * 230, 300, 200, 150), name, 24)
                        for i, name in enumerate(STAGE_NAMES)]

    def handle(self, event):
        for i, b in enumerate(self.buttons):
            if b.clicked(event):
                self.game.start_from(i + 1)
                return "play"

    def draw(self, surf):
        label(surf, W // 2, 180, "스테이지 선택", 40)
        for b in self.buttons:
            b.draw(surf)


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

        # 클릭 영역
        self.run_button = Button((W - 190, 545, 140, 55), "실행", 20)
        self.hand_rects = [pygame.Rect(280 + i * 112, 560, 100, 115) for i in range(6)]
        self.queue_rects = [pygame.Rect(W - 190, 105 + i * 68, 140, 55) for i in range(QUEUE_SIZE)]

    # ---------- 입력 ----------
    def handle(self, event):
        b = self.battle
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "pause"
            if event.key == pygame.K_r:                 # 이 스테이지 처음부터
                self.battle = Battle(self.game.stage)
                self.floats = []
                return None
            if event.key == pygame.K_RETURN:
                b.start_run()
        if self.run_button.clicked(event):
            b.start_run()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # 손패 클릭 → 큐 맨 뒤로
            for i, r in enumerate(self.hand_rects):
                if i < len(b.hand) and r.collidepoint(event.pos):
                    b.queue_card(i)
                    return None
            # 큐 클릭 → 손패로 되돌리기 (계획 중에만)
            for i, r in enumerate(self.queue_rects):
                if i < len(b.queue) and r.collidepoint(event.pos):
                    b.unqueue_card(i)
                    return None
        return None

    # ---------- 시간 ----------
    def update(self, dt):
        b = self.battle
        # 실행 중이면 STEP_DELAY 마다 행동 하나씩 처리
        if b.phase == "run":
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

        # 스테이지가 끝났으면 다음 화면으로
        if b.state == "clear":
            return self.game.stage_cleared(b.turn)
        if b.state == "fail":
            return self.game.stage_failed(b.turn)
        return None

    # ---------- 그리기 ----------
    def cell_rect(self, pos):
        c, r = pos
        return pygame.Rect(GRID_X + c * CELL, GRID_Y + r * CELL, CELL, CELL)

    def draw(self, surf):
        box(surf, (10, 10, W - 20, H - 20))
        self.draw_left(surf)
        self.draw_grid(surf)
        self.draw_hud(surf)
        self.draw_queue(surf)
        self.draw_hand(surf)
        self.draw_ops(surf)

    # 연산 글자를 띄울 위치 (영역별 기준점)
    OP_POS = {
        "deck": (130, 226),          # 카드 더미 아래
        "magazine": (130, 414),      # 마법 탄창 위
        "queue": (W - 120, 505),     # 행동 큐 아래
        "grid": (GRID_X + N * CELL // 2, 19),  # 격자 위
    }

    def draw_ops(self, surf):
        """pop(), enqueue() 같은 연산 이름을 잠깐 띄웠다가 흐려지며 사라지게 (기획서 독창 요소 ③)."""
        shown = {}  # 영역별로 이미 그린 줄 수
        for where, text, age in reversed(self.floats):    # 최신 것부터
            k = shown.get(where, 0)
            if k >= 2:                                    # 영역마다 최근 2줄만
                continue
            shown[where] = k + 1
            x, y = self.OP_POS[where]
            img = font(13).render(text, True, BLACK)
            img.set_alpha(int(255 * (1 - age / OP_SHOW_TIME)))
            rect = img.get_rect(center=(x, y - k * 16 - age // 160))  # 위로 살짝 떠오름
            pygame.draw.rect(surf, WHITE, rect.inflate(4, 0))
            surf.blit(img, rect)

    def draw_left(self, surf):
        """왼쪽: 카드 더미, 버린 카드, 마법 탄창."""
        deck = self.battle.deck
        box(surf, (30, 30, 200, 660))
        label(surf, 130, 60, "더미 카드", 17)
        box(surf, (70, 80, 120, 130), 2)
        label(surf, 130, 145, str(len(deck.draw_pile)), 30)
        label(surf, 130, 240, "버린 카드", 17)
        box(surf, (70, 260, 120, 130), 2)
        label(surf, 130, 325, str(len(deck.discard)), 30)

        # 마법 탄창: 아래 칸이 바닥(bottom), 채워진 가장 위 칸이 top
        bullets = self.battle.magazine.to_list()
        label(surf, 130, 440, "마법 탄창", 17)
        for i in range(MAGAZINE_SIZE):
            slot_y = 460 + (MAGAZINE_SIZE - 1 - i) * 42   # i=0 이 맨 아래 칸
            box(surf, (80, slot_y, 100, 38), 2)
            if i < len(bullets):
                label(surf, 130, slot_y + 19, bullets[i], 15)
            if i == len(bullets) - 1:
                label(surf, 205, slot_y + 19, "◀ top", 13)
        # TODO(표현 주서연): 재장전 시 magazine.last_sort_steps 를 한 단계씩 보여주기

    def draw_grid(self, surf):
        """가운데: 10x10 격자. 칸·탄·적·플레이어 그림은 assets.py 가 그림."""
        board = self.battle.board
        for r in range(N):
            for c in range(N):
                rect = self.cell_rect((c, r))
                assets.draw_tile(surf, rect, board.tile((c, r)))
                pygame.draw.rect(surf, BLACK, rect, 1)      # 칸 테두리
        box(surf, (GRID_X, GRID_Y, N * CELL, N * CELL))

        # 바닥의 탄
        for pos, bullet in board.items.items():
            assets.draw_item(surf, self.cell_rect(pos), bullet)

        # 적 + 머리 위 정보(이번 턴 이동 칸 수, 얼어 있으면 '얼음')
        for e in board.enemies:
            rect = self.cell_rect(e.pos)
            assets.draw_enemy(surf, rect, e.kind)
            if e.frozen > 0:
                label(surf, rect.centerx, rect.centery - 14, "얼음", 11)
            elif e.kind == "chaser":
                label(surf, rect.centerx, rect.centery - 14, str(e.steps), 13)

        # 플레이어
        p = board.player
        assets.draw_player(surf, self.cell_rect(p.pos), p.facing)
        # TODO(표현 주서연): 칸 사이를 미끄러지듯 이동하는 애니메이션

    def draw_hud(self, surf):
        """격자 바로 아래: 스테이지, 체력, 턴, 최근 사건."""
        b = self.battle
        hp = "♥" * b.board.player.hp + "♡" * (MAX_HP - b.board.player.hp)
        cx = GRID_X + N * CELL // 2
        label(surf, cx, 500, f"{STAGE_NAMES[b.stage_no - 1]}   체력 {hp}   턴 {b.turn}   {b.message}", 15)

    def draw_queue(self, surf):
        """오른쪽: 행동 큐 (위가 먼저 실행되는 front) + 실행 버튼."""
        b = self.battle
        box(surf, (W - 210, 30, 180, 490))
        label(surf, W - 120, 55, "행동 큐", 19)
        label(surf, W - 120, 85, "▲ 먼저 실행 (front)", 13)
        cards = b.queue.to_list()
        for i, r in enumerate(self.queue_rects):
            box(surf, r, 2)
            if i < len(cards):
                label(surf, *r.center, f"{i + 1}. {cards[i]}", 16)
        label(surf, W - 120, 465, "▼ 새 카드 (rear)", 13)
        if b.phase == "run":
            label(surf, *self.run_button.rect.center, "실행 중...", 18)
        else:
            self.run_button.draw(surf)

    def draw_hand(self, surf):
        """아래: 이번 턴에 뽑은 카드."""
        b = self.battle
        box(surf, (260, 520, W - 490, 170))
        label(surf, (260 + W - 230) // 2, 538, "손에 뽑은 카드  (클릭: 큐에 넣기 / 큐 카드 클릭: 되돌리기)", 15)
        for i, r in enumerate(self.hand_rects):
            if i < len(b.hand):
                assets.draw_card(surf, r, b.hand[i])


# ======================================================================
class PauseScene(Scene):
    def __init__(self):
        self.resume = Button((W // 2 - 100, 330, 200, 55), "계속하기")
        self.quit = Button((W // 2 - 100, 400, 200, 55), "타이틀로")

    def handle(self, event):
        if self.resume.clicked(event) or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            return "resume"
        if self.quit.clicked(event):
            return "title"

    def draw(self, surf):
        label(surf, W // 2, 250, "일시정지", 40)
        label(surf, W // 2, 290, "조작: 카드 클릭 / Enter 실행 / R 다시 시작 / ESC 일시정지", 15)
        self.resume.draw(surf)
        self.quit.draw(surf)


# ======================================================================
class TodoScene(Scene):
    """팀원이 아직 채우지 않은 함수가 불렸을 때 보여 주는 안내 화면."""

    def __init__(self, err):
        self.err = err   # todo.NotDone (어디, 담당)
        self.back = Button((W // 2 - 100, 470, 200, 55), "타이틀로")

    def handle(self, event):
        if self.back.clicked(event):
            return "title"

    def draw(self, surf):
        label(surf, W // 2, 200, "아직 구현되지 않은 부분이 있어요", 36)
        label(surf, W // 2, 280, f"{self.err.where}", 26)
        label(surf, W // 2, 325, f"담당: {self.err.who}", 22)
        label(surf, W // 2, 390, "구현한 뒤 터미널에서  python check.py  로 확인하세요", 18)
        self.back.draw(surf)


# ======================================================================
class ResultScene(Scene):
    """결과: 성공/실패와 스테이지별 턴 수."""

    def __init__(self, game):
        self.game = game
        self.retry = Button((W // 2 - 100, 480, 200, 60), "다시 하기", 24)

    def handle(self, event):
        if self.retry.clicked(event):
            return "select"

    def draw(self, surf):
        g = self.game
        label(surf, W // 2, 160, "탈출 성공!" if g.cleared else "실패...", 48)
        total_stars = 0
        for i, turns in enumerate(g.records):
            stage_no = g.first_stage + i
            n = stars(stage_no, turns)
            total_stars += n
            label(surf, W // 2, 250 + i * 40,
                  f"{STAGE_NAMES[stage_no - 1]} : {turns}턴   {'★' * n}{'☆' * (3 - n)}", 22)
        y = 250 + len(g.records) * 40
        if not g.cleared:
            label(surf, W // 2, y, f"{STAGE_NAMES[g.stage - 1]} : {g.failed_turns}턴째에 쓰러짐", 22)
        elif g.records:
            label(surf, W // 2, y + 20,
                  f"전체 {sum(g.records)}턴   별 {total_stars} / {len(g.records) * 3}", 24)
        self.retry.draw(surf)
