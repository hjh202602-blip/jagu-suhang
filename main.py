"""
격자 사냥 - 실행 파일 (담당: 개발 김보민)
실행: python main.py

여기서는 게임 루프와 화면 전환만 처리함
  - 규칙: battle.py / 격자·적: board.py / 카드: cards.py / 탄창: magazine.py
  - 화면: scenes.py / 그리기 도구: ui.py / 맵: stages.py / 숫자: settings.py
  - 팀원이 채울 핵심: structures.py(큐·스택), algorithms.py(BFS·정렬·뒤집기), assets.py(그림)

아직 안 채운 함수(todo)가 불리면 게임이 꺼지지 않고 "미구현" 화면으로 바뀜.
"""
import pygame

from settings import W, H, FPS, WHITE
from stages import STAGES
from todo import NotDone
from scenes import TitleScene, SelectScene, PlayScene, PauseScene, ResultScene, TodoScene


class Game:
    """현재 화면과 진행 기록(몇 스테이지인지, 스테이지별 턴 수)을 들고 있음."""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption("격자 사냥")
        self.clock = pygame.time.Clock()

        self.stage = 1          # 지금 플레이 중인 스테이지 번호
        self.first_stage = 1    # 이번 도전을 시작한 스테이지 (결과 화면 표시용)
        self.records = []       # 클리어한 스테이지마다 걸린 턴 수
        self.cleared = False    # 마지막 스테이지까지 통과했는지
        self.failed_turns = 0   # 실패했을 때 그 스테이지에서 버틴 턴 수

        self.play = None        # 진행 중인 PlayScene (일시정지 후 돌아오기 위해 따로 보관)
        self.scene = TitleScene()

    # ---------- 진행 기록 (PlayScene / SelectScene 이 호출) ----------
    def start_from(self, stage_no):
        """스테이지 선택 화면에서 고른 스테이지부터 새로 도전."""
        self.stage = self.first_stage = stage_no
        self.records = []
        self.cleared = False

    def stage_cleared(self, turns):
        """스테이지 클리어: 다음 스테이지로, 마지막이면 결과 화면으로."""
        self.records.append(turns)
        if self.stage < len(STAGES):
            self.stage += 1
            return "play"
        self.cleared = True
        return "result"

    def stage_failed(self, turns):
        """체력 0: 결과 화면에 몇 스테이지 몇 턴째에 쓰러졌는지 표시."""
        self.cleared = False
        self.failed_turns = turns
        return "result"

    # ---------- 화면 전환 ----------
    def change(self, name):
        """화면 이름을 받아 실제 화면 객체로 바꿈."""
        if name == "title":
            self.scene = TitleScene()
        elif name == "select":
            self.scene = SelectScene(self)
        elif name == "play":            # 새 스테이지 시작
            self.play = PlayScene(self)
            self.scene = self.play
        elif name == "pause":
            self.scene = PauseScene()
        elif name == "resume":          # 일시정지에서 하던 판으로 복귀
            self.scene = self.play
        elif name == "result":
            self.scene = ResultScene(self)

    # ---------- 게임 루프 ----------
    def run(self):
        while True:
            dt = self.clock.tick(FPS)   # 지난 프레임 이후 흐른 시간(ms)
            try:
                # 1) 입력
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        return
                    nxt = self.scene.handle(event)
                    if nxt:
                        self.change(nxt)

                # 2) 시간 흐름 (실행 중 행동 진행, 스테이지 종료 확인)
                nxt = self.scene.update(dt)
                if nxt:
                    self.change(nxt)

                # 3) 그리기
                self.screen.fill(WHITE)
                self.scene.draw(self.screen)
            except NotDone as err:
                # 팀원이 아직 안 채운 함수가 불림 → 누가 무엇을 채워야 하는지 보여 줌
                self.scene = TodoScene(err)
                self.screen.fill(WHITE)
                self.scene.draw(self.screen)
            pygame.display.flip()


if __name__ == "__main__":
    Game().run()
    pygame.quit()
