import os
import random

import pygame

from source.config.settings import BG_COLOR, TEXT_COLOR, ACCENT_COLOR, FONT_NAME
from source.utils.save_manager import load_save, save_data
from source.utils.ui import draw_panel, draw_button


ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")


class ChefScene:
    def __init__(self, game):
        self.game = game

        self.stage_order = [
            "overview",
            "briefing_dialogue",
            "prep_sort",
            "order_dialogue",
            "station_timing",
            "rush_dialogue",
            "plating",
            "inspection_dialogue",
            "service_sprint",
            "closing_dialogue",
            "results",
        ]
        self.stage_index = 0
        self.active_stage = self.stage_order[self.stage_index]

        self.skill_scores = {
            "timing": 0,
            "precision": 0,
            "organization": 0,
            "composure": 0,
        }

        self.overview_lines = [
            "Chefs lead a kitchen by planning prep, cooking dishes, plating meals, and keeping service moving.",
            "They balance speed with accuracy while coordinating ingredients, timing, and teamwork.",
        ]
        self.key_skills = [
            "Timing",
            "Organization",
            "Precision",
            "Composure",
            "Communication",
        ]

        self.dialogues = {
            "briefing_dialogue": [
                "Head Chef: Lunch service starts soon, so we need a clean prep station.",
                "Sous Chef: Orders are already stacking up for grilled chicken bowls.",
                "Head Chef: Stay organized now and the whole kitchen will move faster later.",
            ],
            "order_dialogue": [
                "Server: Two new tables just sat down and they both want hot food fast.",
                "Head Chef: Pick the right heat for each dish or service will bottleneck.",
                "Head Chef: A great chef controls the station instead of reacting too late.",
            ],
            "rush_dialogue": [
                "Expo: Table twelve needs a full pickup in three minutes.",
                "Head Chef: Plating matters. Guests taste with their eyes before the first bite.",
                "Head Chef: Build the plate in the right order so it arrives balanced and clean.",
            ],
            "inspection_dialogue": [
                "Restaurant Manager: A reviewer just walked in for dinner service.",
                "Expo: Tickets are flying in, and every dish needs to match the order exactly.",
                "Head Chef: Stay calm, read the ticket, and send the right plate every time.",
            ],
            "closing_dialogue": [
                "Head Chef: Service is complete and the dining room is happy.",
                "Server: Orders came out on time and the plates looked excellent.",
                "Head Chef: That is what a strong kitchen shift feels like.",
            ],
        }
        self.dialogue_state = {
            stage: {"index": 0, "char_index": 0, "timer": 0.0, "is_typing": True}
            for stage in self.dialogues
        }
        self.typing_speed = 55

        self.prep_correct_order = [
            "Wash produce",
            "Slice vegetables",
            "Season chicken",
            "Heat the pan",
        ]
        self.prep_cards = self.prep_correct_order[:]
        random.shuffle(self.prep_cards)
        self.prep_completed = []
        self.prep_feedback = "Click the prep tasks in the order a chef should do them before service."

        self.station_rounds = [
            {
                "dish": "Tomato soup",
                "goal": "Keep it gently bubbling without burning the bottom.",
                "correct": "Low",
                "reason": "Correct. Soups hold best over low heat so flavor stays steady.",
            },
            {
                "dish": "Seared salmon",
                "goal": "Build a crisp edge while keeping the center tender.",
                "correct": "Medium-High",
                "reason": "Correct. Medium-high heat gives a sear without overcooking the fish.",
            },
            {
                "dish": "Stir-fried vegetables",
                "goal": "Cook fast so they stay bright instead of steaming.",
                "correct": "High",
                "reason": "Correct. High heat keeps the vegetables crisp and quick.",
            },
        ]
        self.station_options = ["Low", "Medium-High", "High"]
        self.station_round_index = 0
        self.station_feedback = "Choose the best heat level for the dish on the ticket."

        self.plating_correct_order = [
            "Starch base",
            "Main protein",
            "Vegetables",
            "Sauce finish",
        ]
        self.plating_pool = self.plating_correct_order[:]
        random.shuffle(self.plating_pool)
        self.plating_slots = [None, None, None, None]
        self.plating_selected_item = None
        self.plating_feedback = "Build the plate in a clean order, then check it for service."

        self.service_time_limit = 45.0
        self.service_time_left = self.service_time_limit
        self.service_rounds = [
            {
                "ticket": "Ticket: Steak frites, medium, no garnish",
                "options": ["Steak frites, medium, no garnish", "Steak frites, rare, no garnish", "Salmon with fries"],
                "correct": 0,
            },
            {
                "ticket": "Ticket: Chicken bowl with extra greens",
                "options": ["Chicken bowl with rice", "Chicken bowl with extra greens", "Chicken salad wrap"],
                "correct": 1,
            },
            {
                "ticket": "Ticket: Pasta alfredo, add mushrooms",
                "options": ["Pasta marinara", "Pasta alfredo, no mushrooms", "Pasta alfredo, add mushrooms"],
                "correct": 2,
            },
            {
                "ticket": "Ticket: Burger, no onions, side salad",
                "options": ["Burger, no onions, side salad", "Burger with onions, fries", "Turkey sandwich, side salad"],
                "correct": 0,
            },
            {
                "ticket": "Ticket: Veggie flatbread, extra basil",
                "options": ["Veggie flatbread, extra basil", "Veggie pizza, no basil", "Caprese salad"],
                "correct": 0,
            },
            {
                "ticket": "Ticket: Salmon bowl, sauce on side",
                "options": ["Salmon bowl, extra sauce", "Salmon bowl, sauce on side", "Chicken bowl, sauce on side"],
                "correct": 1,
            },
        ]
        self.service_round_index = 0
        self.service_hits = 0
        self.service_feedback = "Read the ticket and click the plated dish that matches it exactly."
        self.service_finished = False

        self.steam_bubbles = []
        self._star_icon_source = None
        self._star_icon_cache = {}
        self._seed_steam_bubbles()

    def _seed_steam_bubbles(self):
        for _ in range(12):
            self.steam_bubbles.append(
                {
                    "x_ratio": random.uniform(0.16, 0.84),
                    "y_ratio": random.uniform(0.24, 0.80),
                    "size_ratio": random.uniform(0.015, 0.04),
                }
            )

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.return_to_hub()
            return

        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return

        if self.active_stage == "overview":
            back_button_rect, start_button_rect = self._overview_button_rects()
            if back_button_rect.collidepoint(event.pos):
                self.return_to_hub()
            elif start_button_rect.collidepoint(event.pos):
                self.advance_stage()
        elif self.active_stage in self.dialogues:
            if self._continue_button_rect().collidepoint(event.pos):
                self.advance_dialogue_stage()
        elif self.active_stage == "prep_sort":
            self.handle_prep_sort_click(event.pos)
        elif self.active_stage == "station_timing":
            self.handle_station_timing_click(event.pos)
        elif self.active_stage == "plating":
            self.handle_plating_click(event.pos)
        elif self.active_stage == "service_sprint":
            self.handle_service_click(event.pos)
        elif self.active_stage == "results":
            if self._results_button_rect().collidepoint(event.pos):
                self.finish_world()

    def update(self, delta_time):
        if self.active_stage in self.dialogues:
            self.update_dialogue(delta_time)
        elif self.active_stage == "service_sprint" and not self.service_finished:
            self.service_time_left = max(0.0, self.service_time_left - delta_time)
            if self.service_time_left <= 0:
                self.complete_service_sprint()

    def render(self, screen):
        screen.fill(BG_COLOR)
        if self.active_stage == "overview":
            self.render_overview(screen)
        elif self.active_stage in self.dialogues:
            self.render_dialogue_stage(screen)
        elif self.active_stage == "prep_sort":
            self.render_prep_sort(screen)
        elif self.active_stage == "station_timing":
            self.render_station_timing(screen)
        elif self.active_stage == "plating":
            self.render_plating(screen)
        elif self.active_stage == "service_sprint":
            self.render_service_sprint(screen)
        elif self.active_stage == "results":
            self.render_results(screen)

    def advance_stage(self):
        if self.stage_index < len(self.stage_order) - 1:
            self.stage_index += 1
            self.active_stage = self.stage_order[self.stage_index]

    def update_dialogue(self, delta_time):
        state = self.dialogue_state[self.active_stage]
        if not state["is_typing"]:
            return

        state["timer"] += delta_time
        if state["timer"] >= 1 / self.typing_speed:
            state["timer"] = 0.0
            line = self.dialogues[self.active_stage][state["index"]]
            state["char_index"] += 1
            if state["char_index"] >= len(line):
                state["char_index"] = len(line)
                state["is_typing"] = False

    def advance_dialogue_stage(self):
        state = self.dialogue_state[self.active_stage]
        if state["is_typing"]:
            self.complete_dialogue_line(state)
            return

        if state["index"] < len(self.dialogues[self.active_stage]) - 1:
            state["index"] += 1
            state["char_index"] = 0
            state["timer"] = 0.0
            state["is_typing"] = True
            return

        self.advance_stage()

    def handle_prep_sort_click(self, pos):
        if self._hint_button_rect().collidepoint(pos):
            self.prep_feedback = "Hint: Start with clean ingredients, then cut, season, and finally heat the pan."
            return

        if self._action_button_rect().collidepoint(pos):
            self.prep_completed = []
            self.prep_feedback = "Prep board reset. Click the tasks in the right order."
            return

        next_index = len(self.prep_completed)
        for index, rect in enumerate(self._prep_card_rects()):
            if not rect.collidepoint(pos):
                continue

            card = self.prep_cards[index]
            if card in self.prep_completed:
                return

            if card == self.prep_correct_order[next_index]:
                self.prep_completed.append(card)
                if len(self.prep_completed) == len(self.prep_correct_order):
                    self.skill_scores["organization"] = 4
                    self.prep_feedback = "Station ready. Organized prep makes the rest of service smoother."
                    self.advance_stage()
                else:
                    self.prep_feedback = f"Good. {len(self.prep_completed)} prep steps locked in."
            else:
                self.prep_feedback = "That step comes later. Kitchens run best when prep happens in order."
            return

    def handle_station_timing_click(self, pos):
        for option, rect in self._station_option_rects().items():
            if not rect.collidepoint(pos):
                continue

            round_data = self.current_station_round()
            if option == round_data["correct"]:
                self.station_feedback = round_data["reason"]
                self.station_round_index += 1
                if self.station_round_index >= len(self.station_rounds):
                    self.skill_scores["timing"] = 4
                    self.advance_stage()
            else:
                self.station_feedback = f"Not quite. {option} would throw off the dish timing."
            return

    def handle_plating_click(self, pos):
        if self._hint_button_rect().collidepoint(pos):
            self.plating_feedback = "Hint: The base goes down first, the main item anchors the dish, and the finish comes last."
            return

        if self._action_button_rect().collidepoint(pos):
            if self.plating_slots == self.plating_correct_order:
                self.skill_scores["precision"] = 4
                self.plating_feedback = "Plate approved. Clean structure helps food look intentional."
                self.advance_stage()
            else:
                self.plating_feedback = "That plating order feels messy. Rebuild it before it goes to the dining room."
            return

        for index, rect in enumerate(self._plating_pool_rects()):
            if rect.collidepoint(pos) and index < len(self.plating_pool):
                self.plating_selected_item = self.plating_pool[index]
                return

        for index, rect in enumerate(self._plating_slot_rects()):
            if not rect.collidepoint(pos):
                continue

            if self.plating_slots[index] is not None:
                self.plating_pool.append(self.plating_slots[index])
                self.plating_slots[index] = None
                return

            if self.plating_selected_item is not None:
                self.plating_slots[index] = self.plating_selected_item
                self.plating_pool.remove(self.plating_selected_item)
                self.plating_selected_item = None
                return

    def handle_service_click(self, pos):
        if self.service_finished:
            if self._continue_button_rect().collidepoint(pos):
                self.advance_stage()
            return

        for index, rect in enumerate(self._service_option_rects()):
            if not rect.collidepoint(pos):
                continue

            current_round = self.current_service_round()
            if index == current_round["correct"]:
                self.service_hits += 1
                self.service_feedback = "Correct pickup. Keep the pass moving."
                self.service_round_index += 1
                if self.service_round_index >= len(self.service_rounds):
                    self.complete_service_sprint()
            else:
                self.service_feedback = "Wrong dish. Compare the ticket details more carefully."
            return

    def complete_service_sprint(self):
        self.service_finished = True
        self.skill_scores["composure"] = min(5, max(1, self.service_hits))
        self.skill_scores["organization"] = max(self.skill_scores["organization"], min(5, 3 + (self.service_hits // 2)))
        self.service_feedback = "Service finished. Strong chefs stay accurate even when the kitchen gets loud."

    def finish_world(self):
        from source.scenes.main_hub_scene import MainHubScene

        save = load_save()
        completed = save.setdefault("completed_careers", [])
        if "Chef" not in completed:
            completed.append("Chef")

        skills = save.setdefault("skills", {})
        for key, value in self.skill_scores.items():
            skills[key] = max(value, skills.get(key, 0))

        reports = save.setdefault("career_reports", {})
        reports["Chef"] = dict(self.skill_scores)
        save_data(save)

        self.game.scene_manager.set_scene(MainHubScene(self.game))

    def return_to_hub(self):
        from source.scenes.main_hub_scene import MainHubScene

        self.game.scene_manager.set_scene(MainHubScene(self.game))

    def complete_dialogue_line(self, state):
        line = self.dialogues[self.active_stage][state["index"]]
        state["char_index"] = len(line)
        state["timer"] = 0.0
        state["is_typing"] = False

    def render_overview(self, screen):
        title_font = self._get_font(42, bold=True, minimum=28)
        heading_font = self._get_font(30, bold=True, minimum=22)
        body_font = self._get_font(24, minimum=17)
        header_rect, panel_rect = self._overview_rects()
        scale = self._ui_scale()
        content_padding = max(18, int(28 * scale))
        column_gap = max(18, int(22 * scale))
        sidebar_width = max(220, int(panel_rect.w * 0.33))
        main_x = panel_rect.x + content_padding
        main_y = panel_rect.y + content_padding
        main_width = panel_rect.w - (content_padding * 2) - sidebar_width - column_gap
        sidebar_x = main_x + main_width + column_gap
        sidebar_y = main_y
        back_button_rect, start_button_rect = self._overview_button_rects()

        draw_panel(screen, header_rect, (255, 243, 233), border_color=ACCENT_COLOR, border_width=3)
        draw_panel(screen, panel_rect, (253, 249, 241), border_color=ACCENT_COLOR, border_width=3)

        self.draw_text(screen, "Career World: Chef", title_font, TEXT_COLOR, header_rect.x + 30, header_rect.y + 22)
        self.draw_text(screen, "Kitchen Overview", heading_font, TEXT_COLOR, header_rect.x + 30, header_rect.y + title_font.get_height() + 30)

        y = main_y
        self.draw_text(screen, "What You Do", heading_font, TEXT_COLOR, main_x, y)
        y += heading_font.get_height() + max(10, int(14 * scale))
        for line in self.overview_lines:
            y = self.draw_wrapped_text(screen, line, body_font, TEXT_COLOR, main_x, y, main_width) + max(10, int(14 * scale))

        self.draw_text(screen, "Key Skills", heading_font, TEXT_COLOR, sidebar_x, sidebar_y)
        y = sidebar_y + heading_font.get_height() + max(12, int(14 * scale))
        for skill in self.key_skills:
            y = self.draw_wrapped_text(screen, f"• {skill}", body_font, TEXT_COLOR, sidebar_x + 12, y, sidebar_width - 20) + max(4, int(6 * scale))

        self.draw_button(screen, back_button_rect, "Back", font=body_font)
        self.draw_button(screen, start_button_rect, "Start Workday", font=body_font)

    def render_dialogue_stage(self, screen):
        title_font = self._get_font(42, bold=True, minimum=28)
        heading_font = self._get_font(30, bold=True, minimum=22)
        body_font = self._get_font(24, minimum=17)
        small_font = self._get_font(20, minimum=15)
        avatar_rect, scene_rect, dialogue_rect = self._dialogue_rects()
        scale = self._ui_scale()

        self.draw_text(screen, "Chef Workday", title_font, TEXT_COLOR, avatar_rect.x, max(18, avatar_rect.y - title_font.get_height() - 16))

        draw_panel(screen, avatar_rect, (230, 221, 206), border_color=ACCENT_COLOR, border_width=3)
        draw_panel(screen, scene_rect, (248, 237, 224), border_color=ACCENT_COLOR, border_width=3)
        draw_panel(screen, dialogue_rect, (255, 252, 246), border_color=ACCENT_COLOR, border_width=3)

        self._draw_chef_avatar(screen, avatar_rect)
        self.draw_text(screen, self.stage_label(), heading_font, TEXT_COLOR, scene_rect.x + 20, scene_rect.y + 20)
        self.draw_wrapped_text(
            screen,
            "You read the kitchen, prioritize the next task, and keep the line moving with calm decisions.",
            body_font,
            TEXT_COLOR,
            scene_rect.x + 20,
            scene_rect.y + 20 + heading_font.get_height() + 14,
            scene_rect.w - 40,
        )

        pass_rect = pygame.Rect(
            scene_rect.x + max(18, int(22 * scale)),
            scene_rect.bottom - max(74, int(92 * scale)),
            scene_rect.w - max(36, int(44 * scale)),
            max(24, int(28 * scale)),
        )
        draw_panel(screen, pass_rect, (232, 213, 184), border_color=ACCENT_COLOR, border_width=2, radius=14, shadow=False)
        for index in range(3):
            dome_rect = pygame.Rect(
                pass_rect.x + max(12, int(18 * scale)) + index * max(82, int(104 * scale)),
                pass_rect.y - max(18, int(20 * scale)),
                max(52, int(60 * scale)),
                max(22, int(24 * scale)),
            )
            pygame.draw.ellipse(screen, (245, 244, 239), dome_rect)
            pygame.draw.rect(screen, (245, 244, 239), (dome_rect.x, dome_rect.centery - 3, dome_rect.w, 7), border_radius=4)

        state = self.dialogue_state[self.active_stage]
        line = self.dialogues[self.active_stage][state["index"]]
        visible = line[: state["char_index"]]
        button_rect = self._continue_button_rect()
        dialogue_text_width = max(180, dialogue_rect.w - 40 - button_rect.w - 20)
        self.draw_wrapped_text(screen, visible, body_font, TEXT_COLOR, dialogue_rect.x + 20, dialogue_rect.y + 20, dialogue_text_width)
        self.draw_text(screen, "Kitchen radio", small_font, TEXT_COLOR, dialogue_rect.x + 20, dialogue_rect.bottom - small_font.get_height() - 16)

        self.draw_button(
            screen,
            button_rect,
            "Next" if state["index"] < len(self.dialogues[self.active_stage]) - 1 else "Continue",
            font=body_font,
        )

    def render_prep_sort(self, screen):
        width, height = screen.get_size()
        title_font = self._get_font(42, bold=True, minimum=28)
        body_font = self._get_font(24, minimum=17)
        heading_font = self._get_font(30, bold=True, minimum=22)
        scale = self._ui_scale()
        station_rect = self._prep_station_rect()
        feedback_y = station_rect.bottom + max(14, int(18 * scale))

        self.draw_text(screen, "Skill Game 1: Prep Station", title_font, TEXT_COLOR, 60, 40)
        self.draw_wrapped_text(
            screen,
            "Set up the line for grilled chicken bowls by clicking each prep task in the right order.",
            body_font,
            TEXT_COLOR,
            60,
            95,
            width - 120,
        )

        draw_panel(screen, station_rect, (248, 241, 232), border_color=ACCENT_COLOR, border_width=3)
        self.draw_text(screen, "Prep Board", heading_font, TEXT_COLOR, station_rect.x + 24, station_rect.y + 20)

        for index, rect in enumerate(self._prep_card_rects()):
            card = self.prep_cards[index]
            is_done = card in self.prep_completed
            fill = (214, 236, 213) if is_done else (255, 251, 245)
            draw_panel(screen, rect, fill, border_color=ACCENT_COLOR, border_width=2, radius=14, shadow=False)
            self.draw_wrapped_text(screen, card, body_font, TEXT_COLOR, rect.x + 14, rect.y + 18, rect.w - 28)
            if is_done:
                self.draw_text(screen, "Done", body_font, TEXT_COLOR, rect.right - 72, rect.bottom - 38)

        self.draw_wrapped_text(screen, self.prep_feedback, body_font, TEXT_COLOR, 60, feedback_y, width - 120)
        self.draw_button(screen, self._hint_button_rect(), "Hint")
        self.draw_button(screen, self._action_button_rect(), "Reset Prep")

    def render_station_timing(self, screen):
        width, height = screen.get_size()
        title_font = self._get_font(42, bold=True, minimum=28)
        body_font = self._get_font(24, minimum=17)
        heading_font = self._get_font(30, bold=True, minimum=22)
        small_font = self._get_font(20, minimum=15)
        scale = self._ui_scale()

        self.draw_text(screen, "Skill Game 2: Heat Control", title_font, TEXT_COLOR, 60, 40)
        current_round = self.current_station_round()

        ticket_rect = pygame.Rect(60, 130, width - 120, max(150, int(height * 0.26)))
        draw_panel(screen, ticket_rect, (255, 249, 239), border_color=ACCENT_COLOR, border_width=3)
        self.draw_text(screen, current_round["dish"], heading_font, TEXT_COLOR, ticket_rect.x + 22, ticket_rect.y + 18)
        self.draw_wrapped_text(
            screen,
            current_round["goal"],
            body_font,
            TEXT_COLOR,
            ticket_rect.x + 22,
            ticket_rect.y + 18 + heading_font.get_height() + 16,
            ticket_rect.w - max(180, int(240 * scale)),
        )

        pan_rect = pygame.Rect(ticket_rect.right - max(150, int(190 * scale)), ticket_rect.y + 24, max(120, int(150 * scale)), max(80, int(96 * scale)))
        pygame.draw.ellipse(screen, (65, 65, 65), pan_rect)
        handle_rect = pygame.Rect(pan_rect.right - 6, pan_rect.centery - 8, max(70, int(84 * scale)), 16)
        pygame.draw.rect(screen, (95, 95, 95), handle_rect, border_radius=8)
        for bubble in self.steam_bubbles[:6]:
            x = pan_rect.x + int(pan_rect.w * bubble["x_ratio"])
            y = pan_rect.y - int(24 * scale) + int(pan_rect.h * bubble["y_ratio"] * 0.15)
            radius = max(3, int(min(pan_rect.w, pan_rect.h) * bubble["size_ratio"]))
            pygame.draw.circle(screen, (239, 239, 239), (x, y), radius)

        for option, rect in self._station_option_rects().items():
            draw_panel(screen, rect, (238, 244, 249), border_color=ACCENT_COLOR, border_width=2)
            self.draw_text(screen, option, body_font, TEXT_COLOR, rect.x + 18, rect.y + (rect.h - body_font.get_height()) // 2)

        progress_text = f"Round {min(self.station_round_index + 1, len(self.station_rounds))} of {len(self.station_rounds)}"
        self.draw_text(screen, progress_text, small_font, TEXT_COLOR, 60, height - 160)
        self.draw_wrapped_text(screen, self.station_feedback, body_font, TEXT_COLOR, 60, height - 125, width - 120)

    def render_plating(self, screen):
        width, height = screen.get_size()
        title_font = self._get_font(42, bold=True, minimum=28)
        body_font = self._get_font(24, minimum=17)
        heading_font = self._get_font(30, bold=True, minimum=22)
        scale = self._ui_scale()
        left_rect, right_rect = self._plating_panel_rects()
        feedback_y = max(left_rect.bottom, right_rect.bottom) + max(14, int(18 * scale))

        self.draw_text(screen, "Skill Game 3: Plate Builder", title_font, TEXT_COLOR, 60, 40)
        self.draw_wrapped_text(
            screen,
            "Arrange the plate so it builds from foundation to finish before it heads to the dining room.",
            body_font,
            TEXT_COLOR,
            60,
            95,
            width - 120,
        )

        draw_panel(screen, left_rect, (248, 241, 232), border_color=ACCENT_COLOR, border_width=3)
        draw_panel(screen, right_rect, (243, 247, 252), border_color=ACCENT_COLOR, border_width=3)

        self.draw_text(screen, "Components", heading_font, TEXT_COLOR, left_rect.x + 24, left_rect.y + 18)
        self.draw_text(screen, "Plating Order", heading_font, TEXT_COLOR, right_rect.x + 24, right_rect.y + 18)

        for index, rect in enumerate(self._plating_pool_rects()):
            fill = (255, 226, 203) if index < len(self.plating_pool) and self.plating_pool[index] == self.plating_selected_item else (255, 251, 245)
            draw_panel(screen, rect, fill, border_color=ACCENT_COLOR, border_width=2, radius=12, shadow=False)
            if index < len(self.plating_pool):
                self.draw_wrapped_text(screen, self.plating_pool[index], body_font, TEXT_COLOR, rect.x + 12, rect.y + 12, rect.w - 24)

        for index, rect in enumerate(self._plating_slot_rects()):
            draw_panel(screen, rect, (255, 255, 255), border_color=ACCENT_COLOR, border_width=2, radius=12, shadow=False)
            label = self.plating_slots[index] if self.plating_slots[index] else f"Slot {index + 1}"
            self.draw_wrapped_text(screen, label, body_font, TEXT_COLOR, rect.x + 12, rect.y + 10, rect.w - 24)

        self.draw_wrapped_text(screen, self.plating_feedback, body_font, TEXT_COLOR, 60, feedback_y, width - 120)
        self.draw_button(screen, self._hint_button_rect(), "Hint")
        self.draw_button(screen, self._action_button_rect(), "Check Plate")

    def render_service_sprint(self, screen):
        width, height = screen.get_size()
        title_font = self._get_font(42, bold=True, minimum=28)
        body_font = self._get_font(24, minimum=17)
        heading_font = self._get_font(30, bold=True, minimum=22)
        small_font = self._get_font(20, minimum=15)

        self.draw_text(screen, "Skill Game 4: Service Sprint", title_font, TEXT_COLOR, 60, 40)
        self.draw_text(screen, f"Time Left: {int(self.service_time_left):02d} seconds", heading_font, TEXT_COLOR, 60, 95)

        board_rect = pygame.Rect(60, 140, width - 120, max(250, height - 310))
        draw_panel(screen, board_rect, (252, 247, 239), border_color=ACCENT_COLOR, border_width=3)

        if self.service_finished:
            self.draw_wrapped_text(
                screen,
                f"You matched {self.service_hits} orders during the rush. {self.service_feedback}",
                body_font,
                TEXT_COLOR,
                board_rect.x + 24,
                board_rect.y + 28,
                board_rect.w - 48,
            )
            self.draw_button(screen, self._continue_button_rect(), "Continue")
            return

        current_round = self.current_service_round()
        ticket_rect = pygame.Rect(board_rect.x + 24, board_rect.y + 20, board_rect.w - 48, max(72, int(board_rect.h * 0.18)))
        draw_panel(screen, ticket_rect, (255, 252, 246), border_color=ACCENT_COLOR, border_width=2, radius=14, shadow=False)
        self.draw_wrapped_text(screen, current_round["ticket"], heading_font, TEXT_COLOR, ticket_rect.x + 16, ticket_rect.y + 16, ticket_rect.w - 32)

        for index, rect in enumerate(self._service_option_rects()):
            fill = (239, 243, 248) if index != current_round["correct"] else (244, 248, 240)
            draw_panel(screen, rect, fill, border_color=ACCENT_COLOR, border_width=2, radius=14, shadow=False)
            self.draw_text(screen, f"Plate {index + 1}", small_font, TEXT_COLOR, rect.x + 16, rect.y + 14)
            self.draw_wrapped_text(screen, current_round["options"][index], body_font, TEXT_COLOR, rect.x + 16, rect.y + 42, rect.w - 32)

        self.draw_wrapped_text(screen, self.service_feedback, body_font, TEXT_COLOR, 60, height - 130, width - 120)
        self.draw_text(screen, f"Orders matched: {self.service_hits}", small_font, TEXT_COLOR, 60, height - 165)

    def render_results(self, screen):
        title_font = self._get_font(42, bold=True, minimum=28)
        heading_font = self._get_font(30, bold=True, minimum=22)
        body_font = self._get_font(24, minimum=17)
        small_font = self._get_font(20, minimum=15)
        panel_rect, ratings_rect, summary_rect = self._results_layout_rects()

        draw_panel(screen, panel_rect, (252, 247, 238), border_color=ACCENT_COLOR, border_width=3, radius=22)
        self.draw_text(screen, "Chef Report", title_font, TEXT_COLOR, panel_rect.x + 24, panel_rect.y + 20)
        self.draw_wrapped_text(
            screen,
            "You completed a full kitchen shift by organizing prep, controlling heat, plating cleanly, and staying accurate during the rush.",
            body_font,
            TEXT_COLOR,
            panel_rect.x + 24,
            panel_rect.y + 20 + title_font.get_height() + 14,
            panel_rect.w - 48,
        )

        skill_cards = self._results_skill_card_rects(ratings_rect)
        ratings = [
            ("Timing", self.skill_scores["timing"]),
            ("Precision", self.skill_scores["precision"]),
            ("Organization", self.skill_scores["organization"]),
            ("Composure", self.skill_scores["composure"]),
        ]
        for index, (label, value) in enumerate(ratings):
            card_rect = skill_cards[index]
            draw_panel(screen, card_rect, (255, 252, 246), border_color=ACCENT_COLOR, border_width=2, radius=16, shadow=False)
            self.draw_text(screen, label, heading_font, TEXT_COLOR, card_rect.x + 18, card_rect.y + 16)
            self.draw_star_rating(screen, card_rect.x + 18, card_rect.y + 20 + heading_font.get_height(), value, body_font.get_height())

        draw_panel(screen, summary_rect, (255, 252, 246), border_color=ACCENT_COLOR, border_width=2, radius=18, shadow=False)
        self.draw_text(screen, "What This Career Needs", heading_font, TEXT_COLOR, summary_rect.x + 18, summary_rect.y + 16)
        self.draw_wrapped_text(
            screen,
            "Chefs coordinate ingredients, equipment, timing, plating, and teamwork to turn many small tasks into one polished guest experience.",
            body_font,
            TEXT_COLOR,
            summary_rect.x + 18,
            summary_rect.y + 18 + heading_font.get_height() + 8,
            summary_rect.w - 36,
        )

        best_skill = max(self.skill_scores, key=self.skill_scores.get)
        label_map = {
            "timing": "timing",
            "precision": "precision",
            "organization": "organization",
            "composure": "composure",
        }
        self.draw_text(screen, f"Strongest area: {label_map[best_skill].title()}", small_font, TEXT_COLOR, summary_rect.x + 18, summary_rect.bottom - small_font.get_height() - 18)
        self.draw_button(screen, self._results_button_rect(), "Return to Hub")

    def current_station_round(self):
        return self.station_rounds[min(self.station_round_index, len(self.station_rounds) - 1)]

    def current_service_round(self):
        return self.service_rounds[min(self.service_round_index, len(self.service_rounds) - 1)]

    def stage_label(self):
        labels = {
            "briefing_dialogue": "Pre-Service Briefing",
            "order_dialogue": "Orders Start Arriving",
            "rush_dialogue": "Mid-Service Rush",
            "inspection_dialogue": "Dinner Inspection",
            "closing_dialogue": "Kitchen Close",
        }
        return labels.get(self.active_stage, "Chef")

    def draw_star_rating(self, screen, x, y, value, target_height):
        clamped_value = max(1, min(5, value))
        star_icon = self._get_star_icon(target_height)
        spacing = max(4, star_icon.get_width() // 5)

        for index in range(clamped_value):
            screen.blit(star_icon, (x + index * (star_icon.get_width() + spacing), y))

    def _get_star_icon(self, target_height):
        scaled_height = max(14, int(target_height))
        cached_icon = self._star_icon_cache.get(scaled_height)
        if cached_icon is not None:
            return cached_icon

        if self._star_icon_source is None:
            star_path = os.path.join(ASSETS_DIR, "star.png")
            self._star_icon_source = pygame.image.load(star_path).convert_alpha()

        scale_ratio = scaled_height / self._star_icon_source.get_height()
        scaled_width = max(1, int(self._star_icon_source.get_width() * scale_ratio))
        scaled_icon = pygame.transform.smoothscale(self._star_icon_source, (scaled_width, scaled_height))
        self._star_icon_cache[scaled_height] = scaled_icon
        return scaled_icon

    def _draw_chef_avatar(self, screen, rect):
        center_x = rect.centerx
        scale = self._ui_scale()
        hat_rect = pygame.Rect(center_x - max(48, int(58 * scale)), rect.y + max(18, int(22 * scale)), max(96, int(116 * scale)), max(52, int(62 * scale)))
        pygame.draw.ellipse(screen, (250, 248, 244), hat_rect)
        band_rect = pygame.Rect(center_x - max(40, int(50 * scale)), hat_rect.bottom - max(10, int(12 * scale)), max(80, int(100 * scale)), max(18, int(20 * scale)))
        pygame.draw.rect(screen, (236, 232, 226), band_rect, border_radius=9)
        head_rect = pygame.Rect(center_x - max(28, int(32 * scale)), band_rect.bottom + 8, max(56, int(64 * scale)), max(68, int(78 * scale)))
        pygame.draw.ellipse(screen, (222, 188, 154), head_rect)
        coat_rect = pygame.Rect(center_x - max(54, int(62 * scale)), head_rect.bottom - 6, max(108, int(124 * scale)), rect.bottom - head_rect.bottom - max(18, int(22 * scale)))
        pygame.draw.rect(screen, (248, 248, 247), coat_rect, border_radius=16)
        pygame.draw.line(screen, ACCENT_COLOR, (coat_rect.centerx, coat_rect.y + 18), (coat_rect.centerx, coat_rect.bottom - 18), 3)
        for index in range(3):
            y = coat_rect.y + 24 + index * max(22, int(26 * scale))
            pygame.draw.circle(screen, ACCENT_COLOR, (coat_rect.centerx - 14, y), 4)
            pygame.draw.circle(screen, ACCENT_COLOR, (coat_rect.centerx + 14, y), 4)

    def _overview_button_rects(self):
        panel_rect = self._overview_rects()[1]
        scale = self._ui_scale()
        button_width = max(190, int(240 * scale))
        button_height = max(44, int(56 * scale))
        margin = max(18, int(24 * scale))
        y = panel_rect.bottom - button_height - margin
        return (
            pygame.Rect(panel_rect.x + margin, y, button_width, button_height),
            pygame.Rect(panel_rect.right - button_width - margin, y, button_width, button_height),
        )

    def _continue_button_rect(self):
        scale = self._ui_scale()
        button_width = max(180, int(260 * scale))
        button_height = max(48, int(60 * scale))

        if self.active_stage in self.dialogues:
            dialogue_rect = self._dialogue_rects()[2]
            margin = max(16, int(18 * scale))
            return pygame.Rect(
                dialogue_rect.right - button_width - margin,
                dialogue_rect.bottom - button_height - margin,
                button_width,
                button_height,
            )

        width, height = self.game.screen.get_size()
        return pygame.Rect(width - button_width - 60, height - button_height - 23, button_width, button_height)

    def _results_button_rect(self):
        panel_rect, _, summary_rect = self._results_layout_rects()
        scale = self._ui_scale()
        button_width = max(170, int(240 * scale))
        button_height = max(44, int(56 * scale))
        return pygame.Rect(
            summary_rect.centerx - (button_width // 2),
            panel_rect.bottom - button_height - max(18, int(24 * scale)),
            button_width,
            button_height,
        )

    def _hint_button_rect(self):
        scale = self._ui_scale()
        height = self.game.screen.get_height()
        button_width = max(150, int(180 * scale))
        button_height = max(52, int(60 * scale))
        margin_x = max(40, int(60 * scale))
        margin_bottom = max(18, int(24 * scale))
        return pygame.Rect(margin_x, height - button_height - margin_bottom, button_width, button_height)

    def _action_button_rect(self):
        scale = self._ui_scale()
        width, height = self.game.screen.get_size()
        button_width = max(190, int(240 * scale))
        button_height = max(52, int(60 * scale))
        margin_x = max(40, int(60 * scale))
        margin_bottom = max(18, int(24 * scale))
        return pygame.Rect(width - button_width - margin_x, height - button_height - margin_bottom, button_width, button_height)

    def _prep_card_rects(self):
        station_rect = self._prep_station_rect()
        scale = self._ui_scale()
        padding_x = max(18, int(24 * scale))
        header_space = max(58, int(76 * scale))
        gap_x = max(16, int(20 * scale))
        gap_y = max(14, int(18 * scale))
        card_width = (station_rect.w - padding_x * 2 - gap_x) // 2
        card_height = (station_rect.h - header_space - padding_x - gap_y) // 2
        return [
            pygame.Rect(
                station_rect.x + padding_x + (index % 2) * (card_width + gap_x),
                station_rect.y + header_space + (index // 2) * (card_height + gap_y),
                card_width,
                card_height,
            )
            for index in range(4)
        ]

    def _station_option_rects(self):
        width, height = self.game.screen.get_size()
        scale = self._ui_scale()
        gap = max(14, int(18 * scale))
        total_width = width - 120
        option_width = (total_width - gap * 2) // 3
        option_height = max(64, int(height * 0.12))
        y = max(320, int(height * 0.56))
        return {
            option: pygame.Rect(60 + index * (option_width + gap), y, option_width, option_height)
            for index, option in enumerate(self.station_options)
        }

    def _plating_pool_rects(self):
        left_rect, _ = self._plating_panel_rects()
        scale = self._ui_scale()
        padding_x = max(18, int(24 * scale))
        top = left_rect.y + max(62, int(76 * scale))
        gap = max(10, int(12 * scale))
        card_height = (left_rect.bottom - max(18, int(24 * scale)) - top - gap * 3) // 4
        return [
            pygame.Rect(left_rect.x + padding_x, top + index * (card_height + gap), left_rect.w - padding_x * 2, card_height)
            for index in range(4)
        ]

    def _plating_slot_rects(self):
        _, right_rect = self._plating_panel_rects()
        scale = self._ui_scale()
        padding_x = max(18, int(24 * scale))
        top = right_rect.y + max(62, int(76 * scale))
        bottom = right_rect.bottom - max(18, int(24 * scale))
        gap = max(10, int(12 * scale))
        card_height = (bottom - top - gap * 3) // 4
        return [
            pygame.Rect(right_rect.x + padding_x, top + index * (card_height + gap), right_rect.w - padding_x * 2, card_height)
            for index in range(4)
        ]

    def _service_option_rects(self):
        board_rect = pygame.Rect(60, 140, self.game.screen.get_width() - 120, max(250, self.game.screen.get_height() - 310))
        gap = max(14, int(18 * self._ui_scale()))
        option_width = (board_rect.w - gap * 2 - 48) // 3
        option_height = board_rect.h - max(130, int(board_rect.h * 0.28))
        y = board_rect.y + max(118, int(board_rect.h * 0.26))
        return [
            pygame.Rect(board_rect.x + 24 + index * (option_width + gap), y, option_width, option_height)
            for index in range(3)
        ]

    def _ui_scale(self):
        width, height = self.game.screen.get_size()
        return max(0.72, min(width / 1000, height / 600, 1.45))

    def _get_font(self, size, bold=False, minimum=16, name=None):
        scaled_size = max(minimum, int(size * self._ui_scale()))
        return pygame.font.SysFont(name or FONT_NAME, scaled_size, bold=bold)

    def _overview_rects(self):
        width, height = self.game.screen.get_size()
        scale = self._ui_scale()
        margin_x = max(24, int(40 * scale))
        margin_top = max(20, int(28 * scale))
        gap = max(14, int(18 * scale))
        header_height = max(92, int(118 * scale))
        header_rect = pygame.Rect(margin_x, margin_top, width - margin_x * 2, header_height)
        panel_rect = pygame.Rect(
            margin_x,
            header_rect.bottom + gap,
            width - margin_x * 2,
            height - header_rect.bottom - gap - margin_top,
        )
        return header_rect, panel_rect

    def _prep_station_rect(self):
        width, height = self.game.screen.get_size()
        scale = self._ui_scale()
        margin_x = max(36, int(60 * scale))
        top = max(138, int(150 * scale))
        bottom_space = max(126, int(150 * scale))
        return pygame.Rect(margin_x, top, width - margin_x * 2, height - top - bottom_space)

    def _plating_panel_rects(self):
        width, height = self.game.screen.get_size()
        scale = self._ui_scale()
        margin_x = max(36, int(60 * scale))
        top = max(138, int(150 * scale))
        bottom_space = max(126, int(150 * scale))
        gap = max(16, int(20 * scale))
        panel_height = height - top - bottom_space
        available_width = width - margin_x * 2
        left_width = (available_width - gap) // 2
        right_width = available_width - left_width - gap
        left_rect = pygame.Rect(margin_x, top, left_width, panel_height)
        right_rect = pygame.Rect(left_rect.right + gap, top, right_width, panel_height)
        return left_rect, right_rect

    def _dialogue_rects(self):
        width, height = self.game.screen.get_size()
        scale = self._ui_scale()
        margin = max(24, int(32 * scale))
        gap = max(14, int(18 * scale))
        title_space = max(54, int(70 * scale))
        dialogue_height = max(132, int(150 * scale))
        top_y = margin + title_space
        dialogue_rect = pygame.Rect(margin, height - dialogue_height - margin, width - margin * 2, dialogue_height)
        top_height = max(150, dialogue_rect.top - top_y - gap)
        avatar_width = max(160, min(int(240 * scale), width // 3))
        avatar_rect = pygame.Rect(margin, top_y, avatar_width, top_height)
        scene_rect = pygame.Rect(avatar_rect.right + gap, top_y, width - avatar_rect.right - gap - margin, top_height)
        return avatar_rect, scene_rect, dialogue_rect

    def _results_layout_rects(self):
        width, height = self.game.screen.get_size()
        scale = self._ui_scale()
        margin_x = max(28, int(width * 0.06))
        margin_y = max(24, int(height * 0.08))
        panel_rect = pygame.Rect(margin_x, margin_y, width - margin_x * 2, height - margin_y * 2)
        inner_x = panel_rect.x + max(20, int(24 * scale))
        content_top = panel_rect.y + max(96, int(120 * scale))
        gap = max(16, int(20 * scale))
        bottom_space = max(74, int(88 * scale))
        content_height = panel_rect.bottom - bottom_space - content_top

        if panel_rect.w >= 840:
            ratings_width = int(panel_rect.w * 0.44)
            ratings_rect = pygame.Rect(inner_x, content_top, ratings_width, content_height)
            summary_rect = pygame.Rect(ratings_rect.right + gap, content_top, panel_rect.right - ratings_rect.right - gap - max(20, int(24 * scale)), content_height)
        else:
            ratings_height = int(content_height * 0.40)
            ratings_rect = pygame.Rect(inner_x, content_top, panel_rect.w - max(40, int(48 * scale)), ratings_height)
            summary_rect = pygame.Rect(inner_x, ratings_rect.bottom + gap, ratings_rect.w, content_height - ratings_height - gap)

        return panel_rect, ratings_rect, summary_rect

    def _results_skill_card_rects(self, ratings_rect):
        gap = max(12, int(16 * self._ui_scale()))
        stacked_card_height = (ratings_rect.h - gap * 3) // 4
        minimum_card_height = max(72, int(86 * self._ui_scale()))
        minimum_grid_width = max(300, int(340 * self._ui_scale()))

        if ratings_rect.w >= 420 or (ratings_rect.w >= minimum_grid_width and stacked_card_height < minimum_card_height):
            card_width = (ratings_rect.w - gap) // 2
            card_height = (ratings_rect.h - gap) // 2
            return [
                pygame.Rect(ratings_rect.x + (index % 2) * (card_width + gap), ratings_rect.y + (index // 2) * (card_height + gap), card_width, card_height)
                for index in range(4)
            ]

        return [pygame.Rect(ratings_rect.x, ratings_rect.y + index * (stacked_card_height + gap), ratings_rect.w, stacked_card_height) for index in range(4)]

    def draw_text(self, surface, text, font, color, x, y):
        text_surface = font.render(text, True, color)
        surface.blit(text_surface, (x, y))

    def draw_wrapped_text(self, surface, text, font, color, x, y, max_width):
        words = text.split(" ")
        lines = []
        current_line = ""
        for word in words:
            test_line = f"{current_line}{word} ".strip()
            if font.size(test_line)[0] <= max_width:
                current_line = f"{current_line}{word} "
            else:
                lines.append(current_line.strip())
                current_line = f"{word} "
        if current_line:
            lines.append(current_line.strip())

        for index, line in enumerate(lines):
            text_surface = font.render(line, True, color)
            surface.blit(text_surface, (x, y + index * (font.get_height() + 8)))

        return y + len(lines) * (font.get_height() + 8)

    def draw_button(self, surface, rect, label, font=None):
        draw_button(
            surface,
            rect,
            label,
            font or self._get_font(24, minimum=17),
            (221, 233, 248),
            TEXT_COLOR,
            border_color=ACCENT_COLOR,
        )