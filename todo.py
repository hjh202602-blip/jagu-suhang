"""
"팀원이 채워야 하는 부분" 표시 도구 (수정할 필요 없음)

빈 함수 안에서 todo("어디", "담당") 를 부르면 NotDone 에러가 남.
  - 게임(main.py)은 이 에러를 잡아서 "누가 무엇을 채워야 하는지" 화면에 보여 줌
  - check.py 는 이 에러를 보고 "아직 안 함" 으로 표시함
구현을 다 했으면 그 함수 안의 todo(...) 줄은 지우면 됨.
"""


class NotDone(NotImplementedError):
    """아직 구현하지 않은 함수가 불렸을 때 나는 에러."""

    def __init__(self, where, who):
        super().__init__(f"{where} 미구현 (담당: {who})")
        self.where = where   # 예: "Queue.enqueue"
        self.who = who       # 예: "기획 홍정현"


def todo(where, who):
    """빈 함수 자리 표시. 호출되면 NotDone 에러를 냄."""
    raise NotDone(where, who)
