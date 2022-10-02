import pygame

from pongy.models import MoveDirection


class KeyBoardControls:
    @staticmethod
    def is_exit_pressed() -> bool:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    return True
        return False

    @staticmethod
    def get_action() -> None | MoveDirection:
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_UP]:
            return MoveDirection.LEFT
        if keys[pygame.K_RIGHT] or keys[pygame.K_DOWN]:
            return MoveDirection.RIGHT
        return None
