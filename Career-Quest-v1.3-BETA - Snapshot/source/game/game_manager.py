# game/game_manager.py

import pygame
from source.config.settings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE, BG_COLOR
from source.game.scene_manager import SceneManager
from source.scenes.startup_scene import StartupScene

class GameManager:
    def __init__(self):
        self.base_size = (SCREEN_WIDTH, SCREEN_HEIGHT)
        self.window = pygame.display.set_mode(self.base_size, pygame.RESIZABLE)
        self.screen = pygame.Surface(self.base_size).convert()
        self.viewport_rect = self._calculate_viewport(self.window.get_size())
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.running = True

        self.scene_manager = SceneManager()
        self.scene_manager.set_scene(StartupScene(self))

    def _calculate_viewport(self, window_size):
        window_width, window_height = window_size
        base_width, base_height = self.base_size
        scale = min(window_width / base_width, window_height / base_height)
        render_width = max(1, int(base_width * scale))
        render_height = max(1, int(base_height * scale))
        return pygame.Rect(
            (window_width - render_width) // 2,
            (window_height - render_height) // 2,
            render_width,
            render_height,
        )

    def _translate_mouse_event(self, event):
        if not hasattr(event, "pos"):
            return event

        if not self.viewport_rect.collidepoint(event.pos):
            return None

        base_width, base_height = self.base_size
        translated_x = int((event.pos[0] - self.viewport_rect.x) * base_width / self.viewport_rect.w)
        translated_y = int((event.pos[1] - self.viewport_rect.y) * base_height / self.viewport_rect.h)

        event_data = event.dict.copy()
        event_data["pos"] = (translated_x, translated_y)

        if "rel" in event_data:
            event_data["rel"] = (
                int(event_data["rel"][0] * base_width / self.viewport_rect.w),
                int(event_data["rel"][1] * base_height / self.viewport_rect.h),
            )

        return pygame.event.Event(event.type, event_data)

    def _is_modal_overlay_active(self):
        current_scene = self.scene_manager.current_scene
        return bool(current_scene and getattr(current_scene, "show_reset_dialog", False))

    def _get_window_background_color(self):
        if not self._is_modal_overlay_active():
            return BG_COLOR

        return tuple(max(0, channel - 80) for channel in BG_COLOR)

    def run(self):
        while self.running:
            delta_time = self.clock.tick(FPS) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.VIDEORESIZE:
                    self.window = pygame.display.set_mode(event.size, pygame.RESIZABLE)
                    self.viewport_rect = self._calculate_viewport(self.window.get_size())
                elif event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
                    translated_event = self._translate_mouse_event(event)
                    if translated_event is not None:
                        self.scene_manager.handle_event(translated_event)
                else:
                    self.scene_manager.handle_event(event)

            self.scene_manager.update(delta_time)
            self.scene_manager.render(self.screen)

            self.window.fill(self._get_window_background_color())
            scaled_surface = pygame.transform.smoothscale(self.screen, self.viewport_rect.size)
            self.window.blit(scaled_surface, self.viewport_rect)

            pygame.display.flip()