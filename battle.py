"""
한 스테이지의 전투 진행 (규칙: 기획 홍정현 / 이동·충돌·적 AI: 개발 김보민)

턴 흐름
  1) 계획(plan): 손패 6장 중 최대 5장을 골라 행동 큐에 넣음
  2) 실행(run): 큐 맨 앞부터 하나씩 꺼내 실행 (step() 한 번 = 행동 하나)
  3) 적 차례: 추적자가 머리 위 숫자만큼 BFS 최단 경로로 다가옴
  4) 남은 손패는 버리고 다음 턴

화면 코드(scenes.py)는 이 클래스의 값을 읽어서 그리기만 하고,
규칙은 전부 여기서 처리함.
핵심 자료구조·알고리즘(structures.py, algorithms.py)이 아직 비어 있어도
BFS/재장전/뒤집기는 "미구현" 안내만 하고 넘어가도록 해 둠 (NotDone 처리).
"""
import random

import algorithms
from settings import DIRS, HAND_SIZE, QUEUE_SIZE, N
from structures import Queue
from todo import NotDone
from board import Board, EXIT, FLIP, FLOOR
from cards import Deck
from magazine import Magazine
from stages import STAGES

# 탄 종류별 피해량 - TODO(기획 홍정현): 밸런스 조정
DAMAGE = {"화염탄": 2, "빙결탄": 1, "폭발탄": 1}
FREEZE_TURNS = 2  # 빙결탄에 맞은 적이 멈추는 턴 수 (맞은 턴 포함)
STUN = "기절"      # 피격 시 큐 맨 뒤에 들어가는 행동 (아무것도 안 함, 카드 더미에 안 들어감)


