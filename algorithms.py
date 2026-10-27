"""
핵심 알고리즘 모음

★ 팀원이 채울 부분 ★  (각 함수 안의 todo(...) 를 지우고 직접 구현)
  - bfs_path       : 개발 김보민   (적 추격)
  - selection_sort : 표현 주서연   (재장전)
  - reverse_queue  : 기획 홍정현   (뒤집기 타일)

규칙 (기획서)
  - 라이브러리의 길찾기, sort(), sorted() 를 쓰지 않고 직접 구현
  - 큐/스택은 structures.py 의 Queue, Stack 을 사용
  - 다 채웠으면  python check.py  로 확인

아직 안 채워도 게임은 실행됨 (적이 안 움직이거나, 재장전/뒤집기가 효과 없이 넘어감).
"""
from structures import Queue, Stack  # 구현할 때 사용 (BFS → Queue, 큐 뒤집기 → Stack)
from todo import todo


def bfs_path(start, goal, can_pass):
    """
    [개발 김보민] BFS 로 start → goal 최단 경로 찾기 (상하좌우 4방향).

    매개변수
        start, goal : (c, r) 좌표 튜플
        can_pass    : 함수. can_pass((c, r)) 가 True 면 그 칸을 지나갈 수 있음
                      (격자 밖, 벽, 다른 적은 board.py 에서 False 가 되도록 만들어 둠)
    반환
        start 를 뺀 경로 리스트 [첫 칸, 둘째 칸, ..., goal]
        길이 없거나 start == goal 이면 빈 리스트 []

    예)  start=(0,0), goal=(2,0), 사이에 벽 없음  →  [(1,0), (2,0)]

    힌트
        1) Queue 에 start 를 넣고, prev = {start: None} 으로 "어디서 왔는지" 기록
        2) 큐에서 하나 꺼내 이웃 4칸 중 can_pass 이고 prev 에 없는 칸을 넣기
        3) goal 에 도착하면 prev 를 거꾸로 따라가 경로를 만들고 뒤집기
    """
    # TODO(개발 김보민): BFS 구현
    todo("algorithms.bfs_path", "개발 김보민")


def selection_sort(items, key):
    """
    [표현 주서연] 선택 정렬. items 를 key 값이 작은 순서로 "제자리" 정렬.

    매개변수
        items : 정렬할 리스트 (이 리스트 자체를 바꿈)
        key   : 함수. key(x) 가 작을수록 앞으로
    반환
        자리를 바꿀 때마다 그 순간의 items 복사본을 모은 리스트
        (화면에서 정렬 과정을 한 단계씩 보여주는 애니메이션에 씀)

    예)  items = ["폭발탄", "빙결탄"], key = 세기
         → items 는 ["빙결탄", "폭발탄"] 이 되고, 반환값은 [["빙결탄", "폭발탄"]]

    힌트: i 번째 자리에 i 번째 이후에서 가장 작은 값을 찾아와 바꾸기를 반복
    """
    # TODO(표현 주서연): 선택 정렬 구현 (sort(), sorted() 금지)
    todo("algorithms.selection_sort", "표현 주서연")


def reverse_queue(queue):
    """
    [기획 홍정현] 뒤집기 타일: queue 에 남은 순서를 거꾸로 바꿈 (제자리).

    매개변수
        queue : structures.Queue
    반환
        없음 (queue 자체를 바꿈)

    예)  queue 가 [발사, 왼쪽 보기, 앞으로 이동] → [앞으로 이동, 왼쪽 보기, 발사]

    힌트: 큐에서 전부 dequeue 해서 Stack 에 push → Stack 에서 전부 pop 해서 다시 enqueue
          (FIFO 가 LIFO 로 바뀌는 순간을 게임에서 보여주는 기믹)
    """
    # TODO(기획 홍정현): Stack 을 이용해 큐 뒤집기
    todo("algorithms.reverse_queue", "기획 홍정현")
