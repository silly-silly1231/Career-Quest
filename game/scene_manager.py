# game/scene_manager.py

class SceneManager:
    def __init__(self):
        self.current_scene = None

    def set_scene(self, scene):
        self.current_scene = scene

    def handle_event(self, event):
        if self.current_scene:
            self.current_scene.handle_event(event)

    def update(self, delta_time):
        if self.current_scene:
            self.current_scene.update(delta_time)

    def render(self, screen):
        if self.current_scene:
            self.current_scene.render(screen)