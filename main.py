import os
# رفع مشکل گرافیک ویندوز
os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'

import random
import json
from datetime import datetime
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.modalview import ModalView
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.core.window import Window
from kivy.core.text import Label as CoreLabel, LabelBase # ایمپورت LabelBase برای ثبت فونت
from kivy.properties import ListProperty, NumericProperty, BooleanProperty, StringProperty

# ================== ثبت فونت ایموجی ویندوز ==================
# مسیر فونت ایموجی در ویندوز
emoji_font_path = 'C:/Windows/Fonts/seguiemj.ttf'
if os.path.exists(emoji_font_path):
    LabelBase.register(name='Emoji', fn_regular=emoji_font_path)

Window.size = (500, 700)
Window.clearcolor = (0.98, 0.96, 0.93, 1)
SCORES_FILE = "scores.json"

TILE_COLORS = {
    0: (0.88, 0.85, 0.80, 1), 2: (0.93, 0.89, 0.85, 1), 4: (0.93, 0.87, 0.78, 1),
    8: (0.95, 0.69, 0.47, 1), 16: (0.96, 0.58, 0.39, 1), 32: (0.96, 0.49, 0.37, 1),
    64: (0.96, 0.37, 0.23, 1), 128: (0.93, 0.81, 0.45, 1), 256: (0.93, 0.79, 0.38, 1),
    512: (0.93, 0.77, 0.31, 1), 1024: (0.93, 0.75, 0.24, 1), 2048: (0.93, 0.73, 0.17, 1),
}

TEXT_COLORS = {
    0: (0, 0, 0, 1), 2: (0.47, 0.43, 0.40, 1), 4: (0.47, 0.43, 0.40, 1),
    8: (0.98, 0.96, 0.95, 1), 16: (0.98, 0.96, 0.95, 1), 32: (0.98, 0.96, 0.95, 1),
    64: (0.98, 0.96, 0.95, 1), 128: (0.98, 0.96, 0.95, 1), 256: (0.98, 0.96, 0.95, 1),
    512: (0.98, 0.96, 0.95, 1), 1024: (0.98, 0.96, 0.95, 1), 2048: (0.98, 0.96, 0.95, 1),
}

