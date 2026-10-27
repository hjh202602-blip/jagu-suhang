"""
팀원용 채점기: 내가 맡은 부분을 맞게 만들었는지 확인
실행: python check.py

결과 표시
  [완료]   테스트 통과
  [미완성] 아직 todo(...) 가 남아 있음
  [오류]   만들긴 했는데 결과가 틀림 → 아래 이유를 보고 고치기
"""
import inspect
import sys

import algorithms
from structures import Queue, Stack
from todo import NotDone

# 윈도우 터미널에서 한글이 깨지지 않도록
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


# ======================================================================
# 테스트들 (각 함수는 틀리면 AssertionError 를 냄)
# ======================================================================

def test_queue():
    q = Queue(3)
    assert q.is_empty() and len(q) == 0, "새 큐는 비어 있어야 함"
    assert q.dequeue() is None and q.peek() is None, "빈 큐에서 dequeue/peek 은 None"
    assert q.enqueue("a") is True and q.enqueue("b") is True and q.enqueue("c") is True
    assert q.is_full(), "capacity 3 에 3개 넣으면 꽉 참"
    assert q.enqueue("d") is False, "꽉 찬 큐에 enqueue 하면 False"
    assert q.to_list() == ["a", "b", "c"], f"to_list 순서 틀림: {q.to_list()}"
    assert q.peek() == "a", "peek 은 맨 앞 값"
    assert q.dequeue() == "a" and q.dequeue() == "b", "먼저 넣은 것이 먼저 나와야 함 (FIFO)"
    assert len(q) == 1
    q.enqueue("x")
    q.enqueue("y")
    assert q.remove_at(1) == "x" and q.to_list() == ["c", "y"], "remove_at 은 앞에서 index 번째"
    q.clear()
    assert q.is_empty()
    big = Queue()                                   # capacity 없음
    for i in range(100):
        big.enqueue(i)
    assert not big.is_full(), "capacity 가 None 이면 꽉 차지 않음"
    assert [big.dequeue() for _ in range(100)] == list(range(100)), "100개 넣고 빼도 순서 유지"


def test_stack():
    s = Stack(3)
    assert s.is_empty() and len(s) == 0, "새 스택은 비어 있어야 함"
    assert s.pop() is None and s.peek() is None, "빈 스택에서 pop/peek 은 None"
    assert s.push("a") is True and s.push("b") is True and s.push("c") is True
    assert s.is_full(), "capacity 3 에 3개 넣으면 꽉 참"
    assert s.push("d") is False, "꽉 찬 스택에 push 하면 False (오버플로)"
    assert s.to_list() == ["a", "b", "c"], f"to_list 는 바닥→맨 위 순서: {s.to_list()}"
    assert s.peek() == "c", "peek 은 맨 위 값"
    assert s.pop() == "c" and s.pop() == "b", "마지막에 넣은 것이 먼저 나와야 함 (LIFO)"
    assert len(s) == 1
    s.clear()
    assert s.is_empty()
    assert not Stack().is_full(), "capacity 가 None 이면 꽉 차지 않음"


def test_reverse_queue():
    q = Queue(5)
    for x in ["발사", "왼쪽 보기", "앞으로 이동"]:
        q.enqueue(x)
    result = algorithms.reverse_queue(q)
    assert result is None, "반환값 없이 queue 자체를 바꿔야 함"
    assert q.to_list() == ["앞으로 이동", "왼쪽 보기", "발사"], f"뒤집은 결과 틀림: {q.to_list()}"
    empty = Queue()
    algorithms.reverse_queue(empty)
    assert empty.is_empty(), "빈 큐를 뒤집어도 빈 큐"


