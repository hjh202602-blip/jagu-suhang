# 그림 넣는 곳 (표현 주서연)

이 폴더에 아래 이름으로 PNG 를 넣으면 게임이 자동으로 그 그림을 씀. 없으면 글자로 된 임시 그림이 나옴.
이름 목록은 `assets.py` 의 `IMAGE_FILES` 와 같음.

| 파일 | 그림 | 크기 |
|---|---|---|
| `wall.png` | 벽 | 46x46 |
| `exit.png` | 출구 | 46x46 |
| `flip.png` | 뒤집기 타일 | 46x46 |
| `player.png` | 플레이어 (**위를 보는** 모습, 방향은 자동 회전) | 46x46 |
| `chaser.png` | 추적자 | 46x46 |
| `dummy.png` | 허수아비 | 46x46 |
| `bullet_fire.png` / `bullet_ice.png` / `bullet_bomb.png` | 바닥의 화염탄 / 빙결탄 / 폭발탄 | 46x46 |
| `card_forward.png` / `card_back.png` | 앞으로 이동 / 뒤로 이동 카드 | 100x115 |
| `card_turn_left.png` / `card_turn_right.png` | 왼쪽 보기 / 오른쪽 보기 카드 | 100x115 |
| `card_fire.png` / `card_reload.png` | 발사 / 재장전 카드 | 100x115 |

크기가 달라도 자동으로 맞춰지지만, 위 크기로 그리면 가장 깔끔함.
직접 만든 그림이 아니면 출처를 README 의 리소스 표에 적을 것 (기획서 9번).