class Battle:
    """한 스테이지의 상태: 보드, 카드 더미, 손패, 행동 큐, 탄창, 턴 수."""

    def __init__(self, stage_no):
        self.stage_no = stage_no
        self.board = Board(STAGES[stage_no - 1])
        self.deck = Deck()
        self.hand = []                      # 이번 턴에 뽑은 카드 (그냥 리스트)
        self.queue = Queue(QUEUE_SIZE)      # 행동 큐
        self.magazine = Magazine()          # 마법 탄창 (스택)
        self.turn = 0
        self.phase = "plan"                 # plan(계획 중) / run(실행 중)
        self.state = "playing"              # playing / clear / fail
        self.message = ""                   # 화면에 보여줄 최근 사건 한 줄
        self.ops = []                       # 아직 화면에 안 넘긴 자료구조 연산 기록 (where, 글자)
        self.sounds = []                    # 아직 화면에 안 넘긴 효과음 이름
        self.start_turn()

    # ================= 자료구조 연산 기록 =================
    def op(self, where, text):
        """
        자료구조 연산이 일어났다고 기록 (기획서 독창 요소 ③).
        where: 'queue'(행동 큐) / 'magazine'(탄창) / 'deck'(카드 더미) / 'grid'(BFS)
        화면(scenes.py)이 take_ops() 로 가져가서 잠깐 띄웠다가 지움.
        """
        self.ops.append((where, text))

    def take_ops(self):
        """쌓인 연산 기록을 넘겨주고 비움."""
        ops, self.ops = self.ops, []
        return ops

    def sound(self, name):
        """효과음을 내야 한다고 기록. 재생은 화면(scenes.py)이 assets.play() 로."""
        self.sounds.append(name)

    def take_sounds(self):
        sounds, self.sounds = self.sounds, []
        return sounds

    # ================= 턴 관리 =================
    def start_turn(self):
        """새 턴: 카드 뽑기, 적 이동 칸 수 정하기."""
        self.turn += 1
        self.hand = self.deck.draw(HAND_SIZE)
        self.op("deck", f"pop() x{len(self.hand)}")
        for e in self.board.enemies:
            e.roll_steps()
        self.refill_ammo()
        self.phase = "plan"

    def refill_ammo(self):
        """
        탄이 하나도 없는데(탄창·바닥 모두) 적이 남아 있으면 더 이상 깰 수 없음.
        → 플레이어가 갈 수 있는 가까운 빈 칸에 화염탄을 하나 만들어 줌.
        """
        board = self.board
        if not board.enemies or not self.magazine.is_empty() or board.items:
            return
        blocked = {e.pos for e in board.enemies}
        near, far = [], []
        for r in range(N):
            for c in range(N):
                pos = (c, r)
                if board.tile(pos) != FLOOR or pos in blocked or pos == board.player.pos:
                    continue
                path = board.bfs_path(board.player.pos, pos, blocked)
                if path:
                    (near if len(path) <= 4 else far).append(pos)
        cands = near or far
        if cands:
            pos = random.choice(cands)
            board.items[pos] = "화염탄"
            self.message = "탄이 다 떨어져서 화염탄이 새로 나타났다"

    def end_turn(self):
        """턴 끝: 남은 손패를 버리고 다음 턴 시작."""
        self.deck.discard_cards(self.hand)
        self.hand = []
        self.start_turn()

    # ================= 계획 단계 =================
    def queue_card(self, hand_index):
        """손패의 카드를 행동 큐 맨 뒤에 넣기 (enqueue)."""
        if self.phase != "plan" or self.queue.is_full():
            return
        card = self.hand[hand_index]
        if self.queue.enqueue(card):
            self.hand.pop(hand_index)
            self.op("queue", f"enqueue({card})")

    def unqueue_card(self, queue_index):
        """계획 중에는 큐에 넣은 카드를 손패로 되돌릴 수 있음."""
        if self.phase != "plan":
            return
        card = self.queue.remove_at(queue_index)
        if card is not None:
            self.hand.append(card)

    def start_run(self):
        """실행 버튼: 이 순간부터는 큐를 바꿀 수 없음."""
        if self.phase == "plan" and self.state == "playing":
            self.phase = "run"

    # ================= 실행 단계 =================
    def step(self):
        """실행 중 한 번 호출될 때마다 행동 하나, 큐가 비면 적 차례를 처리."""
        if self.phase != "run" or self.state != "playing":
            return
        if not self.queue.is_empty():
            card = self.queue.dequeue()
            self.op("queue", f"dequeue() → {card}")
            self.do_action(card)
            if card != STUN:                # 기절은 진짜 카드가 아니라 버리지 않음
                self.deck.discard_cards([card])
            self.check_state()
        else:
            self.enemy_turn()
            self.check_state()
            if self.state == "playing":
                self.end_turn()

    def do_action(self, card):
        """카드 하나의 효과 처리."""
        p = self.board.player
        if card == "앞으로 이동":
            self.move_player(DIRS[p.facing])
        elif card == "뒤로 이동":
            dx, dy = DIRS[p.facing]
            self.move_player((-dx, -dy))   # 방향은 그대로, 뒤로 한 칸
        elif card == "왼쪽 보기":
            p.facing = (p.facing + 3) % 4
            self.message = "왼쪽으로 돌았다"
        elif card == "오른쪽 보기":
            p.facing = (p.facing + 1) % 4
            self.message = "오른쪽으로 돌았다"
        elif card == "발사":
            self.fire()
        elif card == "재장전":
            if self.magazine.is_empty():
                self.message = "탄창이 비어 있어서 재장전할 게 없다"
            elif self.magazine.reload():
                self.message = "재장전: 센 탄이 맨 위로"
                self.sound("reload")
                self.op("magazine", f"pop() x{len(self.magazine)} → 선택 정렬 → push()")
            else:
                self.message = "[미구현] 선택 정렬 (표현 주서연) - 탄창 그대로"
        elif card == STUN:
            self.message = "기절해서 한 박자 쉬었다"

    def move_player(self, d):
        """플레이어를 d 방향으로 한 칸. 벽이면 멈추고, 적이면 부딪혀서 체력 -1."""
        board = self.board
        p = board.player
        nxt = (p.pos[0] + d[0], p.pos[1] + d[1])

        if not board.in_bounds(nxt) or board.is_wall(nxt):
            self.message = "벽에 막혔다"
            return
        if board.enemy_at(nxt):
            p.hp -= 1
            self.message = "적과 부딪혔다! 체력 -1, 기절"
            self.sound("hurt")
            # 피격: 다음 행동(큐 맨 앞)을 버리고 맨 뒤에 '기절' 넣기
            lost = self.queue.dequeue()
            if lost is not None:
                self.op("queue", f"dequeue() → {lost} 버림")
                if lost != STUN:
                    self.deck.discard_cards([lost])
            self.queue.enqueue(STUN)
            self.op("queue", f"enqueue({STUN})")
            return

        p.pos = nxt
        self.message = ""

        # 탄 줍기: 탄창 맨 위에 push, 꽉 찼으면 못 주움(오버플로)
        if nxt in board.items:
            bullet = board.items[nxt]
            if self.magazine.push(bullet):
                del board.items[nxt]
                self.message = f"{bullet} 장전"
                self.op("magazine", f"push({bullet})")
                self.sound("pickup")
            else:
                self.message = "탄창이 꽉 차서 못 주웠다"
                self.op("magazine", "push() 실패: 오버플로")

        # 뒤집기 타일: 남은 행동 순서를 거꾸로 (algorithms.reverse_queue)
        if board.tile(nxt) == FLIP:
            try:
                algorithms.reverse_queue(self.queue)
                self.message = "뒤집기 타일! 남은 행동이 거꾸로"
                self.sound("flip")
                self.op("queue", "dequeue()→push() … pop()→enqueue()")
            except NotDone:
                self.message = "[미구현] 큐 뒤집기 (기획 홍정현) - 순서 그대로"

        # 출구: 적이 남아 있으면 안내만
        if board.tile(nxt) == EXIT and board.enemies:
            self.message = "적을 모두 쓰러뜨려야 출구가 열린다"

    def fire(self):
        """탄창 맨 위 탄을 pop 해서 바라보는 방향으로 직선 발사."""
        board = self.board
        p = board.player
        bullet = self.magazine.pop()
        if bullet is None:
            self.message = "탄창이 비어 있다"
            self.op("magazine", "pop() → 비어 있음")
            return
        self.op("magazine", f"pop() → {bullet}")
        self.sound("fire")

        dx, dy = DIRS[p.facing]
        pos = p.pos
        while True:
            pos = (pos[0] + dx, pos[1] + dy)
            if not board.in_bounds(pos):
                self.message = f"{bullet} 빗나감"
                return
            if board.is_wall(pos):
                if bullet == "폭발탄":
                    board.set_tile(pos, FLOOR)
                    self.message = "폭발탄이 벽을 부쉈다"
                else:
                    self.message = f"{bullet}이 벽에 막혔다"
                return
            enemy = board.enemy_at(pos)
            if enemy:
                enemy.hp -= DAMAGE[bullet]
                self.sound("hit")
                if bullet == "빙결탄":
                    enemy.frozen = FREEZE_TURNS
                board.remove_dead()
                self.message = f"{bullet} 명중!" + (" 적 처치" if enemy.hp <= 0 else "")
                return

    # ================= 적 차례 =================
    def enemy_turn(self):
        """추적자가 머리 위 숫자만큼 BFS 최단 경로를 따라 다가옴. 플레이어에 닿으면 공격."""
        board = self.board
        p = board.player
        for e in board.enemies:
            if e.frozen > 0:            # 얼어 있으면 이번 턴은 쉼
                e.frozen -= 1
                continue
            if e.steps == 0:            # 허수아비
                continue
            others = {o.pos for o in board.enemies if o is not e}
            try:
                path = board.bfs_path(e.pos, p.pos, blocked=others)
            except NotDone:
                self.message = "[미구현] BFS (개발 김보민) - 적이 움직이지 않음"
                return
            if path:
                self.op("grid", f"BFS: 최단 {len(path)}칸")
            e.trail = []                # 이번 턴에 지나간 칸 (화면의 이동 애니메이션용)
            for nxt in path[:e.steps]:
                if nxt == p.pos:        # 플레이어 칸에 닿음 → 공격하고 멈춤
                    p.hp -= 1
                    self.message = "적에게 공격당했다! 체력 -1"
                    self.sound("hurt")
                    break
                e.pos = nxt
                e.trail.append(nxt)

    # ================= 승패 =================
    def check_state(self):
        """체력 0 이면 실패, 적을 모두 쓰러뜨리고 출구에 서 있으면 클리어."""
        p = self.board.player
        if p.hp <= 0:
            self.state = "fail"
            self.sound("fail")
        elif not self.board.enemies and self.board.tile(p.pos) == EXIT:
            self.state = "clear"
            self.sound("clear")