def _check_path(path, start, goal, can_pass, expect_len):
    assert len(path) == expect_len, f"최단 경로 길이는 {expect_len} 이어야 함 (지금 {len(path)})"
    assert path[-1] == goal, "경로 마지막 칸은 goal"
    prev = start
    for cell in path:
        assert abs(cell[0] - prev[0]) + abs(cell[1] - prev[1]) == 1, f"{prev}→{cell} 은 상하좌우 한 칸이 아님"
        assert can_pass(cell), f"{cell} 은 지나갈 수 없는 칸"
        prev = cell


def test_bfs():
    def grid(walls, size=5):
        return lambda p: 0 <= p[0] < size and 0 <= p[1] < size and p not in walls

    open_grid = grid(set())
    path = algorithms.bfs_path((0, 0), (2, 0), open_grid)
    assert path == [(1, 0), (2, 0)], f"벽 없는 직선 경로 틀림: {path}"
    assert algorithms.bfs_path((1, 1), (1, 1), open_grid) == [], "start == goal 이면 []"

    # 가운데 세로 벽을 돌아가야 하는 경우: (0,2) → (4,2), 벽 x=2 (y 0~3)
    walls = {(2, 0), (2, 1), (2, 2), (2, 3)}
    can = grid(walls)
    _check_path(algorithms.bfs_path((0, 2), (4, 2), can), (0, 2), (4, 2), can, 8)

    # 완전히 막힌 경우
    blocked = grid({(2, y) for y in range(5)})
    assert algorithms.bfs_path((0, 0), (4, 4), blocked) == [], "길이 없으면 []"


def test_selection_sort():
    power = {"빙결탄": 1, "화염탄": 2, "폭발탄": 3}
    items = ["폭발탄", "빙결탄", "화염탄"]
    steps = algorithms.selection_sort(items, key=lambda b: power[b])
    assert items == ["빙결탄", "화염탄", "폭발탄"], f"정렬 결과 틀림: {items}"
    assert isinstance(steps, list) and steps, "자리를 바꿀 때마다의 상태를 리스트로 반환해야 함"
    assert steps[-1] == items, "마지막 단계는 정렬이 끝난 상태"
    assert steps[0] is not items, "단계는 복사본이어야 함 (list(items))"

    nums = [5, 3, 8, 1, 9, 2]
    algorithms.selection_sort(nums, key=lambda x: x)
    assert nums == [1, 2, 3, 5, 8, 9], f"숫자 정렬 틀림: {nums}"
    already = [1, 2, 3]
    assert algorithms.selection_sort(already, key=lambda x: x) == [], "이미 정렬돼 있으면 바꾼 단계 없음 → []"

    src = inspect.getsource(algorithms.selection_sort)
    assert "sorted(" not in src and ".sort(" not in src, "sort()/sorted() 는 쓰면 안 됨 (기획서 규칙)"


# (테스트 이름, 담당, 함수)
TESTS = [
    ("Queue (structures.py)", "기획 홍정현", test_queue),
    ("Stack (structures.py)", "표현 주서연", test_stack),
    ("reverse_queue (algorithms.py)", "기획 홍정현", test_reverse_queue),
    ("bfs_path (algorithms.py)", "개발 김보민", test_bfs),
    ("selection_sort (algorithms.py)", "표현 주서연", test_selection_sort),
]


def main():
    print("=== 격자 사냥 : 핵심 기믹 확인 ===\n")
    passed = 0
    for name, who, test in TESTS:
        try:
            test()
            print(f"[완료]   {name}  - {who}")
            passed += 1
        except NotDone as err:
            print(f"[미완성] {name}  - {who}   ({err.where} 가 아직 비어 있음)")
        except AssertionError as err:
            print(f"[오류]   {name}  - {who}\n         이유: {err}")
        except Exception as err:   # 구현 중 생긴 다른 에러 (오타 등)
            print(f"[오류]   {name}  - {who}\n         {type(err).__name__}: {err}")
    print(f"\n{passed} / {len(TESTS)} 완료")
    print("\n그림 에셋(assets.py)은 테스트가 없음 → python main.py 로 화면에서 확인")


if __name__ == "__main__":
    main()
