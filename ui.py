"""
그리기 도구 (담당: 표현 주서연)
- 화면마다 반복해서 쓰는 사각형, 글자, 버튼을 모아 둠
- 모든 화면은 이 함수들로 그림 → 디자인을 바꿀 때 여기만 고치면 전체가 바뀜
"""
import pygame

from settings import BLACK, GRAY, FONT_NAME

_fonts = {}  # 크기별 폰트 캐시 (매 프레임 폰트를 새로 만들지 않도록)


def font(size):
    if size not in _fonts:
        _fonts[size] = pygame.font.SysFont(FONT_NAME, size)
    return _fonts[size]


def box(surf, rect, width=3):
    """검은 테두리 사각형. rect = (x, y, 너비, 높이)"""
    pygame.draw.rect(surf, BLACK, rect, width)


def label(surf, x, y, text, size=20):
    """(x, y) 를 중심으로 글자 쓰기."""
    img = font(size).render(text, True, BLACK)
    surf.blit(img, img.get_rect(center=(x, y)))


class Button:
    """클릭 가능한 사각형 버튼. 마우스를 올리면 회색으로 바뀜."""

    def __init__(self, rect, text, size=20):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.size = size

    def draw(self, surf):
        if self.rect.collidepoint(pygame.mouse.get_pos()):
            pygame.draw.rect(surf, GRAY, self.rect)
        box(surf, self.rect, 2)
        label(surf, *self.rect.center, self.text, self.size)

    def clicked(self, event):
        """이 이벤트가 버튼 위에서 왼쪽 클릭이면 True."""
        return (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                and self.rect.collidepoint(event.pos))
