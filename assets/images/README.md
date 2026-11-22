# 그림 넣는 곳 (표현 담당)

이 폴더에 아래 이름으로 PNG 를 넣으면 게임이 자동으로 그 그림을 씀. 없으면 글자로 된 임시 그림이 나옴.
이름 목록은 `assets.py` 의 `IMAGE_FILES` 와 같음.

| 파일 | 그림 | 크기 |
|---|---|---|
| `wall.png` | 벽 | 46x46 |
| `exit.png` | 출구 | 46x46 |
| `flip.png` | 뒤집기 타일 | 46x46 |
| `player.png` | 플레이어 (정면 모습, 방향은 금색 화살촉으로 따로 표시) | 46x46 |
| `chaser.png` | 추적자 | 46x46 |
| `dummy.png` | 허수아비 | 46x46 |
| `bullet_fire.png` / `bullet_ice.png` / `bullet_bomb.png` | 바닥의 화염탄 / 빙결탄 / 폭발탄 | 46x46 |
| `card_forward.png` / `card_back.png` | 앞으로 이동 / 뒤로 이동 카드 | 237x330 |
| `card_dash.png` | 2칸 앞으로 카드 | 237x330 |
| `card_turn_left.png` / `card_turn_right.png` | 왼쪽 보기 / 오른쪽 보기 카드 | 237x330 |
| `card_fire.png` / `card_reload.png` | 발사 / 재장전 카드 | 237x330 |

### 전체 컨셉: 나무 탁자 위 양피지 보드게임 (중세풍)

`python assets/make_theme.py` 로 만드는 그림 (numpy 필요, 게임 실행에는 필요 없음)
| 파일 | 내용 |
|---|---|
| `bg_table.png` | 화면 전체 나무 탁자 (가장자리 어둡게, 가운데 촛불 빛) |
| `parchment.png` | 패널·칸에 깔리는 양피지 무늬 |
| `board.png` | 격자를 담은 양피지 지도 (찢긴 가장자리, 잉크 격자, A~J / 1~10 좌표) |
| `wall.png` | 돌 블록 토큰 |
| `exit.png` / `exit_open.png` | 출구 문 (닫힘 / 적을 다 잡아 열림) |
| `flip.png` | 뒤집기 타일 (놋쇠 판) |
| `bullet_fire.png` / `bullet_ice.png` / `bullet_bomb.png` | 탄 보석 토큰 (불꽃 루비 / 얼음 결정 / 심지 폭탄) |
| `card_cover.png` | 카드 더미에 엎어 둔 카드 뒷면 |

패널·버튼·두루마리·봉랍 같은 화면 장식은 `ui.py` 에서 그림.

### 유닛 그림 (player / chaser / dummy)

`python assets/make_units.py` 로 그린 그림 (카드와 같은 갈색 가죽·금색·양피지 톤). 둥근 받침 위에 선 보드게임 말 모양, 92x92 로 저장.
플레이어는 돌리지 않고 그대로 그리고, 바라보는 방향은 칸 가장자리의 금색 화살촉으로 표시.

### 카드 그림 만드는 법

카드는 `card_sheet.png` (카드 9칸 시트)에서 잘라 씀. 시트를 바꾸면 `python assets/make_cards.py` 로 다시 만들기.
- 시트에 있는 카드: ADVANCE, RETREAT, FIRE, RELOAD 는 그대로 자름
- 시트에 없는 카드는 빈 카드 틀로 만듦: TURN 그림 + 금색 화살촉 → 왼쪽/오른쪽 보기, ADVANCE 장화 2개(잔상) → 2칸 앞으로
- `card_slash_left.png` 는 지금 게임에 없는 카드 (기획서의 '왼쪽 공격'용으로 보관), `card_blank.png` 는 빈 틀
- 게임에서는 카드 아래 영어 이름 띠 위에 한글 이름을 덮어 씀 (assets.py 의 draw_card)

크기가 달라도 자동으로 맞춰지지만, 위 크기로 그리면 가장 깔끔함.
직접 만든 그림이 아니면 출처를 README 의 리소스 표에 적을 것 (기획서 9번).
