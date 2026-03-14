import os
import random

import pygame

from source.config.settings import ACCENT_COLOR, BG_COLOR, FONT_NAME, TEXT_COLOR
from source.utils.save_manager import load_save, save_data
from source.utils.ui import draw_button, draw_panel


ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")


class DoctorScene:
    def __init__(self, game):
        self.game = game

        self.stage_order = [
            "overview",
            "intake_dialogue",
            "triage_board",
            "consult_dialogue",
            "diagnosis_rounds",
            "rounds_dialogue",
            "care_plan",
            "emergency_dialogue",
            "bedside_manner",
            "closing_dialogue",
            "results",
        ]
        self.stage_index = 0
        self.active_stage = self.stage_order[self.stage_index]

        self.skill_scores = {
            "triage": 0,
            "diagnosis": 0,
            "accuracy": 0,
            "empathy": 0,
        }

        self.overview_lines = [
            "Doctors assess symptoms, prioritize urgent cases, diagnose conditions, and create safe treatment plans.",
            "They combine science, communication, and calm decision-making to help patients through a full day of care.",
        ]
        self.key_skills = [
            "Triage",
            "Diagnosis",
            "Accuracy",
            "Empathy",
            "Communication",
        ]

        self.dialogues = {
            "intake_dialogue": [
                "Charge Nurse: The waiting room is full, so we need smart triage right away.",
                "Charge Nurse: Sort the most urgent patients first so the team can move fast without missing risk.",
                "Doctor: Stay calm, gather the facts, and act in the right order.",
            ],
            "consult_dialogue": [
                "Nurse: Your next patients are ready for consultation.",
                "Doctor: Match symptoms carefully before you lock in a diagnosis.",
                "Doctor: One rushed guess can send care in the wrong direction.",
            ],
            "rounds_dialogue": [
                "Resident: We have to update plans before afternoon rounds.",
                "Doctor: Good treatment is not just knowing the illness. It is choosing the right sequence of care.",
                "Doctor: Build each plan safely and clearly.",
            ],
            "emergency_dialogue": [
                "Family Member: My dad is scared and keeps asking what happens next.",
                "Doctor: Patients remember your tone as much as your instructions.",
                "Doctor: In a long shift, empathy keeps care human.",
            ],
            "closing_dialogue": [
                "Charge Nurse: The department is stable and your charts are complete.",
                "Resident: Your decisions kept care moving and patients informed.",
                "Doctor: That is what a full workday looks like in medicine.",
            ],
        }
        self.dialogue_state = {
            stage: {"index": 0, "char_index": 0, "timer": 0.0, "is_typing": True}
            for stage in self.dialogues
        }
        self.typing_speed = 55

        self.triage_cases = [
            {"label": "Chest pain and shortness of breath", "priority": 1},
            {"label": "High fever and dehydration", "priority": 2},
            {"label": "Sprained wrist after a fall", "priority": 4},
            {"label": "Deep cut with steady bleeding", "priority": 3},
        ]
        self.triage_cards = self.triage_cases[:]
        random.shuffle(self.triage_cards)
        self.triage_completed = []
        self.triage_feedback = "Click each patient in the order they should be seen first."

        self.diagnosis_rounds = [
            {
                "patient": "Patient A",
                "symptoms": "Frequent thirst, blurry vision, and unusual fatigue.",
                "options": ["Asthma", "Diabetes", "Broken bone"],
                "correct": 1,
                "reason": "Correct. Those symptoms point toward diabetes and need follow-up testing.",
            },
            {
                "patient": "Patient B",
                "symptoms": "Fever, sore throat, and swollen glands after several days of feeling worse.",
                "options": ["Strep throat", "Sunburn", "Migraine"],
                "correct": 0,
                "reason": "Correct. That symptom cluster fits strep throat best.",
            },
            {
                "patient": "Patient C",
                "symptoms": "Wheezing, chest tightness, and coughing after running outside.",
                "options": ["Asthma flare", "Food poisoning", "Ear infection"],
                "correct": 0,
                "reason": "Correct. Those symptoms fit an asthma flare.",
            },
        ]
        self.diagnosis_round_index = 0
        self.diagnosis_feedback = "Review the symptoms and choose the best diagnosis."

        self.care_plan_order = [
            "Check vital signs",
            "Order tests",
            "Review results",
            "Explain treatment",
        ]
        self.care_plan_pool = self.care_plan_order[:]
        random.shuffle(self.care_plan_pool)
        self.care_plan_slots = [None, None, None, None]
        self.care_plan_selected_item = None
        self.care_plan_feedback = "Build the care plan in the safest order, then confirm it."

        self.bedside_time_limit = 40.0
        self.bedside_time_left = self.bedside_time_limit
        self.bedside_rounds = [
            {
                "prompt": "A patient says, 'I am nervous about the test results.'",
                "options": [
                    "You should calm down and wait.",
                    "I understand. I will explain what we know and what happens next.",
                    "Ask the nurse later.",
                ],
                "correct": 1,
            },
            {
                "prompt": "A parent asks why their child needs another check.",
                "options": [
                    "Because that is the rule.",
                    "I want to make sure we are not missing anything serious.",
                    "It is probably nothing.",
                ],
                "correct": 1,
            },
            {
                "prompt": "An older patient says they did not understand the medication instructions.",
                "options": [
                    "Read the paper again.",
                    "I can go over it with you step by step right now.",
                    "Someone else already explained it.",
                ],
                "correct": 1,
            },
            {
                "prompt": "A patient looks frightened before a procedure.",
                "options": [
                    "We do this all the time.",
                    "There is nothing to worry about.",
                    "It is normal to feel worried. I will tell you what to expect.",
                ],
                "correct": 2,
            },
        ]
        self.bedside_round_index = 0
        self.bedside_hits = 0
        self.bedside_feedback = "Choose the response that keeps the patient informed and respected."
        self.bedside_finished = False

        self._star_icon_source = None
        self._star_icon_cache = {}

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
        elif self.active_stage == "triage_board":
            self.handle_triage_click(event.pos)
        elif self.active_stage == "diagnosis_rounds":
            self.handle_diagnosis_click(event.pos)
        elif self.active_stage == "care_plan":
            self.handle_care_plan_click(event.pos)
        elif self.active_stage == "bedside_manner":
            self.handle_bedside_click(event.pos)
        elif self.active_stage == "results":
            if self._results_button_rect().collidepoint(event.pos):
                self.finish_world()

    def update(self, delta_time):
        if self.active_stage in self.dialogues:
            self.update_dialogue(delta_time)
        elif self.active_stage == "bedside_manner" and not self.bedside_finished:
            self.bedside_time_left = max(0.0, self.bedside_time_left - delta_time)
            if self.bedside_time_left <= 0:
                self.complete_bedside_rounds()

    def render(self, screen):
        screen.fill(BG_COLOR)
        if self.active_stage == "overview":
            self.render_overview(screen)
        elif self.active_stage in self.dialogues:
            self.render_dialogue_stage(screen)
        elif self.active_stage == "triage_board":
            self.render_triage_board(screen)
        elif self.active_stage == "diagnosis_rounds":
            self.render_diagnosis_rounds(screen)
        elif self.active_stage == "care_plan":
            self.render_care_plan(screen)
        elif self.active_stage == "bedside_manner":
            self.render_bedside_manner(screen)
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

    def handle_triage_click(self, pos):
        if self._hint_button_rect().collidepoint(pos):
            self.triage_feedback = "Hint: Chest pain with trouble breathing comes before pain that is stable and controlled."
            return

        if self._action_button_rect().collidepoint(pos):
            self.triage_completed = []
            self.triage_feedback = "Board reset. Start with the most urgent patient."
            return

        next_priority = len(self.triage_completed) + 1
        for index, rect in enumerate(self._triage_card_rects()):
            if not rect.collidepoint(pos):
                continue

            case = self.triage_cards[index]
            if case["label"] in self.triage_completed:
                return

            if case["priority"] == next_priority:
                self.triage_completed.append(case["label"])
                if len(self.triage_completed) == len(self.triage_cards):
                    self.skill_scores["triage"] = 4
                    self.triage_feedback = "Correct. Smart triage protects the sickest patients first."
                    self.advance_stage()
                else:
                    self.triage_feedback = f"Good call. {len(self.triage_completed)} cases sorted."
            else:
                self.triage_feedback = "That patient can wait longer than someone else on the board."
            return

    def handle_diagnosis_click(self, pos):
        for index, rect in enumerate(self._diagnosis_option_rects()):
            if not rect.collidepoint(pos):
                continue

            current_round = self.current_diagnosis_round()
            if index == current_round["correct"]:
                self.skill_scores["diagnosis"] = min(5, self.skill_scores["diagnosis"] + 2)
                self.diagnosis_feedback = current_round["reason"]
                self.diagnosis_round_index += 1
                if self.diagnosis_round_index >= len(self.diagnosis_rounds):
                    self.skill_scores["accuracy"] = max(self.skill_scores["accuracy"], 4)
                    self.advance_stage()
            else:
                self.diagnosis_feedback = "Not quite. Re-check the symptom pattern before you decide."
            return

    def handle_care_plan_click(self, pos):
        if self._hint_button_rect().collidepoint(pos):
            self.care_plan_feedback = "Hint: gather patient status first, then test, then interpret, then explain the plan."
            return

        if self._action_button_rect().collidepoint(pos):
            if self.care_plan_slots == self.care_plan_order:
                self.skill_scores["accuracy"] = 5
                self.care_plan_feedback = "Correct. Safe care follows a clear sequence."
                self.advance_stage()
            else:
                self.care_plan_feedback = "That order risks acting before you have enough information."
            return

        for index, rect in enumerate(self._care_plan_pool_rects()):
            if rect.collidepoint(pos) and index < len(self.care_plan_pool):
                self.care_plan_selected_item = self.care_plan_pool[index]
                return

        for index, rect in enumerate(self._care_plan_slot_rects()):
            if not rect.collidepoint(pos):
                continue

            if self.care_plan_slots[index] is not None:
                self.care_plan_pool.append(self.care_plan_slots[index])
                self.care_plan_slots[index] = None
                return

            if self.care_plan_selected_item is not None:
                self.care_plan_slots[index] = self.care_plan_selected_item
                self.care_plan_pool.remove(self.care_plan_selected_item)
                self.care_plan_selected_item = None
                return

    def handle_bedside_click(self, pos):
        if self.bedside_finished:
            if self._continue_button_rect().collidepoint(pos):
                self.advance_stage()
            return

        for index, rect in enumerate(self._bedside_option_rects()):
            if not rect.collidepoint(pos):
                continue

            current_round = self.current_bedside_round()
            if index == current_round["correct"]:
                self.bedside_hits += 1
                self.bedside_feedback = "Good response. Patients need clarity and reassurance."
                self.bedside_round_index += 1
                if self.bedside_round_index >= len(self.bedside_rounds):
                    self.complete_bedside_rounds()
            else:
                self.bedside_feedback = "Try again. The strongest answer should acknowledge the patient's concern and explain the next step."
            return

    def complete_bedside_rounds(self):
        self.bedside_finished = True
        self.skill_scores["empathy"] = min(5, max(1, self.bedside_hits))
        self.bedside_feedback = "Shift complete. Bedside manner is part of treatment, not an extra."

    def finish_world(self):
        from source.scenes.main_hub_scene import MainHubScene

        save = load_save()
        completed = save.setdefault("completed_careers", [])
        if "Doctor" not in completed:
            completed.append("Doctor")

        skills = save.setdefault("skills", {})
        for key, value in self.skill_scores.items():
            skills[key] = max(value, skills.get(key, 0))

        reports = save.setdefault("career_reports", {})
        reports["Doctor"] = dict(self.skill_scores)
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

        draw_panel(screen, header_rect, (235, 250, 241), border_color=ACCENT_COLOR, border_width=3)
        draw_panel(screen, panel_rect, (252, 248, 238), border_color=ACCENT_COLOR, border_width=3)

        self.draw_text(screen, "Career World: Doctor", title_font, TEXT_COLOR, header_rect.x + 30, header_rect.y + 22)
        self.draw_text(screen, "Hospital Overview", heading_font, TEXT_COLOR, header_rect.x + 30, header_rect.y + title_font.get_height() + 30)

        y = main_y
        self.draw_text(screen, "What You Do", heading_font, TEXT_COLOR, main_x, y)
        y += heading_font.get_height() + max(10, int(14 * scale))
        for line in self.overview_lines:
            y = self.draw_wrapped_text(screen, line, body_font, TEXT_COLOR, main_x, y, main_width) + max(10, int(14 * scale))

        self.draw_text(screen, "Key Skills", heading_font, TEXT_COLOR, sidebar_x, sidebar_y)
        y = sidebar_y + heading_font.get_height() + max(12, int(14 * scale))
        for skill in self.key_skills:
            y = self.draw_wrapped_text(screen, f"- {skill}", body_font, TEXT_COLOR, sidebar_x + 12, y, sidebar_width - 20) + max(4, int(6 * scale))

        self.draw_button(screen, back_button_rect, "Back", font=body_font)
        self.draw_button(screen, start_button_rect, "Start Workday", font=body_font)

    def render_dialogue_stage(self, screen):
        title_font = self._get_font(42, bold=True, minimum=28)
        heading_font = self._get_font(30, bold=True, minimum=22)
        body_font = self._get_font(24, minimum=17)
        small_font = self._get_font(20, minimum=15)
        avatar_rect, scene_rect, dialogue_rect = self._dialogue_rects()

        self.draw_text(screen, "Doctor Workday", title_font, TEXT_COLOR, avatar_rect.x, max(18, avatar_rect.y - title_font.get_height() - 16))

        draw_panel(screen, avatar_rect, (227, 238, 230), border_color=ACCENT_COLOR, border_width=3)
        draw_panel(screen, scene_rect, (243, 248, 242), border_color=ACCENT_COLOR, border_width=3)
        draw_panel(screen, dialogue_rect, (255, 252, 246), border_color=ACCENT_COLOR, border_width=3)

        self._draw_doctor_avatar(screen, avatar_rect)
        self.draw_text(screen, self.stage_label(), heading_font, TEXT_COLOR, scene_rect.x + 20, scene_rect.y + 20)
        self.draw_wrapped_text(
            screen,
            "You balance urgency, evidence, and communication while the unit keeps moving.",
            body_font,
            TEXT_COLOR,
            scene_rect.x + 20,
            scene_rect.y + 20 + heading_font.get_height() + 14,
            scene_rect.w - 40,
        )
        chart_rect = pygame.Rect(scene_rect.x + 24, scene_rect.bottom - 82, scene_rect.w - 48, 46)
        draw_panel(screen, chart_rect, (250, 250, 247), border_color=ACCENT_COLOR, border_width=2, radius=12, shadow=False)
        self.draw_text(screen, "Patient charts updated", small_font, TEXT_COLOR, chart_rect.x + 16, chart_rect.y + 12)

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

    def render_triage_board(self, screen):
        width, height = screen.get_size()
        title_font = self._get_font(42, bold=True, minimum=28)
        body_font = self._get_font(24, minimum=17)
        heading_font = self._get_font(30, bold=True, minimum=22)
        scale = self._ui_scale()
        board_rect = self._triage_board_rect()
        feedback_y = board_rect.bottom + max(14, int(18 * scale))

        self.draw_text(screen, "Skill Game 1: Triage Board", title_font, TEXT_COLOR, 60, 40)
        self.draw_wrapped_text(
            screen,
            "Prioritize the waiting room from most urgent to least urgent care need.",
            body_font,
            TEXT_COLOR,
            60,
            95,
            width - 120,
        )

        draw_panel(screen, board_rect, (245, 250, 244), border_color=ACCENT_COLOR, border_width=3)
        self.draw_text(screen, "Emergency Intake", heading_font, TEXT_COLOR, board_rect.x + 24, board_rect.y + 20)

        for index, rect in enumerate(self._triage_card_rects()):
            case = self.triage_cards[index]
            is_done = case["label"] in self.triage_completed
            fill = (216, 237, 215) if is_done else (255, 251, 245)
            draw_panel(screen, rect, fill, border_color=ACCENT_COLOR, border_width=2, radius=14, shadow=False)
            self.draw_wrapped_text(screen, case["label"], body_font, TEXT_COLOR, rect.x + 14, rect.y + 18, rect.w - 28)
            if is_done:
                order_label = str(self.triage_completed.index(case["label"]) + 1)
                self.draw_text(screen, f"Seen #{order_label}", body_font, TEXT_COLOR, rect.right - 120, rect.bottom - 38)

        self.draw_wrapped_text(screen, self.triage_feedback, body_font, TEXT_COLOR, 60, feedback_y, width - 120)
        self.draw_button(screen, self._hint_button_rect(), "Hint")
        self.draw_button(screen, self._action_button_rect(), "Reset Board")

    def render_diagnosis_rounds(self, screen):
        width, height = screen.get_size()
        title_font = self._get_font(42, bold=True, minimum=28)
        body_font = self._get_font(24, minimum=17)
        heading_font = self._get_font(30, bold=True, minimum=22)
        small_font = self._get_font(20, minimum=15)
        current_round = self.current_diagnosis_round()

        self.draw_text(screen, "Skill Game 2: Diagnosis Match", title_font, TEXT_COLOR, 60, 40)

        chart_rect = pygame.Rect(60, 130, width - 120, max(150, int(height * 0.26)))
        draw_panel(screen, chart_rect, (255, 249, 239), border_color=ACCENT_COLOR, border_width=3)
        self.draw_text(screen, current_round["patient"], heading_font, TEXT_COLOR, chart_rect.x + 22, chart_rect.y + 18)
        self.draw_wrapped_text(
            screen,
            current_round["symptoms"],
            body_font,
            TEXT_COLOR,
            chart_rect.x + 22,
            chart_rect.y + 18 + heading_font.get_height() + 16,
            chart_rect.w - 220,
        )

        badge_rect = pygame.Rect(chart_rect.right - 156, chart_rect.y + 22, 128, 42)
        draw_panel(screen, badge_rect, (235, 244, 255), border_color=ACCENT_COLOR, border_width=2, radius=12, shadow=False)
        self.draw_text(screen, "Consult", small_font, TEXT_COLOR, badge_rect.x + 28, badge_rect.y + 10)

        for index, rect in enumerate(self._diagnosis_option_rects()):
            draw_panel(screen, rect, (239, 243, 248), border_color=ACCENT_COLOR, border_width=2)
            self.draw_text(screen, current_round["options"][index], body_font, TEXT_COLOR, rect.x + 18, rect.y + (rect.h - body_font.get_height()) // 2)

        progress_text = f"Case {min(self.diagnosis_round_index + 1, len(self.diagnosis_rounds))} of {len(self.diagnosis_rounds)}"
        self.draw_text(screen, progress_text, small_font, TEXT_COLOR, 60, height - 160)
        self.draw_wrapped_text(screen, self.diagnosis_feedback, body_font, TEXT_COLOR, 60, height - 125, width - 120)

    def render_care_plan(self, screen):
        width, height = screen.get_size()
        title_font = self._get_font(42, bold=True, minimum=28)
        body_font = self._get_font(24, minimum=17)
        heading_font = self._get_font(30, bold=True, minimum=22)
        scale = self._ui_scale()
        left_rect, right_rect = self._care_plan_panel_rects()
        feedback_y = max(left_rect.bottom, right_rect.bottom) + max(14, int(18 * scale))

        self.draw_text(screen, "Skill Game 3: Care Plan", title_font, TEXT_COLOR, 60, 40)
        self.draw_wrapped_text(
            screen,
            "Arrange the doctor workflow so information is gathered, reviewed, and explained in a safe sequence.",
            body_font,
            TEXT_COLOR,
            60,
            95,
            width - 120,
        )

        draw_panel(screen, left_rect, (248, 241, 232), border_color=ACCENT_COLOR, border_width=3)
        draw_panel(screen, right_rect, (243, 247, 252), border_color=ACCENT_COLOR, border_width=3)

        self.draw_text(screen, "Actions", heading_font, TEXT_COLOR, left_rect.x + 24, left_rect.y + 18)
        self.draw_text(screen, "Care Sequence", heading_font, TEXT_COLOR, right_rect.x + 24, right_rect.y + 18)

        for index, rect in enumerate(self._care_plan_pool_rects()):
            fill = (255, 226, 203) if index < len(self.care_plan_pool) and self.care_plan_pool[index] == self.care_plan_selected_item else (255, 251, 245)
            draw_panel(screen, rect, fill, border_color=ACCENT_COLOR, border_width=2, radius=12, shadow=False)
            if index < len(self.care_plan_pool):
                self.draw_wrapped_text(screen, self.care_plan_pool[index], body_font, TEXT_COLOR, rect.x + 12, rect.y + 12, rect.w - 24)

        for index, rect in enumerate(self._care_plan_slot_rects()):
            draw_panel(screen, rect, (255, 255, 255), border_color=ACCENT_COLOR, border_width=2, radius=12, shadow=False)
            label = self.care_plan_slots[index] if self.care_plan_slots[index] else f"Step {index + 1}"
            self.draw_wrapped_text(screen, label, body_font, TEXT_COLOR, rect.x + 12, rect.y + 10, rect.w - 24)

        self.draw_wrapped_text(screen, self.care_plan_feedback, body_font, TEXT_COLOR, 60, feedback_y, width - 120)
        self.draw_button(screen, self._hint_button_rect(), "Hint")
        self.draw_button(screen, self._action_button_rect(), "Check Plan")

    def render_bedside_manner(self, screen):
        width, height = screen.get_size()
        title_font = self._get_font(42, bold=True, minimum=28)
        body_font = self._get_font(24, minimum=17)
        heading_font = self._get_font(30, bold=True, minimum=22)
        small_font = self._get_font(20, minimum=15)

        self.draw_text(screen, "Skill Game 4: Bedside Manner", title_font, TEXT_COLOR, 60, 40)
        self.draw_text(screen, f"Time Left: {int(self.bedside_time_left):02d} seconds", heading_font, TEXT_COLOR, 60, 95)

        board_rect = pygame.Rect(60, 140, width - 120, max(250, height - 310))
        draw_panel(screen, board_rect, (252, 247, 239), border_color=ACCENT_COLOR, border_width=3)

        if self.bedside_finished:
            self.draw_wrapped_text(
                screen,
                f"You handled {self.bedside_hits} patient conversations well. {self.bedside_feedback}",
                body_font,
                TEXT_COLOR,
                board_rect.x + 24,
                board_rect.y + 28,
                board_rect.w - 48,
            )
            self.draw_button(screen, self._continue_button_rect(), "Continue")
            return

        current_round = self.current_bedside_round()
        prompt_rect = pygame.Rect(board_rect.x + 24, board_rect.y + 20, board_rect.w - 48, max(82, int(board_rect.h * 0.2)))
        draw_panel(screen, prompt_rect, (255, 252, 246), border_color=ACCENT_COLOR, border_width=2, radius=14, shadow=False)
        self.draw_wrapped_text(screen, current_round["prompt"], heading_font, TEXT_COLOR, prompt_rect.x + 16, prompt_rect.y + 16, prompt_rect.w - 32)

        for index, rect in enumerate(self._bedside_option_rects()):
            draw_panel(screen, rect, (239, 243, 248), border_color=ACCENT_COLOR, border_width=2, radius=14, shadow=False)
            self.draw_text(screen, f"Response {index + 1}", small_font, TEXT_COLOR, rect.x + 16, rect.y + 14)
            self.draw_wrapped_text(screen, current_round["options"][index], body_font, TEXT_COLOR, rect.x + 16, rect.y + 42, rect.w - 32)

        self.draw_wrapped_text(screen, self.bedside_feedback, body_font, TEXT_COLOR, 60, height - 130, width - 120)
        self.draw_text(screen, f"Patients reassured: {self.bedside_hits}", small_font, TEXT_COLOR, 60, height - 165)

    def render_results(self, screen):
        title_font = self._get_font(42, bold=True, minimum=28)
        heading_font = self._get_font(30, bold=True, minimum=22)
        body_font = self._get_font(24, minimum=17)
        small_font = self._get_font(20, minimum=15)
        panel_rect, ratings_rect, summary_rect = self._results_layout_rects()

        draw_panel(screen, panel_rect, (252, 247, 238), border_color=ACCENT_COLOR, border_width=3, radius=22)
        self.draw_text(screen, "Doctor Report", title_font, TEXT_COLOR, panel_rect.x + 24, panel_rect.y + 20)
        self.draw_wrapped_text(
            screen,
            "You completed a doctor workday by triaging urgent cases, matching symptoms, organizing treatment, and communicating with empathy.",
            body_font,
            TEXT_COLOR,
            panel_rect.x + 24,
            panel_rect.y + 20 + title_font.get_height() + 14,
            panel_rect.w - 48,
        )

        skill_cards = self._results_skill_card_rects(ratings_rect)
        ratings = [
            ("Triage", self.skill_scores["triage"]),
            ("Diagnosis", self.skill_scores["diagnosis"]),
            ("Accuracy", self.skill_scores["accuracy"]),
            ("Empathy", self.skill_scores["empathy"]),
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
            "Doctors combine science, observation, and trust. They must prioritize risk, diagnose carefully, document clearly, and communicate in ways patients can follow.",
            body_font,
            TEXT_COLOR,
            summary_rect.x + 18,
            summary_rect.y + 18 + heading_font.get_height() + 8,
            summary_rect.w - 36,
        )

        best_skill = max(self.skill_scores, key=self.skill_scores.get)
        label_map = {
            "triage": "triage",
            "diagnosis": "diagnosis",
            "accuracy": "accuracy",
            "empathy": "empathy",
        }
        self.draw_text(screen, f"Strongest area: {label_map[best_skill].title()}", small_font, TEXT_COLOR, summary_rect.x + 18, summary_rect.bottom - small_font.get_height() - 18)
        self.draw_button(screen, self._results_button_rect(), "Return to Hub")

    def current_diagnosis_round(self):
        return self.diagnosis_rounds[min(self.diagnosis_round_index, len(self.diagnosis_rounds) - 1)]

    def current_bedside_round(self):
        return self.bedside_rounds[min(self.bedside_round_index, len(self.bedside_rounds) - 1)]

    def stage_label(self):
        labels = {
            "intake_dialogue": "Shift Intake Briefing",
            "consult_dialogue": "Consultation Block",
            "rounds_dialogue": "Afternoon Rounds",
            "emergency_dialogue": "Family Update",
            "closing_dialogue": "End of Shift",
        }
        return labels.get(self.active_stage, "Doctor")

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

    def _draw_doctor_avatar(self, screen, rect):
        center_x = rect.centerx
        scale = self._ui_scale()
        head_rect = pygame.Rect(center_x - max(28, int(32 * scale)), rect.y + max(26, int(30 * scale)), max(56, int(64 * scale)), max(68, int(78 * scale)))
        pygame.draw.ellipse(screen, (222, 188, 154), head_rect)
        coat_rect = pygame.Rect(center_x - max(56, int(64 * scale)), head_rect.bottom - 4, max(112, int(128 * scale)), rect.bottom - head_rect.bottom - max(18, int(22 * scale)))
        pygame.draw.rect(screen, (248, 248, 247), coat_rect, border_radius=16)
        shirt_rect = pygame.Rect(coat_rect.centerx - max(18, int(22 * scale)), coat_rect.y + 14, max(36, int(44 * scale)), coat_rect.h - 24)
        pygame.draw.rect(screen, (188, 213, 228), shirt_rect, border_radius=10)
        pygame.draw.line(screen, ACCENT_COLOR, (coat_rect.centerx, coat_rect.y + 14), (coat_rect.centerx, coat_rect.bottom - 16), 3)
        stetho_left = (coat_rect.centerx - max(18, int(22 * scale)), coat_rect.y + 24)
        stetho_right = (coat_rect.centerx + max(18, int(22 * scale)), coat_rect.y + 24)
        stetho_bottom = (coat_rect.centerx, coat_rect.y + max(58, int(70 * scale)))
        pygame.draw.line(screen, TEXT_COLOR, stetho_left, stetho_bottom, 3)
        pygame.draw.line(screen, TEXT_COLOR, stetho_right, stetho_bottom, 3)
        pygame.draw.circle(screen, TEXT_COLOR, stetho_bottom, 6)

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

    def _triage_card_rects(self):
        board_rect = self._triage_board_rect()
        scale = self._ui_scale()
        padding_x = max(18, int(24 * scale))
        header_space = max(58, int(76 * scale))
        gap_x = max(16, int(20 * scale))
        gap_y = max(14, int(18 * scale))
        card_width = (board_rect.w - padding_x * 2 - gap_x) // 2
        card_height = (board_rect.h - header_space - padding_x - gap_y) // 2
        return [
            pygame.Rect(
                board_rect.x + padding_x + (index % 2) * (card_width + gap_x),
                board_rect.y + header_space + (index // 2) * (card_height + gap_y),
                card_width,
                card_height,
            )
            for index in range(4)
        ]

    def _diagnosis_option_rects(self):
        width, height = self.game.screen.get_size()
        scale = self._ui_scale()
        gap = max(14, int(18 * scale))
        total_width = width - 120
        option_width = (total_width - gap * 2) // 3
        option_height = max(64, int(height * 0.12))
        y = max(320, int(height * 0.56))
        return [
            pygame.Rect(60 + index * (option_width + gap), y, option_width, option_height)
            for index in range(3)
        ]

    def _care_plan_pool_rects(self):
        left_rect, _ = self._care_plan_panel_rects()
        scale = self._ui_scale()
        padding_x = max(18, int(24 * scale))
        top = left_rect.y + max(62, int(76 * scale))
        gap = max(10, int(12 * scale))
        card_height = (left_rect.bottom - max(18, int(24 * scale)) - top - gap * 3) // 4
        return [
            pygame.Rect(left_rect.x + padding_x, top + index * (card_height + gap), left_rect.w - padding_x * 2, card_height)
            for index in range(4)
        ]

    def _care_plan_slot_rects(self):
        _, right_rect = self._care_plan_panel_rects()
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

    def _bedside_option_rects(self):
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

    def _triage_board_rect(self):
        width, height = self.game.screen.get_size()
        scale = self._ui_scale()
        margin_x = max(36, int(60 * scale))
        top = max(138, int(150 * scale))
        bottom_space = max(126, int(150 * scale))
        return pygame.Rect(margin_x, top, width - margin_x * 2, height - top - bottom_space)

    def _care_plan_panel_rects(self):
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