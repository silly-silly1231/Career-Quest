# scenes/main_hub_scene.py

import pygame
from source.config.settings import BG_COLOR, TEXT_COLOR, SCREEN_WIDTH, SCREEN_HEIGHT, FONT_NAME, ACCENT_COLOR, ROUNDED_RADIUS
from source.utils.ui import draw_panel
from source.utils.save_manager import delete_save_data, load_save
from source.scenes.chef_scene import ChefScene
from source.scenes.doctor_scene import DoctorScene
from source.scenes.software_developer_scene import SoftwareDeveloperScene

class MainHubScene:
    def __init__(self, game):
        self.game = game
        self.save = load_save()

        # Career info: name + placeholder color
        self.careers = [
            {"name": "Software Developer", "color": (180, 200, 255), "available": True},
            {"name": "Chef", "color": (255, 180, 180), "available": True},
            {"name": "Doctor", "color": (180, 255, 180), "available": True},
        ]

        self.square_margin = 40
        self.square_width = (SCREEN_WIDTH - self.square_margin * 5) // 4
        self.square_height = self.square_width  # square

        self.font = pygame.font.SysFont(FONT_NAME, 24)
        self.title_font = pygame.font.SysFont(FONT_NAME, 38, bold=True)
        self.small_font = pygame.font.SysFont(FONT_NAME, 18)
        self.job_box_height = 40  # small box for job name
        self.feedback_message = "Select a career world to begin your workday."
        self.show_reset_dialog = False

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.handle_click(event.pos)

    def update(self, delta_time):
        pass

    def handle_click(self, pos):
        if self.show_reset_dialog:
            if self._get_reset_confirm_rect().collidepoint(pos):
                delete_save_data()
                self.save = load_save()
                self.show_reset_dialog = False
                self.game.running = False
            elif self._get_reset_cancel_rect().collidepoint(pos):
                self.show_reset_dialog = False
            return

        if self._get_reset_button_rect().collidepoint(pos):
            self.show_reset_dialog = True
            return

        width, height = self.game.screen.get_size()
        for index, career in enumerate(self.careers):
            rect = self.get_career_rect(index, width, height)
            if not rect.collidepoint(pos):
                continue

            if career["name"] == "Software Developer" and career["available"]:
                self.game.scene_manager.set_scene(SoftwareDeveloperScene(self.game))
            elif career["name"] == "Chef" and career["available"]:
                self.game.scene_manager.set_scene(ChefScene(self.game))
            elif career["name"] == "Doctor" and career["available"]:
                self.game.scene_manager.set_scene(DoctorScene(self.game))
            else:
                self.feedback_message = "More career worlds are coming soon."
            return

    def get_career_rect(self, index, width, height):
        card_count = len(self.careers)
        self.square_width = (width - self.square_margin * (card_count + 1)) // card_count
        self.square_height = self.square_width
        x = self.square_margin + index * (self.square_width + self.square_margin)
        y = (height - self.square_height) // 2
        return pygame.Rect(x, y, self.square_width, self.square_height)

    def render(self, screen):
        screen.fill(BG_COLOR)

        width, height = screen.get_width(), screen.get_height()
        title_font = self._get_scaled_font(38, minimum=38, bold=True)
        subtitle_font = self._get_scaled_font(18, minimum=18)
        label_font = self._get_scaled_font(24, minimum=20)

        title_surface = title_font.render("Career Hub", True, TEXT_COLOR)
        screen.blit(title_surface, (40, 35))
        subtitle = subtitle_font.render(self.feedback_message, True, TEXT_COLOR)
        screen.blit(subtitle, (40, 35 + title_surface.get_height() + 8))

        for i, career in enumerate(self.careers):
            square_rect = self.get_career_rect(i, width, height)
            draw_panel(screen, square_rect, career["color"], border_color=ACCENT_COLOR, border_width=3)

            # Job name box (bottom of square)
            job_box_rect = pygame.Rect(
                square_rect.x,
                square_rect.y + self.square_height - self.job_box_height,
                self.square_width,
                self.job_box_height
            )

            draw_panel(screen, job_box_rect, (200, 200, 200), border_color=ACCENT_COLOR, border_width=2)

            # Job name text
            text_surface = label_font.render(career["name"], True, TEXT_COLOR)
            text_rect = text_surface.get_rect(center=job_box_rect.center)
            screen.blit(text_surface, text_rect)

            if not career["available"]:
                overlay = pygame.Surface((self.square_width, self.square_height), pygame.SRCALPHA)
                pygame.draw.rect(
                    overlay,
                    (80, 80, 80, 110),
                    overlay.get_rect(),
                    border_radius=ROUNDED_RADIUS,
                )
                screen.blit(overlay, square_rect.topleft)
                coming_text = subtitle_font.render("Coming Soon", True, TEXT_COLOR)
                coming_rect = coming_text.get_rect(center=(square_rect.centerx, square_rect.centery))
                screen.blit(coming_text, coming_rect)

            if career["name"] in self.save.get("completed_careers", []):
                complete_text = subtitle_font.render("Completed", True, TEXT_COLOR)
                complete_rect = complete_text.get_rect(midtop=(square_rect.centerx, square_rect.y + 12))
                screen.blit(complete_text, complete_rect)

        reset_button_rect = self._get_reset_button_rect()
        draw_panel(screen, reset_button_rect, (215, 225, 235), border_color=ACCENT_COLOR, border_width=2)
        reset_text = subtitle_font.render("Reset Data", True, TEXT_COLOR)
        reset_text_rect = reset_text.get_rect(center=reset_button_rect.center)
        screen.blit(reset_text, reset_text_rect)

        if self.show_reset_dialog:
            overlay = pygame.Surface((width, height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 90))
            screen.blit(overlay, (0, 0))

            dialog_rect = self._get_reset_dialog_rect()
            draw_panel(screen, dialog_rect, (245, 245, 245), border_color=ACCENT_COLOR, border_width=3)

            question_text = subtitle_font.render("Reset all data?", True, TEXT_COLOR)
            question_rect = question_text.get_rect(center=(dialog_rect.centerx, dialog_rect.y + 55))
            screen.blit(question_text, question_rect)

            confirm_rect = self._get_reset_confirm_rect()
            cancel_rect = self._get_reset_cancel_rect()
            draw_panel(screen, confirm_rect, (235, 190, 190), border_color=ACCENT_COLOR, border_width=2)
            draw_panel(screen, cancel_rect, (200, 220, 200), border_color=ACCENT_COLOR, border_width=2)

            confirm_text = subtitle_font.render("Yes", True, TEXT_COLOR)
            cancel_text = subtitle_font.render("No", True, TEXT_COLOR)
            screen.blit(confirm_text, confirm_text.get_rect(center=confirm_rect.center))
            screen.blit(cancel_text, cancel_text.get_rect(center=cancel_rect.center))

    def _get_scaled_font(self, size, minimum=18, bold=False):
        width, height = self.game.screen.get_size()
        scale = max(1.0, min(width / SCREEN_WIDTH, height / SCREEN_HEIGHT))
        return pygame.font.SysFont(FONT_NAME, max(minimum, int(size * scale)), bold=bold)

    def _get_reset_button_rect(self):
        width, height = self.game.screen.get_size()
        return pygame.Rect(width - 180, height - 70, 140, 40)

    def _get_reset_dialog_rect(self):
        width, height = self.game.screen.get_size()
        return pygame.Rect((width - 380) // 2, (height - 190) // 2, 380, 190)

    def _get_reset_confirm_rect(self):
        dialog_rect = self._get_reset_dialog_rect()
        return pygame.Rect(dialog_rect.x + 45, dialog_rect.bottom - 70, 130, 42)

    def _get_reset_cancel_rect(self):
        dialog_rect = self._get_reset_dialog_rect()
        return pygame.Rect(dialog_rect.right - 175, dialog_rect.bottom - 70, 130, 42)