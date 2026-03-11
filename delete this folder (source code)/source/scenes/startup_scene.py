# scenes/startup_scene.py

import pygame
from source.config.settings import BG_COLOR, TEXT_COLOR, SCREEN_WIDTH, SCREEN_HEIGHT, FONT_NAME, ACCENT_COLOR
from source.utils.ui import draw_panel, draw_button
from source.utils.save_manager import load_save, save_data
from source.scenes.main_hub_scene import MainHubScene


class StartupScene:
    def __init__(self, game):
        self.game = game
        self.started = False

        # Dialogue content
        self.dialogue_lines = [
            "Welcome to Career Quest.",
            "This game is your interactive journey into different careers.",
            "Instead of reading about jobs, you'll experience them.",
            "Each world shows you what one day in that profession feels like.",
            "You'll complete real skill-based challenges inspired by that career.",
            "By the end, you'll understand what the job involves...",
            "...and the skills you'll need to succeed.",
            "Ready to begin your first career adventure?"
        ]
        self.current_line = 0

        # Typewriter effect
        self.char_index = 0
        self.typing_speed = 50  # characters per second
        self.typing_timer = 0
        self.is_typing = True

        self.save = load_save()
        self.tutorial_completed = self.save.get("tutorial_dialogue_completed", False)

        # If no save exists or tutorial not completed, continue as normal

    # --------------------------
    # Handle input
    # --------------------------
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.running = False
            return

        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return

        if not self.started and self._play_button_rect().collidepoint(event.pos):
            if self.tutorial_completed:
                self.game.scene_manager.set_scene(MainHubScene(self.game))
                return

            self.started = True
            save_data(self.save)
            return

        if self.started and self._dialogue_button_rect().collidepoint(event.pos):
            self.advance_dialogue()

    # --------------------------
    # Update
    # --------------------------
    def update(self, delta_time):
        if self.started and self.is_typing:
            self.typing_timer += delta_time
            if self.typing_timer >= 1 / self.typing_speed:
                self.typing_timer = 0
                self.char_index += 1
                if self.char_index >= len(self.dialogue_lines[self.current_line]):
                    self.char_index = len(self.dialogue_lines[self.current_line])
                    self.is_typing = False

    # --------------------------
    # Render
    # --------------------------
    def render(self, screen):
        screen.fill(BG_COLOR)
        if not self.started:
            self.render_intro(screen)
        else:
            self.render_character_scene(screen)

    # --------------------------
    # Intro screen
    # --------------------------
    def render_intro(self, screen):
        width, height = screen.get_width(), screen.get_height()
        title_font = self._get_font(72, bold=True, minimum=44)
        button_font = self._get_font(30, bold=True, minimum=22)

        title_surface = title_font.render("Career Quest", True, TEXT_COLOR)
        title_rect = title_surface.get_rect(center=(width // 2, height // 2 - title_surface.get_height()))
        screen.blit(title_surface, title_rect)

        draw_button(
            screen,
            self._play_button_rect(),
            "Play",
            button_font,
            (221, 233, 248),
            TEXT_COLOR,
            border_color=ACCENT_COLOR,
        )

    # --------------------------
    # Character + dialogue scene
    # --------------------------
    def render_character_scene(self, screen):
        width, height = screen.get_size()
        scale = self._ui_scale(width, height)
        margin = max(24, int(32 * scale))
        gap = max(16, int(20 * scale))
        dialogue_rect = self._dialogue_rect()
        draw_panel(screen, dialogue_rect, (230, 220, 200), border_color=ACCENT_COLOR, border_width=3)

        # Placeholder character
        character_height = max(170, min(int(height * 0.38), dialogue_rect.top - margin * 2))
        character_width = max(140, int(character_height * 0.7))
        character_rect = pygame.Rect(
            0,
            0,
            character_width,
            character_height
        )
        character_rect.midbottom = (width // 2, dialogue_rect.top - gap)
        draw_panel(screen, character_rect, (180, 180, 180), border_color=ACCENT_COLOR, border_width=3)

        # Typewriter text
        dialogue_font = self._get_font(28, minimum=20)
        full_text = self.dialogue_lines[self.current_line]
        visible_text = full_text[:self.char_index]
        button_rect = self._dialogue_button_rect()
        self.draw_wrapped_text(
            screen,
            visible_text,
            dialogue_font,
            dialogue_rect.x + margin,
            dialogue_rect.y + margin,
            dialogue_rect.w - margin * 2 - button_rect.w - gap,
        )
        draw_button(
            screen,
            button_rect,
            "Next" if self.current_line < len(self.dialogue_lines) - 1 else "Continue",
            self._get_font(24, minimum=17),
            (221, 233, 248),
            TEXT_COLOR,
            border_color=ACCENT_COLOR,
        )

    def _ui_scale(self, width, height):
        return max(0.75, min(width / SCREEN_WIDTH, height / SCREEN_HEIGHT))

    def _get_font(self, size, bold=False, minimum=18):
        width, height = self.game.screen.get_size()
        scaled_size = max(minimum, int(size * self._ui_scale(width, height)))
        return pygame.font.SysFont(FONT_NAME, scaled_size, bold=bold)

    # --------------------------
    # Start new line typing
    # --------------------------
    def start_typing_new_line(self):
        self.char_index = 0
        self.typing_timer = 0
        self.is_typing = True

    def complete_current_line(self):
        self.char_index = len(self.dialogue_lines[self.current_line])
        self.typing_timer = 0
        self.is_typing = False

    def advance_dialogue(self):
        if self.is_typing:
            self.complete_current_line()
            return

        if self.current_line < len(self.dialogue_lines) - 1:
            self.current_line += 1
            self.start_typing_new_line()
            return

        self.save["tutorial_dialogue_completed"] = True
        save_data(self.save)
        self.game.scene_manager.set_scene(MainHubScene(self.game))

    def _dialogue_rect(self):
        width, height = self.game.screen.get_size()
        scale = self._ui_scale(width, height)
        margin = max(24, int(32 * scale))
        dialogue_height = max(180, min(int(height * 0.34), height - margin * 2))
        return pygame.Rect(
            margin,
            height - dialogue_height - margin,
            width - margin * 2,
            dialogue_height,
        )

    def _dialogue_button_rect(self):
        dialogue_rect = self._dialogue_rect()
        width, height = self.game.screen.get_size()
        scale = self._ui_scale(width, height)
        button_width = max(180, int(260 * scale))
        button_height = max(48, int(60 * scale))
        margin = max(16, int(18 * scale))
        return pygame.Rect(
            dialogue_rect.right - button_width - margin,
            dialogue_rect.bottom - button_height - margin,
            button_width,
            button_height,
        )

    def _play_button_rect(self):
        width, height = self.game.screen.get_size()
        scale = self._ui_scale(width, height)
        button_width = max(180, int(240 * scale))
        button_height = max(54, int(68 * scale))
        return pygame.Rect(
            (width - button_width) // 2,
            height // 2 + max(28, int(36 * scale)),
            button_width,
            button_height,
        )

    # --------------------------
    # Text wrapping
    # --------------------------
    def draw_wrapped_text(self, surface, text, font, x, y, max_width):
        words = text.split(' ')
        lines = []
        current_line = ""
        for word in words:
            test_line = current_line + word + " "
            if font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word + " "
        lines.append(current_line)
        for i, line in enumerate(lines):
            text_surface = font.render(line.strip(), True, TEXT_COLOR)
            surface.blit(text_surface, (x, y + i * (font.get_height() + 8)))