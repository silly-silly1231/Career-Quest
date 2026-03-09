# game/game_manager.py

import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE
from game.scene_manager import SceneManager
from scenes.startup_scene import StartupScene

class GameManager:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.running = True

        self.scene_manager = SceneManager()
        self.scene_manager.set_scene(StartupScene(self))

    def run(self):
        while self.running:
            delta_time = self.clock.tick(FPS) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)
                else:
                    self.scene_manager.handle_event(event)

            self.scene_manager.update(delta_time)
            self.scene_manager.render(self.screen)

            pygame.display.flip()