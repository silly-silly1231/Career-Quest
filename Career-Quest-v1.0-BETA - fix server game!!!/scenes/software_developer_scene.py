import random

import pygame

from settings import BG_COLOR, TEXT_COLOR, ACCENT_COLOR, FONT_NAME
from utils.save_manager import load_save, save_data
from utils.ui import draw_panel, draw_button


class SoftwareDeveloperScene:
    def __init__(self, game):
        self.game = game
        self.title_font = pygame.font.SysFont(FONT_NAME, 42, bold=True)
        self.heading_font = pygame.font.SysFont(FONT_NAME, 30, bold=True)
        self.body_font = pygame.font.SysFont(FONT_NAME, 24)
        self.small_font = pygame.font.SysFont(FONT_NAME, 20)
        self.code_font = pygame.font.SysFont("Consolas", 22)

        self.stage_order = [
            "overview",
            "standup",
            "bug_hunt",
            "feature_dialogue",
            "logic_builder",
            "crisis_dialogue",
            "optimization",
            "emergency_dialogue",
            "pressure_debug",
            "launch_dialogue",
            "results",
        ]
        self.stage_index = 0
        self.active_stage = self.stage_order[self.stage_index]

        self.skill_scores = {
            "debugging": 0,
            "logic": 0,
            "efficiency": 0,
            "speed": 0,
        }

        self.overview_lines = [
            "Software Developers create programs, apps, and systems that power technology.",
            "They solve problems, debug errors, design features, and collaborate with teams.",
        ]
        self.key_skills = [
            "Logical thinking",
            "Problem solving",
            "Attention to detail",
            "Debugging",
            "Communication",
        ]

        self.dialogues = {
            "standup": [
                "Team Lead: Morning everyone! Our app launches tomorrow.",
                "Designer: The login page is finished.",
                "Tester: We found a few bugs last night.",
                "Team Lead: Developer, we need you to fix them before the demo.",
            ],
            "feature_dialogue": [
                "Manager: Marketing wants a new feature.",
                "Manager: They want users to be able to reset their password.",
                "Manager: Can you build it quickly?",
            ],
            "crisis_dialogue": [
                "Tester: The app is running really slow!",
                "Tester: Users say pages take forever to load.",
                "You investigate performance before the demo falls behind schedule.",
            ],
            "emergency_dialogue": [
                "Team Lead: The login system broke again!",
                "Team Lead: We only have 2 minutes before the presentation.",
                "You need to spot bugs fast and stay calm under pressure.",
            ],
            "launch_dialogue": [
                "Team Lead: The demo worked!",
                "Marketing: The app launch was successful!",
                "Tester: All major bugs are gone.",
            ],
        }

        self.dialogue_state = {
            stage: {"index": 0, "char_index": 0, "timer": 0.0, "is_typing": True}
            for stage in self.dialogues
        }
        self.typing_speed = 55

        self.bug_code_lines = [
            "def login(username, password)",
            '    if username == "" or password == "":',
            '        return "Error"',
            '    print("Logging in...")',
        ]
        self.bug_error_line = 0
        self.bug_selected_line = None
        self.bug_feedback = "Click the line that crashes the app."

        self.logic_correct_order = [
            "Ask for Email",
            "Verify User",
            "Send Email",
            "Update Password",
        ]
        self.logic_pool = self.logic_correct_order[:]
        random.shuffle(self.logic_pool)
        self.logic_slots = [None, None, None, None]
        self.logic_selected_block = None
        self.logic_feedback = "Place the steps in the correct order, then check your logic."

        self.optimization_choice = None
        self.optimization_feedback = "Choose the faster approach for large numbers of users."
        self.packet_offset = 0.0

        self.pressure_time_limit = 60.0
        self.pressure_time_left = self.pressure_time_limit
        self.pressure_rounds = [
            {"lines": ['Line 3: pritn("Hello")', 'Line 7: score += 1', 'Line 10: return score'], "bug_index": 0},
            {"lines": ['Line 2: if score = 10', 'Line 4: print(score)', 'Line 6: total += bonus'], "bug_index": 0},
            {"lines": ['Line 1: usernme = input()', 'Line 5: password = getpass()', 'Line 8: return True'], "bug_index": 0},
            {"lines": ['Line 9: for i in range(3)', 'Line 11: print(i)', 'Line 12: done = True'], "bug_index": 0},
            {"lines": ['Line 3: items.apend(task)', 'Line 6: len(items)', 'Line 7: save(items)'], "bug_index": 0},
            {"lines": ['Line 5: while ready == True:', 'Line 9: result = run()', 'Line 10: return result'], "bug_index": 0},
        ]
        self.pressure_round_index = 0
        self.pressure_hits = 0
        self.pressure_feedback = "Click the broken line before time runs out."
        self.pressure_finished = False

        self.load_background_shapes = []
        self._seed_background_shapes()

    def _seed_background_shapes(self):
        for _ in range(12):
            self.load_background_shapes.append(
                {
                    "x": random.randint(80, 860),
                    "y": random.randint(120, 460),
                    "size": random.randint(16, 36),
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
        elif self.active_stage == "bug_hunt":
            self.handle_bug_hunt_click(event.pos)
        elif self.active_stage == "logic_builder":
            self.handle_logic_click(event.pos)
        elif self.active_stage == "optimization":
            self.handle_optimization_click(event.pos)
        elif self.active_stage == "pressure_debug":
            self.handle_pressure_click(event.pos)
        elif self.active_stage == "results":
            if self._results_button_rect().collidepoint(event.pos):
                self.finish_world()

    def update(self, delta_time):
        if self.active_stage in self.dialogues:
            self.update_dialogue(delta_time)
        elif self.active_stage == "optimization":
            self.packet_offset = (self.packet_offset + delta_time * 160) % 700
        elif self.active_stage == "pressure_debug" and not self.pressure_finished:
            self.pressure_time_left = max(0.0, self.pressure_time_left - delta_time)
            if self.pressure_time_left <= 0:
                self.complete_pressure_debug()

    def render(self, screen):
        screen.fill(BG_COLOR)
        if self.active_stage == "overview":
            self.render_overview(screen)
        elif self.active_stage in self.dialogues:
            self.render_dialogue_stage(screen)
        elif self.active_stage == "bug_hunt":
            self.render_bug_hunt(screen)
        elif self.active_stage == "logic_builder":
            self.render_logic_builder(screen)
        elif self.active_stage == "optimization":
            self.render_optimization(screen)
        elif self.active_stage == "pressure_debug":
            self.render_pressure_debug(screen)
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

    def handle_bug_hunt_click(self, pos):
        line_rects = self._bug_line_rects()
        for index, rect in enumerate(line_rects):
            if rect.collidepoint(pos):
                self.bug_selected_line = index

        if self._hint_button_rect().collidepoint(pos):
            self.bug_feedback = "Hint: Python function definitions must end with a colon."
        elif self._action_button_rect().collidepoint(pos):
            if self.bug_selected_line == self.bug_error_line:
                self.skill_scores["debugging"] += 4
                self.bug_feedback = "Correct. A missing colon can stop the whole program."
                self.advance_stage()
            else:
                self.bug_feedback = "Not quite. Check the function declaration line first."

    def handle_logic_click(self, pos):
        if self._hint_button_rect().collidepoint(pos):
            self.logic_feedback = "Hint: You need the user's email before you can verify them."
            return

        if self._action_button_rect().collidepoint(pos):
            if self.logic_slots == self.logic_correct_order:
                self.skill_scores["logic"] += 5
                self.logic_feedback = "Correct. Good systems design follows a safe sequence."
                self.advance_stage()
            else:
                self.logic_feedback = "That order would break the reset flow. Try again."
            return

        for index, rect in enumerate(self._logic_pool_rects()):
            if rect.collidepoint(pos) and index < len(self.logic_pool):
                self.logic_selected_block = self.logic_pool[index]
                return

        for index, rect in enumerate(self._logic_slot_rects()):
            if not rect.collidepoint(pos):
                continue

            if self.logic_slots[index] is not None:
                self.logic_pool.append(self.logic_slots[index])
                self.logic_slots[index] = None
                return

            if self.logic_selected_block is not None:
                self.logic_slots[index] = self.logic_selected_block
                self.logic_pool.remove(self.logic_selected_block)
                self.logic_selected_block = None
                return

    def handle_optimization_click(self, pos):
        option_a_rect, option_b_rect = self._optimization_button_rects()
        if option_a_rect.collidepoint(pos):
            self.optimization_choice = "A"
            self.optimization_feedback = "Algorithm A causes a traffic jam because it searches everything for every user."
        elif option_b_rect.collidepoint(pos):
            self.optimization_choice = "B"
            self.skill_scores["efficiency"] += 4
            self.optimization_feedback = "Correct. Direct lookup scales much better and keeps the app responsive."
            self.advance_stage()

    def handle_pressure_click(self, pos):
        if self.pressure_finished:
            if self._continue_button_rect().collidepoint(pos):
                self.advance_stage()
            return

        for index, rect in enumerate(self._pressure_line_rects()):
            if not rect.collidepoint(pos):
                continue

            if index == self.current_pressure_round()["bug_index"]:
                self.pressure_hits += 1
                self.pressure_feedback = "Fixed. Keep going."
                self.pressure_round_index += 1
                if self.pressure_round_index >= len(self.pressure_rounds):
                    self.complete_pressure_debug()
            else:
                self.pressure_feedback = "Wrong line. Scan for the syntax typo first."
            return

    def complete_pressure_debug(self):
        self.pressure_finished = True
        self.skill_scores["speed"] = min(5, max(1, self.pressure_hits))
        self.skill_scores["debugging"] += min(1, self.pressure_hits // 3)
        self.pressure_feedback = "Time. Your best developers' skill is staying accurate under pressure."

    def finish_world(self):
        from scenes.main_hub_scene import MainHubScene

        save = load_save()
        completed = save.setdefault("completed_careers", [])
        if "Software Developer" not in completed:
            completed.append("Software Developer")

        skills = save.setdefault("skills", {})
        for key, value in self.skill_scores.items():
            skills[key] = max(value, skills.get(key, 0))

        reports = save.setdefault("career_reports", {})
        reports["Software Developer"] = dict(self.skill_scores)
        save_data(save)

        self.game.scene_manager.set_scene(MainHubScene(self.game))

    def return_to_hub(self):
        from scenes.main_hub_scene import MainHubScene

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

        draw_panel(screen, header_rect, (235, 244, 255), border_color=ACCENT_COLOR, border_width=3)
        draw_panel(screen, panel_rect, (252, 248, 238), border_color=ACCENT_COLOR, border_width=3)

        self.draw_text(screen, "Career World: Software Developer", title_font, TEXT_COLOR, header_rect.x + 30, header_rect.y + 22)
        self.draw_text(screen, "Career Overview", heading_font, TEXT_COLOR, header_rect.x + 30, header_rect.y + title_font.get_height() + 30)

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
        width, height = screen.get_size()
        title_font = self._get_font(42, bold=True, minimum=28)
        heading_font = self._get_font(30, bold=True, minimum=22)
        body_font = self._get_font(24, minimum=17)
        avatar_rect, scene_rect, dialogue_rect = self._dialogue_rects()

        self.draw_text(screen, "Software Developer Workday", title_font, TEXT_COLOR, avatar_rect.x, max(18, avatar_rect.y - title_font.get_height() - 16))

        draw_panel(screen, avatar_rect, (214, 226, 240), border_color=ACCENT_COLOR, border_width=3)
        draw_panel(screen, scene_rect, (245, 239, 228), border_color=ACCENT_COLOR, border_width=3)
        draw_panel(screen, dialogue_rect, (255, 252, 245), border_color=ACCENT_COLOR, border_width=3)

        self.draw_text(screen, self.stage_label(), heading_font, TEXT_COLOR, scene_rect.x + 20, scene_rect.y + 20)
        self.draw_wrapped_text(
            screen,
            "You listen, prioritize, and translate pressure into focused work.",
            body_font,
            TEXT_COLOR,
            scene_rect.x + 20,
            scene_rect.y + 20 + heading_font.get_height() + 14,
            scene_rect.w - 40,
        )

        state = self.dialogue_state[self.active_stage]
        line = self.dialogues[self.active_stage][state["index"]]
        visible = line[: state["char_index"]]
        button_rect = self._continue_button_rect()
        dialogue_text_width = max(180, dialogue_rect.w - 40 - button_rect.w - 20)
        self.draw_wrapped_text(screen, visible, body_font, TEXT_COLOR, dialogue_rect.x + 20, dialogue_rect.y + 20, dialogue_text_width)

        self.draw_button(
            screen,
            button_rect,
            "Next" if state["index"] < len(self.dialogues[self.active_stage]) - 1 else "Continue",
            font=body_font,
        )

    def render_bug_hunt(self, screen):
        width, height = screen.get_width(), screen.get_height()
        self.draw_text(screen, "Skill Game 1: Bug Hunt", self.title_font, TEXT_COLOR, 60, 40)
        self.draw_text(screen, 'Tester report: "The login button crashes the app."', self.body_font, TEXT_COLOR, 60, 95)

        editor_rect = pygame.Rect(60, 140, width - 120, 270)
        draw_panel(screen, editor_rect, (250, 250, 248), border_color=ACCENT_COLOR, border_width=3)
        self.draw_text(screen, "Code Editor", self.heading_font, TEXT_COLOR, 85, 160)

        for index, rect in enumerate(self._bug_line_rects()):
            fill = (255, 231, 212) if self.bug_selected_line == index else (238, 243, 248)
            draw_panel(screen, rect, fill, border_color=ACCENT_COLOR, border_width=1, radius=10, shadow=False)
            self.draw_text(screen, self.bug_code_lines[index], self.code_font, TEXT_COLOR, rect.x + 14, rect.y + 10)

        self.draw_wrapped_text(screen, self.bug_feedback, self.body_font, TEXT_COLOR, 60, 435, width - 120)
        self.draw_button(screen, self._hint_button_rect(), "Hint")
        self.draw_button(screen, self._action_button_rect(), "Fix Bug")

    def render_logic_builder(self, screen):
        width, height = screen.get_width(), screen.get_height()
        self.draw_text(screen, "Skill Game 2: Logic Builder", self.title_font, TEXT_COLOR, 60, 40)
        self.draw_wrapped_text(
            screen,
            "Arrange the password reset steps in the safest order.",
            self.body_font,
            TEXT_COLOR,
            60,
            95,
            width - 120,
        )

        left_rect = pygame.Rect(60, 140, width // 2 - 80, 300)
        right_rect = pygame.Rect(width // 2 + 20, 140, width // 2 - 80, 300)
        draw_panel(screen, left_rect, (245, 241, 232), border_color=ACCENT_COLOR, border_width=3)
        draw_panel(screen, right_rect, (236, 244, 252), border_color=ACCENT_COLOR, border_width=3)

        self.draw_text(screen, "Code Blocks", self.heading_font, TEXT_COLOR, 85, 160)
        self.draw_text(screen, "Sequence Slots", self.heading_font, TEXT_COLOR, width // 2 + 45, 160)

        for index, rect in enumerate(self._logic_pool_rects()):
            fill = (255, 223, 196) if index < len(self.logic_pool) and self.logic_pool[index] == self.logic_selected_block else (255, 251, 245)
            draw_panel(screen, rect, fill, border_color=ACCENT_COLOR, border_width=2, radius=10, shadow=False)
            if index < len(self.logic_pool):
                self.draw_text(screen, self.logic_pool[index], self.body_font, TEXT_COLOR, rect.x + 12, rect.y + 14)

        for index, rect in enumerate(self._logic_slot_rects()):
            draw_panel(screen, rect, (255, 255, 255), border_color=ACCENT_COLOR, border_width=2, radius=10, shadow=False)
            label = self.logic_slots[index] if self.logic_slots[index] else f"[{index + 1}]"
            self.draw_text(screen, label, self.body_font, TEXT_COLOR, rect.x + 12, rect.y + 14)

        self.draw_wrapped_text(screen, self.logic_feedback, self.body_font, TEXT_COLOR, 60, 460, width - 120)
        self.draw_button(screen, self._hint_button_rect(), "Hint")
        self.draw_button(screen, self._action_button_rect(), "Check Order")

    def render_optimization(self, screen):
        width, height = screen.get_width(), screen.get_height()
        title_font = self._get_font(42, bold=True, minimum=28)
        heading_font = self._get_font(30, bold=True, minimum=22)
        body_font = self._get_font(24, minimum=17)
        small_font = self._get_font(20, minimum=15)
        scale = self._ui_scale()
        margin_x = max(32, int(48 * scale))
        top_y = max(28, int(38 * scale))

        self.draw_text(screen, "Skill Game 3: Optimization Puzzle", title_font, TEXT_COLOR, margin_x, top_y)

        intro_rect, option_a_info_rect, option_b_info_rect, feedback_rect = self._optimization_text_rects()
        draw_panel(screen, intro_rect, (252, 247, 238), border_color=ACCENT_COLOR, border_width=2, radius=16)
        self.draw_wrapped_text(
            screen,
            "Choose the faster algorithm for the login system.",
            body_font,
            TEXT_COLOR,
            intro_rect.x + 18,
            intro_rect.y + 14,
            intro_rect.w - 36,
        )

        sim_rect = pygame.Rect(60, 140, width - 120, 240)
        draw_panel(screen, sim_rect, (241, 247, 255), border_color=ACCENT_COLOR, border_width=3)
        self.draw_text(screen, "Server Simulation", heading_font, TEXT_COLOR, 85, 160)

        good_flow = self.optimization_choice == "B"
        speed = 2.5 if good_flow else 0.8
        lane_y = 240
        for index in range(8):
            x = 110 + ((self.packet_offset * speed) + index * 85) % (width - 220)
            y = lane_y + ((index % 2) * 42)
            pygame.draw.circle(screen, (78, 167, 120) if good_flow else (193, 102, 82), (int(x), y), 13)

        if not good_flow:
            for shape in self.load_background_shapes[:5]:
                pygame.draw.circle(screen, (218, 184, 145), (shape["x"], shape["y"]), shape["size"] // 3)

        option_a_rect, option_b_rect = self._optimization_button_rects()
        self.draw_button(screen, option_a_rect, "Algorithm A")
        self.draw_button(screen, option_b_rect, "Algorithm B")

        draw_panel(screen, option_a_info_rect, (255, 251, 245), border_color=ACCENT_COLOR, border_width=2, radius=14, shadow=False)
        draw_panel(screen, option_b_info_rect, (245, 250, 255), border_color=ACCENT_COLOR, border_width=2, radius=14, shadow=False)
        self.draw_wrapped_text(
            screen,
            "Option A: for each user, search entire database",
            small_font,
            TEXT_COLOR,
            option_a_info_rect.x + 14,
            option_a_info_rect.y + 12,
            option_a_info_rect.w - 28,
        )
        self.draw_wrapped_text(
            screen,
            "Option B: use user ID lookup",
            small_font,
            TEXT_COLOR,
            option_b_info_rect.x + 14,
            option_b_info_rect.y + 12,
            option_b_info_rect.w - 28,
        )

        draw_panel(screen, feedback_rect, (252, 247, 238), border_color=ACCENT_COLOR, border_width=2, radius=16)
        self.draw_wrapped_text(
            screen,
            self.optimization_feedback,
            body_font,
            TEXT_COLOR,
            feedback_rect.x + 18,
            feedback_rect.y + 14,
            feedback_rect.w - 36,
        )

    def render_pressure_debug(self, screen):
        width, height = screen.get_width(), screen.get_height()
        self.draw_text(screen, "Skill Game 4: Debugging Under Pressure", self.title_font, TEXT_COLOR, 60, 40)
        self.draw_text(screen, f"Timer: {int(self.pressure_time_left):02d} seconds", self.heading_font, TEXT_COLOR, 60, 95)

        code_rect = pygame.Rect(60, 140, width - 120, 260)
        draw_panel(screen, code_rect, (251, 248, 241), border_color=ACCENT_COLOR, border_width=3)
        self.draw_text(screen, "Code Window", self.heading_font, TEXT_COLOR, 85, 160)

        if self.pressure_finished:
            self.draw_wrapped_text(
                screen,
                f"You fixed {self.pressure_hits} bugs before time ran out. {self.pressure_feedback}",
                self.body_font,
                TEXT_COLOR,
                85,
                220,
                width - 170,
            )
            self.draw_button(screen, self._continue_button_rect(), "Continue")
            return

        for index, rect in enumerate(self._pressure_line_rects()):
            pygame.draw.rect(screen, (239, 243, 248), rect, border_radius=10)
            pygame.draw.rect(screen, TEXT_COLOR, rect, 1, border_radius=10)
            self.draw_text(screen, self.current_pressure_round()["lines"][index], self.code_font, TEXT_COLOR, rect.x + 14, rect.y + 10)

        self.draw_wrapped_text(screen, self.pressure_feedback, self.body_font, TEXT_COLOR, 60, 430, width - 120)
        self.draw_text(screen, f"Bugs fixed: {self.pressure_hits}", self.body_font, TEXT_COLOR, 60, 505)

    def render_results(self, screen):
        width, height = screen.get_width(), screen.get_height()
        panel_rect = pygame.Rect(80, 70, width - 160, height - 140)
        draw_panel(screen, panel_rect, (252, 247, 238), border_color=ACCENT_COLOR, border_width=3, radius=22)

        self.draw_text(screen, "Software Developer Report", self.title_font, TEXT_COLOR, 120, 105)
        ratings = [
            ("Debugging", self.skill_scores["debugging"]),
            ("Logic", self.skill_scores["logic"]),
            ("Efficiency", self.skill_scores["efficiency"]),
            ("Speed", self.skill_scores["speed"]),
        ]
        y = 185
        for label, value in ratings:
            stars = "⭐" * max(1, min(5, value))
            self.draw_text(screen, f"{label}: {stars}", self.heading_font, TEXT_COLOR, 130, y)
            y += 56

        self.draw_wrapped_text(
            screen,
            "Software developers solve problems using logic and creativity. They write code, fix bugs, design features, and work with teams to build technology.",
            self.body_font,
            TEXT_COLOR,
            130,
            y + 10,
            width - 260,
        )
        self.draw_button(screen, self._results_button_rect(), "Return to Hub")

    def current_pressure_round(self):
        return self.pressure_rounds[min(self.pressure_round_index, len(self.pressure_rounds) - 1)]

    def stage_label(self):
        labels = {
            "standup": "Morning Standup Meeting",
            "feature_dialogue": "Midday Feature Request",
            "crisis_dialogue": "Afternoon Crisis",
            "emergency_dialogue": "Pre-Launch Emergency",
            "launch_dialogue": "Launch Success",
        }
        return labels.get(self.active_stage, "Software Developer")

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
        width, height = self.game.screen.get_size()
        panel_rect = pygame.Rect(80, 70, width - 160, height - 140)
        scale = self._ui_scale()
        button_width = max(170, int(240 * scale))
        button_height = max(44, int(56 * scale))
        bottom_margin = max(20, int(28 * scale))
        return pygame.Rect(
            panel_rect.centerx - (button_width // 2),
            panel_rect.bottom - button_height - bottom_margin,
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

    def _bug_line_rects(self):
        width = self.game.screen.get_width()
        return [pygame.Rect(90, 205 + index * 46, width - 180, 38) for index in range(len(self.bug_code_lines))]

    def _logic_pool_rects(self):
        width = self.game.screen.get_width()
        panel_width = max(260, (width // 2) - 120)
        return [pygame.Rect(90, 215 + index * 58, panel_width, 46) for index in range(4)]

    def _logic_slot_rects(self):
        width = self.game.screen.get_width()
        panel_width = max(260, (width // 2) - 120)
        x = width - panel_width - 85
        return [pygame.Rect(x, 215 + index * 58, panel_width, 46) for index in range(4)]

    def _optimization_button_rects(self):
        scale = self._ui_scale()
        width = self.game.screen.get_width()
        button_width = max(170, int(210 * scale))
        button_height = max(52, int(60 * scale))
        gap = max(16, int(20 * scale))
        y = max(405, int(405 * scale))
        total_width = (button_width * 2) + gap
        start_x = width - total_width - max(32, int(40 * scale))
        return (
            pygame.Rect(start_x, y, button_width, button_height),
            pygame.Rect(start_x + button_width + gap, y, button_width, button_height),
        )

    def _optimization_text_rects(self):
        width, height = self.game.screen.get_size()
        scale = self._ui_scale()
        margin_x = max(32, int(48 * scale))
        intro_top = max(82, int(96 * scale))
        intro_height = max(52, int(66 * scale))
        intro_rect = pygame.Rect(margin_x, intro_top, width - margin_x * 2, intro_height)

        option_a_rect, option_b_rect = self._optimization_button_rects()
        info_gap = max(10, int(12 * scale))
        info_height = max(56, int(74 * scale))
        option_a_info_rect = pygame.Rect(option_a_rect.x, option_a_rect.bottom + info_gap, option_a_rect.w, info_height)
        option_b_info_rect = pygame.Rect(option_b_rect.x, option_b_rect.bottom + info_gap, option_b_rect.w, info_height)

        feedback_top = max(option_a_info_rect.bottom, option_b_info_rect.bottom) + max(14, int(18 * scale))
        feedback_height = max(64, height - feedback_top - max(18, int(24 * scale)))
        feedback_rect = pygame.Rect(margin_x, feedback_top, width - margin_x * 2, feedback_height)
        return intro_rect, option_a_info_rect, option_b_info_rect, feedback_rect

    def _pressure_line_rects(self):
        width = self.game.screen.get_width()
        return [pygame.Rect(90, 215 + index * 56, width - 180, 42) for index in range(3)]

    def _ui_scale(self):
        width, height = self.game.screen.get_size()
        return max(0.72, min(width / 1000, height / 600))

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
        # Use shared helper for consistent buttons with subtle shadows
        draw_button(
            surface,
            rect,
            label,
            font or self._get_font(24, minimum=17),
            (221, 233, 248),
            TEXT_COLOR,
            border_color=ACCENT_COLOR,
        )