def load_scores():
    if not os.path.isfile(SCORES_FILE):
        return []
    try:
        with open(SCORES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            data.sort(key=lambda x: x["score"], reverse=True)
            return data
    except:
        return []

def save_score(name, score):
    scores = load_scores()
    new_entry = {"name": name if name.strip() else "Player", "score": score, "date": datetime.now().strftime("%Y-%m-%d")}
    scores.append(new_entry)
    scores.sort(key=lambda x: x["score"], reverse=True)
    scores = scores[:5]
    
    with open(SCORES_FILE, "w", encoding="utf-8") as f:
        json.dump(scores, f, indent=2, ensure_ascii=False)
        
    for i, s in enumerate(scores):
        if s is new_entry:
            return i + 1
    return None

# ================== صفحه Game Over ==================
class GameOverPopup(ModalView):
    def __init__(self, game_instance, rank, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (0.85, 0.55)
        self.background_color = (0, 0, 0, 0.7)
        self.auto_dismiss = False
        self.game_instance = game_instance

        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        with layout.canvas.before:
            Color(0.2, 0.2, 0.25, 1)
            self.rect = RoundedRectangle(pos=layout.pos, size=layout.size, radius=[15])
        layout.bind(pos=self.update_rect, size=self.update_rect)

        title = Label(text="GAME OVER", font_size=40, bold=True, color=(0.9, 0.3, 0.3, 1))
        
        info_text = f"Player: {game_instance.player_name}\nScore: {game_instance.score}"
        if rank == 1:
            info_text += "\n\n🏆 NEW HIGH SCORE! 🏆"
        elif rank and rank <= 5:
            info_text += f"\n\nYou ranked #{rank}!"
            
        # استفاده از فونت ایموجی برای این لیبل
        info_lbl = Label(text=info_text, font_size=22, halign='center', color=(1, 1, 1, 1), font_name='Emoji')

        btn_layout = BoxLayout(size_hint_y=None, height=60, spacing=15)
        
        btn_restart = Button(
            text="🔁 Play Again", font_size=18, bold=True,
            background_normal='', background_color=(0.2, 0.7, 0.3, 1),
            font_name='Emoji' # اعمال فونت
        )
        btn_restart.bind(on_release=self.restart_game)
        
        btn_menu = Button(
            text="🏠 Main Menu", font_size=18, bold=True,
            background_normal='', background_color=(0.7, 0.4, 0.2, 1),
            font_name='Emoji' # اعمال فونت
        )
        btn_menu.bind(on_release=self.go_to_menu)

        btn_layout.add_widget(btn_restart)
        btn_layout.add_widget(btn_menu)

        layout.add_widget(title)
        layout.add_widget(info_lbl)
        layout.add_widget(btn_layout)
        self.add_widget(layout)

    def update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def restart_game(self, instance):
        self.dismiss()
        self.game_instance.init_grid()
        self.game_instance.draw_board()

    def go_to_menu(self, instance):
        self.dismiss()
        App.get_running_app().root.current = 'welcome'

# ================== منطق بازی 2048 ==================
class Game2048(Widget):
    grid = ListProperty([[0]*4 for _ in range(4)])
    score = NumericProperty(0)
    best = NumericProperty(0)
    game_over = BooleanProperty(False)
    player_name = StringProperty("Player")
    touch_start = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.init_grid()
        self.bind(pos=self.draw_board, size=self.draw_board)
        Window.bind(on_key_down=self.on_key_down)

    def init_grid(self):
        self.grid = [[0]*4 for _ in range(4)]
        self.score = 0
        self.game_over = False
        self.add_random_tile()
        self.add_random_tile()

    def add_random_tile(self):
        empty = [(r, c) for r in range(4) for c in range(4) if self.grid[r][c] == 0]
        if empty:
            r, c = random.choice(empty)
            self.grid[r][c] = 2 if random.random() < 0.9 else 4
            self.draw_board()

    def draw_board(self, *args):
        self.canvas.clear()
        with self.canvas:
            Color(0.73, 0.68, 0.62, 1)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[10])
        
        cell_size = self.width / 4.2
        padding = cell_size * 0.05
        offset_x = (self.width - (cell_size * 4 + padding * 3)) / 2
        offset_y = (self.height - (cell_size * 4 + padding * 3)) / 2

        for r in range(4):
            for c in range(4):
                val = self.grid[r][c]
                x = self.x + offset_x + c * (cell_size + padding)
                y = self.y + offset_y + (3 - r) * (cell_size + padding)
                
                with self.canvas:
                    Color(*TILE_COLORS.get(val, (0.93, 0.73, 0.17, 1)))
                    RoundedRectangle(pos=(x, y), size=(cell_size, cell_size), radius=[5])
                
                if val != 0:
                    font_size = int(cell_size * (0.5 if val < 100 else 0.4 if val < 1000 else 0.3))
                    cl = CoreLabel(
                        text=str(val), font_size=font_size, bold=True,
                        text_size=(cell_size, cell_size), halign='center', valign='middle'
                    )
                    cl.refresh()
                    with self.canvas:
                        Color(*TEXT_COLORS.get(val, (1,1,1,1)))
                        Rectangle(texture=cl.texture, pos=(x, y))

    def move(self, direction):
        if self.game_over: return
        moved = False
        new_grid = [row[:] for row in self.grid]

        if direction == 'left':
            for r in range(4):
                row = [x for x in new_grid[r] if x != 0]
                for i in range(len(row) - 1):
                    if row[i] == row[i+1]:
                        row[i] *= 2; self.score += row[i]; row[i+1] = 0
                row = [x for x in row if x != 0]
                row += [0] * (4 - len(row))
                if row != new_grid[r]: new_grid[r] = row; moved = True
        elif direction == 'right':
            for r in range(4):
                row = [x for x in new_grid[r] if x != 0]
                for i in range(len(row) - 1, 0, -1):
                    if row[i] == row[i-1]:
                        row[i] *= 2; self.score += row[i]; row[i-1] = 0
                row = [x for x in row if x != 0]
                row = [0] * (4 - len(row)) + row
                if row != new_grid[r]: new_grid[r] = row; moved = True
        elif direction == 'up':
            for c in range(4):
                col = [new_grid[r][c] for r in range(4) if new_grid[r][c] != 0]
                for i in range(len(col) - 1):
                    if col[i] == col[i+1]:
                        col[i] *= 2; self.score += col[i]; col[i+1] = 0
                col = [x for x in col if x != 0]
                col += [0] * (4 - len(col))
                for r in range(4):
                    if new_grid[r][c] != col[r]: new_grid[r][c] = col[r]; moved = True
        elif direction == 'down':
            for c in range(4):
                col = [new_grid[r][c] for r in range(4) if new_grid[r][c] != 0]
                for i in range(len(col) - 1, 0, -1):
                    if col[i] == col[i-1]:
                        col[i] *= 2; self.score += col[i]; col[i-1] = 0
                col = [x for x in col if x != 0]
                col = [0] * (4 - len(col)) + col
                for r in range(4):
                    if new_grid[r][c] != col[r]: new_grid[r][c] = col[r]; moved = True

        if moved:
            self.grid = new_grid
            self.add_random_tile()
            if self.is_game_over():
                self.game_over = True
                rank = save_score(self.player_name, self.score)
                popup = GameOverPopup(game_instance=self, rank=rank)
                popup.open()
            self.draw_board()

    def is_game_over(self):
        for r in range(4):
            for c in range(4):
                if self.grid[r][c] == 0: return False
                if c < 3 and self.grid[r][c] == self.grid[r][c+1]: return False
                if r < 3 and self.grid[r][c] == self.grid[r+1][c]: return False
        return True

    def on_key_down(self, window, key, scancode, codepoint, modifiers):
        if App.get_running_app().root.current != 'game': return False
        if key == 276 or key == ord('a'): self.move('left')
        elif key == 275 or key == ord('d'): self.move('right')
        elif key == 273 or key == ord('w'): self.move('up')
        elif key == 274 or key == ord('s'): self.move('down')
        elif key == ord('r'): self.init_grid(); self.draw_board()
        return True

    def on_touch_down(self, touch):
        self.touch_start = touch.pos

    def on_touch_up(self, touch):
        if self.touch_start is None: return
        dx = touch.x - self.touch_start[0]
        dy = touch.y - self.touch_start[1]
        if abs(dx) > abs(dy):
            if dx > 30: self.move('right')
            elif dx < -30: self.move('left')
        else:
            if dy > 30: self.move('up')
            elif dy < -30: self.move('down')
        self.touch_start = None

# ================== صفحه Welcome ==================
class WelcomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=30, spacing=20)
        
        title = Label(text="[b]2048[/b]", font_size=60, markup=True, color=(0.5, 0.4, 0.3, 1), size_hint_y=0.2)
        
        name_box = BoxLayout(orientation='vertical', size_hint_y=0.15, spacing=5)
        name_lbl = Label(text="Enter your name:", size_hint_y=None, height=30, color=(0.4, 0.4, 0.4, 1))
        self.name_input = TextInput(
            text="Player", multiline=False, font_size=20,
            halign="center", size_hint_y=None, height=50, background_color=(0.9, 0.9, 0.9, 1)
        )
        name_box.add_widget(name_lbl)
        name_box.add_widget(self.name_input)
        
        # اعمال فونت ایموجی روی دکمه شروع
        start_btn = Button(
            text="▶ START GAME", font_size=24, bold=True, size_hint_y=0.15,
            background_normal='', background_color=(0.2, 0.8, 0.4, 1),
            font_name='Emoji'
        )
        start_btn.bind(on_release=self.start_game)
        
        score_box = BoxLayout(orientation='vertical', size_hint_y=0.4, padding=10)
        with score_box.canvas.before:
            Color(0.85, 0.82, 0.78, 1)
            self.rect = RoundedRectangle(pos=score_box.pos, size=score_box.size, radius=[10])
        score_box.bind(pos=self.update_rect, size=self.update_rect)
        
        # اعمال فونت ایموجی روی عنوان جدول
        sb_title = Label(text="🏆 Top 5 Scores", size_hint_y=None, height=40, font_size=20, bold=True, color=(0.3, 0.2, 0.1, 1), font_name='Emoji')
        score_box.add_widget(sb_title)
        
        self.sb_layout = BoxLayout(orientation='vertical')
        score_box.add_widget(self.sb_layout)

        layout.add_widget(title)
        layout.add_widget(name_box)
        layout.add_widget(start_btn)
        layout.add_widget(score_box)
        self.add_widget(layout)

    def update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def on_enter(self):
        self.sb_layout.clear_widgets()
        scores = load_scores()
        if not scores:
            self.sb_layout.add_widget(Label(text="No scores yet. Play to rank!", color=(0.4, 0.4, 0.4, 1)))
        else:
            for i, s in enumerate(scores):
                color = (0.8, 0.6, 0.1, 1) if i == 0 else (0.3, 0.3, 0.3, 1)
                text = f"{i+1}. {s['name']} - {s['score']} pts"
                self.sb_layout.add_widget(Label(text=text, font_size=18, bold=True, color=color))

    def start_game(self, instance):
        name = self.name_input.text.strip()
        if not name: name = "Player"
            
        game_widget = App.get_running_app().game_widget
        game_widget.player_name = name
        game_widget.init_grid()
        self.manager.current = 'game'

class GameScreen(Screen):
    pass

class Game2048App(App):
    def build(self):
        sm = ScreenManager()
        welcome = WelcomeScreen(name='welcome')
        game_screen = GameScreen(name='game')
        
        game_layout = BoxLayout(orientation='vertical')
        header = BoxLayout(size_hint_y=0.1, padding=10)
        
        self.score_label = Label(text="Score: 0", font_size=24, bold=True, color=(0.47, 0.43, 0.40, 1))
        self.best_label = Label(text="Best: 0", font_size=24, bold=True, color=(0.47, 0.43, 0.40, 1))
        header.add_widget(self.score_label)
        header.add_widget(self.best_label)
        
        self.game_widget = Game2048(size_hint_y=0.9)
        
        def update_score(*args):
            self.score_label.text = f"Score: {self.game_widget.score}"
            if self.game_widget.score > self.game_widget.best:
                self.game_widget.best = self.game_widget.score
            self.best_label.text = f"Best: {self.game_widget.best}"
        
        self.game_widget.bind(score=update_score)
        
        game_layout.add_widget(header)
        game_layout.add_widget(self.game_widget)
        game_screen.add_widget(game_layout)
        
        sm.add_widget(welcome)
        sm.add_widget(game_screen)
        return sm

if __name__ == '__main__':
    Game2048App().run()