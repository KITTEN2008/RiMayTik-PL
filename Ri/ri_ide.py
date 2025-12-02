# Ri IDE v1.6 - Среда разработки для языка Ri 2.13.1
# Создано программистом KITTEN в 2025 году

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog, Canvas
import threading
import queue
import re
import time
import os
import subprocess
import json

try:
    from ri_compiler import run_ri_code, RI_LANGUAGE_VERSION, RI_LANGUAGE_CREATOR, RI_LANGUAGE_YEAR
except ImportError:
    import ri_compiler
    run_ri_code = ri_compiler.run_ri_code
    RI_LANGUAGE_VERSION = ri_compiler.RI_LANGUAGE_VERSION
    RI_LANGUAGE_CREATOR = "KITTEN"
    RI_LANGUAGE_YEAR = "2025"

class LineNumbers(tk.Canvas):
    def __init__(self, parent, text_widget, **kwargs):
        super().__init__(parent, **kwargs)
        self.text_widget = text_widget
        self.config(
            width=60,
            bg='#2d2d2d',
            highlightthickness=0,
            relief=tk.FLAT
        )
        self.font = ("Consolas", 12)
        
        self.text_widget.bind('<Configure>', self._redraw)
        self.text_widget.bind('<KeyRelease>', self._redraw)
        self.text_widget.bind('<MouseWheel>', self._redraw)
        self.text_widget.bind('<Button-4>', self._redraw)
        self.text_widget.bind('<Button-5>', self._redraw)
        
        self.breakpoints = set()
        self.bind('<Button-1>', self._toggle_breakpoint)
        self.current_execution_line = None
        
    def _redraw(self, event=None):
        self.delete("all")
        
        try:
            first_line = self.text_widget.index('@0,0').split('.')[0]
            last_line = self.text_widget.index('@0,%d' % self.text_widget.winfo_height()).split('.')[0]
            
            first_line = max(1, int(first_line) - 1)
            last_line = min(int(last_line) + 1, int(self.text_widget.index('end-1c').split('.')[0]))
            
            for line_num in range(first_line, last_line + 1):
                bbox = self.text_widget.bbox(f'{line_num}.0')
                if bbox:
                    y = bbox[1]
                    
                    if self.current_execution_line == line_num:
                        self.create_rectangle(
                            0, y - 2, 60, y + 18,
                            fill='#264f78',
                            outline='',
                            tags=f'current_line_{line_num}'
                        )
                    
                    self.create_text(
                        40, y,
                        text=str(line_num),
                        anchor='ne',
                        fill='#858585',
                        font=self.font,
                        tags=f'line_{line_num}'
                    )
                    
                    if line_num in self.breakpoints:
                        self.create_oval(
                            10, y - 5, 20, y + 5,
                            fill='#ff5555',
                            outline='#ff5555',
                            tags=f'breakpoint_{line_num}'
                        )
        except:
            pass
        
        self.config(scrollregion=self.bbox('all'))
    
    def _toggle_breakpoint(self, event):
        try:
            line_num = int(self.text_widget.index(f'@0,{event.y}').split('.')[0])
            
            if line_num in self.breakpoints:
                self.breakpoints.remove(line_num)
            else:
                self.breakpoints.add(line_num)
            
            self._redraw()
        except:
            pass
    
    def get_breakpoints(self):
        return sorted(self.breakpoints)
    
    def set_execution_line(self, line_num):
        self.current_execution_line = line_num
        self._redraw()
    
    def clear_execution_line(self):
        self.current_execution_line = None
        self._redraw()

class Autocomplete:
    def __init__(self, text_widget, ide):
        self.text_widget = text_widget
        self.ide = ide
        self.autocomplete_window = None
        self.suggestions = []
        self.current_suggestion_index = 0
        
        self.keywords = [
            'перем', 'если', 'иначе', 'цикл', 'конец', 'то',
            'вывести', 'ввести', 'функция', 'возврат',
            'и', 'или', 'не', 'истина', 'ложь'
        ]
        
        self.graphics_commands = [
            'окно', 'прямоугольник', 'круг', 'линия', 'текст',
            'задержка', 'очистить', 'обновить_экран', 'остановить'
        ]
        
        self.event_functions = [
            'мышь_х', 'мышь_у', 'мышь_нажата', 'клавиша_нажата',
            'установить_обработчик'
        ]
        
        self.builtin_functions = [
            'случайно', 'длина', 'корень', 'синус', 'косинус',
            'округлить', 'строка', 'число', 'тип', 'время',
            'список_длина', 'элемент'
        ]
        
        self.list_commands = [
            'список', 'добавить', 'удалить'
        ]
        
        self.all_suggestions = (self.keywords + self.graphics_commands + 
                               self.event_functions + self.builtin_functions +
                               self.list_commands)
        
        self.text_widget.bind('<KeyRelease>', self._on_key_release)
        self.text_widget.bind('<Tab>', self._on_tab)
        self.text_widget.bind('<Down>', self._on_down)
        self.text_widget.bind('<Up>', self._on_up)
        self.text_widget.bind('<Return>', self._on_return)
        self.text_widget.bind('<Escape>', self._on_escape)
    
    def _on_key_release(self, event):
        if event.keysym in ('Shift_L', 'Shift_R', 'Control_L', 'Control_R',
                           'Alt_L', 'Alt_R', 'Caps_Lock'):
            return
        
        self._close_autocomplete()
        word = self._get_current_word()
        
        if len(word) >= 1:
            self.suggestions = [s for s in self.all_suggestions 
                              if s.startswith(word.lower())]
            
            if self.suggestions:
                self._show_autocomplete()
    
    def _get_current_word(self):
        cursor_pos = self.text_widget.index(tk.INSERT)
        line, col = map(int, cursor_pos.split('.'))
        line_text = self.text_widget.get(f'{line}.0', f'{line}.{col}')
        
        word_start = 0
        for i in range(col - 1, -1, -1):
            char = self.text_widget.get(f'{line}.{i}')
            if not char.isalnum() and char not in ('_',):
                word_start = i + 1
                break
        
        return line_text[word_start:].lower()
    
    def _show_autocomplete(self):
        try:
            cursor_pos = self.text_widget.index(tk.INSERT)
            bbox = self.text_widget.bbox(cursor_pos)
            if not bbox:
                return
                
            x, y, _, _ = bbox
            
            self.autocomplete_window = tk.Toplevel(self.text_widget)
            self.autocomplete_window.wm_overrideredirect(True)
            self.autocomplete_window.wm_geometry(f"+{self.text_widget.winfo_rootx() + x}+"
                                               f"{self.text_widget.winfo_rooty() + y + 20}")
            
            listbox = tk.Listbox(
                self.autocomplete_window,
                height=min(len(self.suggestions), 8),
                width=30,
                font=("Consolas", 11),
                bg='#2d2d2d',
                fg='white',
                selectbackground='#264f78',
                relief=tk.FLAT
            )
            listbox.pack()
            
            for suggestion in self.suggestions:
                listbox.insert(tk.END, suggestion)
            
            listbox.select_set(0)
            self.autocomplete_listbox = listbox
        except:
            pass
    
    def _close_autocomplete(self):
        if self.autocomplete_window:
            self.autocomplete_window.destroy()
            self.autocomplete_window = None
    
    def _on_tab(self, event):
        if self.autocomplete_window:
            self._insert_suggestion()
            return 'break'
    
    def _on_down(self, event):
        if self.autocomplete_window:
            current = self.autocomplete_listbox.curselection()[0]
            if current < len(self.suggestions) - 1:
                self.autocomplete_listbox.select_clear(current)
                self.autocomplete_listbox.select_set(current + 1)
            return 'break'
    
    def _on_up(self, event):
        if self.autocomplete_window:
            current = self.autocomplete_listbox.curselection()[0]
            if current > 0:
                self.autocomplete_listbox.select_clear(current)
                self.autocomplete_listbox.select_set(current - 1)
            return 'break'
    
    def _on_return(self, event):
        if self.autocomplete_window:
            self._insert_suggestion()
            return 'break'
    
    def _on_escape(self, event):
        self._close_autocomplete()
    
    def _insert_suggestion(self):
        if not self.autocomplete_window:
            return
        
        selection = self.autocomplete_listbox.curselection()
        if selection:
            suggestion = self.suggestions[selection[0]]
            
            cursor_pos = self.text_widget.index(tk.INSERT)
            line, col = map(int, cursor_pos.split('.'))
            
            line_text = self.text_widget.get(f'{line}.0', f'{line}.{col}')
            word_start = 0
            for i in range(col - 1, -1, -1):
                char = self.text_widget.get(f'{line}.{i}')
                if not char.isalnum() and char not in ('_',):
                    word_start = i + 1
                    break
            
            self.text_widget.delete(f'{line}.{word_start}', cursor_pos)
            self.text_widget.insert(f'{line}.{word_start}', suggestion)
            
            self._close_autocomplete()

class GitIntegration:
    def __init__(self, project_path):
        self.project_path = project_path
        
    def init_repository(self):
        try:
            result = subprocess.run(
                ['git', 'init'],
                cwd=self.project_path,
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception as e:
            return False
    
    def commit_changes(self, message):
        try:
            subprocess.run(['git', 'add', '.'], cwd=self.project_path, 
                         capture_output=True)
            
            result = subprocess.run(
                ['git', 'commit', '-m', message],
                cwd=self.project_path,
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception as e:
            return False
    
    def get_status(self):
        try:
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=self.project_path,
                capture_output=True,
                text=True
            )
            if result.stdout:
                return [line for line in result.stdout.strip().split('\n') if line]
            return []
        except Exception as e:
            return []
    
    def get_branches(self):
        try:
            result = subprocess.run(
                ['git', 'branch'],
                cwd=self.project_path,
                capture_output=True,
                text=True
            )
            branches = []
            current_branch = None
            for line in result.stdout.split('\n'):
                if line.strip():
                    if line.startswith('*'):
                        current_branch = line[2:].strip()
                        branches.append(current_branch)
                    else:
                        branches.append(line.strip())
            return branches, current_branch
        except Exception as e:
            return [], None
    
    def get_history(self, limit=20):
        try:
            result = subprocess.run(
                ['git', 'log', f'--oneline', f'-{limit}'],
                cwd=self.project_path,
                capture_output=True,
                text=True
            )
            if result.stdout:
                return [line for line in result.stdout.strip().split('\n') if line]
            return []
        except Exception as e:
            return []
    
    def create_branch(self, name):
        try:
            result = subprocess.run(
                ['git', 'branch', name],
                cwd=self.project_path,
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception as e:
            return False
    
    def checkout_branch(self, name):
        try:
            result = subprocess.run(
                ['git', 'checkout', name],
                cwd=self.project_path,
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception as e:
            return False

class GraphicsWindow:
    def __init__(self, width=800, height=600, title="Графика Ri", ide=None):
        self.window = tk.Toplevel()
        self.window.title(title)
        self.window.geometry(f"{width}x{height}")
        self.ide = ide
        
        self.canvas = Canvas(self.window, width=width, height=height, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        self.canvas.focus_set()
        
        self.mouse_x = 0
        self.mouse_y = 0
        self.mouse_pressed = False
        self.keys_pressed = set()
        self.last_key = ""
        
        self.bind_events()
        self.objects = []
        self.is_open = True
        
        self.window.protocol("WM_DELETE_WINDOW", self.close)
    
    def bind_events(self):
        self.canvas.bind("<Motion>", self.on_mouse_move)
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_release)
        self.canvas.bind("<ButtonPress-2>", self.on_mouse_press_middle)
        self.canvas.bind("<ButtonRelease-2>", self.on_mouse_release_middle)
        self.canvas.bind("<ButtonPress-3>", self.on_mouse_press_right)
        self.canvas.bind("<ButtonRelease-3>", self.on_mouse_release_right)
        
        self.canvas.bind("<KeyPress>", self.on_key_press)
        self.canvas.bind("<KeyRelease>", self.on_key_release)
        
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
    
    def on_mouse_move(self, event):
        self.mouse_x = event.x
        self.mouse_y = event.y
        if self.ide:
            self.ide.event_queue.put(("mouse_move", self.mouse_x, self.mouse_y))
    
    def on_mouse_press(self, event):
        self.mouse_pressed = True
        self.mouse_x = event.x
        self.mouse_y = event.y
        if self.ide:
            self.ide.event_queue.put(("mouse_press", "левая", self.mouse_x, self.mouse_y))
    
    def on_mouse_release(self, event):
        self.mouse_pressed = False
        self.mouse_x = event.x
        self.mouse_y = event.y
        if self.ide:
            self.ide.event_queue.put(("mouse_release", "левая", self.mouse_x, self.mouse_y))
    
    def on_mouse_press_middle(self, event):
        self.mouse_x = event.x
        self.mouse_y = event.y
        if self.ide:
            self.ide.event_queue.put(("mouse_press", "средняя", self.mouse_x, self.mouse_y))
    
    def on_mouse_release_middle(self, event):
        self.mouse_x = event.x
        self.mouse_y = event.y
        if self.ide:
            self.ide.event_queue.put(("mouse_release", "средняя", self.mouse_x, self.mouse_y))
    
    def on_mouse_press_right(self, event):
        self.mouse_x = event.x
        self.mouse_y = event.y
        if self.ide:
            self.ide.event_queue.put(("mouse_press", "правая", self.mouse_x, self.mouse_y))
    
    def on_mouse_release_right(self, event):
        self.mouse_x = event.x
        self.mouse_y = event.y
        if self.ide:
            self.ide.event_queue.put(("mouse_release", "правая", self.mouse_x, self.mouse_y))
    
    def on_key_press(self, event):
        key = self.translate_key(event.keysym)
        self.keys_pressed.add(key)
        self.last_key = key
        
        if self.ide:
            self.ide.event_queue.put(("key_press", key))
    
    def on_key_release(self, event):
        key = self.translate_key(event.keysym)
        if key in self.keys_pressed:
            self.keys_pressed.remove(key)
        
        if self.ide:
            self.ide.event_queue.put(("key_release", key))
    
    def on_mouse_wheel(self, event):
        direction = "вверх" if event.delta > 0 else "вниз"
        if self.ide:
            self.ide.event_queue.put(("mouse_wheel", direction, self.mouse_x, self.mouse_y))
    
    def translate_key(self, keysym):
        translations = {
            "space": "пробел",
            "Return": "ввод",
            "Escape": "эскейп",
            "Tab": "таб",
            "BackSpace": "бэкспейс",
            "Shift_L": "шифт",
            "Shift_R": "шифт",
            "Control_L": "контрол",
            "Control_R": "контрол",
            "Alt_L": "альт",
            "Alt_R": "альт",
            "Left": "влево",
            "Right": "вправо",
            "Up": "вверх",
            "Down": "вниз",
            "Home": "хом",
            "End": "энд",
            "Page_Up": "пэйдж_ап",
            "Page_Down": "пэйдж_даун",
            "Insert": "инсерт",
            "Delete": "делит",
            "F1": "ф1",
            "F2": "ф2",
            "F3": "ф3",
            "F4": "ф4",
            "F5": "ф5",
            "F6": "ф6",
            "F7": "ф7",
            "F8": "ф8",
            "F9": "ф9",
            "F10": "ф10",
            "F11": "ф11",
            "F12": "ф12",
        }
        
        if keysym in translations:
            return translations[keysym]
        
        if len(keysym) == 1:
            return keysym.lower()
        
        if keysym.startswith("KP_"):
            return keysym[3:].lower()
        
        return keysym.lower()
    
    def get_mouse_x(self):
        return self.mouse_x
    
    def get_mouse_y(self):
        return self.mouse_y
    
    def get_mouse_pressed(self):
        return self.mouse_pressed
    
    def get_key_pressed(self, key_code):
        return key_code in self.keys_pressed
    
    def close(self):
        self.is_open = False
        self.window.destroy()
    
    def clear(self, color="white"):
        self.canvas.delete("all")
        self.canvas.config(bg=self._translate_color(color))
        self.objects.clear()
    
    def draw_rectangle(self, x, y, width, height, color="black"):
        fill_color = self._translate_color(color)
        outline_color = "black" if fill_color != "black" else "white"
        obj = self.canvas.create_rectangle(
            x, y, x + width, y + height,
            fill=fill_color,
            outline=outline_color,
            width=2
        )
        self.objects.append(obj)
        return obj
    
    def draw_circle(self, x, y, radius, color="black"):
        fill_color = self._translate_color(color)
        outline_color = "black" if fill_color != "black" else "white"
        obj = self.canvas.create_oval(
            x - radius, y - radius,
            x + radius, y + radius,
            fill=fill_color,
            outline=outline_color,
            width=2
        )
        self.objects.append(obj)
        return obj
    
    def draw_line(self, x1, y1, x2, y2, color="black"):
        obj = self.canvas.create_line(
            x1, y1, x2, y2,
            fill=self._translate_color(color),
            width=2
        )
        self.objects.append(obj)
        return obj
    
    def draw_text(self, x, y, text, color="black"):
        obj = self.canvas.create_text(
            x, y,
            text=text,
            fill=self._translate_color(color),
            font=("Arial", 14)
        )
        self.objects.append(obj)
        return obj
    
    def update_screen(self):
        self.window.update()
    
    def _translate_color(self, color_name):
        colors = {
            "черный": "black",
            "белый": "white",
            "красный": "red",
            "зеленый": "green",
            "синий": "blue",
            "желтый": "yellow",
            "оранжевый": "orange",
            "фиолетовый": "purple",
            "розовый": "pink",
            "серый": "gray",
            "голубой": "lightblue",
            "коричневый": "brown",
            "бирюзовый": "turquoise",
            "золотой": "gold",
            "серебряный": "silver",
            "светло-голубой": "lightblue",
            "темно-синий": "darkblue",
            "темно-зеленый": "darkgreen",
            "светло-зеленый": "lightgreen",
            "светло-розовый": "lightpink",
        }
        return colors.get(color_name.lower(), color_name)

class RiIDE:
    def __init__(self, root):
        self.root = root
        self.ide_version = "1.6"
        self.root.title(f"Ri IDE v{self.ide_version} - Язык Ri {RI_LANGUAGE_VERSION} (создатель: {RI_LANGUAGE_CREATOR}, {RI_LANGUAGE_YEAR})")
        self.root.geometry("1300x850")
        
        self.output_queue = queue.Queue()
        self.input_queue = queue.Queue()
        self.graphics_queue = queue.Queue()
        self.event_queue = queue.Queue()
        self.debug_queue = queue.Queue()
        
        self.event_handlers = {
            "mouse_move": None,
            "mouse_press": None,
            "mouse_release": None,
            "key_press": None,
            "key_release": None,
            "mouse_wheel": None
        }
        
        self.waiting_for_input = False
        self.current_input_prompt = ""
        self.graphics_window = None
        self.is_running = False
        self.debug_mode = False
        self.is_paused = False
        self.current_debug_line = 0
        self.breakpoints = set()
        self.call_stack = []
        
        self.git_integration = None
        self.current_project_path = None
        
        self.setup_ui()
        self.setup_tags()
        self.insert_sample_code()
        
        self.autocomplete = Autocomplete(self.code_editor, self)
        
        self.root.after(100, self.process_queue)
        self.root.after(100, self.process_graphics_queue)
        self.root.after(50, self.process_events)
        self.root.after(100, self.process_debug_queue)
        
        self.setup_shortcuts()
        
    def setup_ui(self):
        menubar = tk.Menu(self.root)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="📄 Новый", command=self.new_file, accelerator="Ctrl+N")
        file_menu.add_command(label="📂 Открыть", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="💾 Сохранить", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_command(label="💾 Сохранить как", command=self.save_as_file)
        file_menu.add_separator()
        file_menu.add_command(label="🚪 Выход", command=self.root.quit)
        
        project_menu = tk.Menu(menubar, tearoff=0)
        project_menu.add_command(label="📁 Создать проект", command=self.create_project)
        project_menu.add_command(label="📂 Открыть проект", command=self.open_project)
        project_menu.add_separator()
        project_menu.add_command(label="🔄 Статус Git", command=self.git_status)
        project_menu.add_command(label="💾 Коммит", command=self.git_commit)
        project_menu.add_command(label="📚 История", command=self.git_history)
        project_menu.add_separator()
        project_menu.add_command(label="🌿 Управление ветками", command=self.git_branches)
        
        run_menu = tk.Menu(menubar, tearoff=0)
        run_menu.add_command(label="▶ Запуск (F5)", command=self.run_code, accelerator="F5")
        run_menu.add_command(label="▶ Отладка (F6)", command=self.start_debug, accelerator="F6")
        run_menu.add_command(label="■ Остановить", command=self.stop_execution)
        run_menu.add_separator()
        run_menu.add_command(label="🎨 Открыть графику", command=self.open_graphics_window)
        run_menu.add_command(label="🧹 Очистить графику", command=self.clear_graphics)
        run_menu.add_separator()
        run_menu.add_command(label="🧹 Очистить консоль", command=self.clear_console)
        
        debug_menu = tk.Menu(menubar, tearoff=0)
        debug_menu.add_command(label="⏸ Пауза (F7)", command=self.debug_pause, accelerator="F7")
        debug_menu.add_command(label="▶ Продолжить (F8)", command=self.debug_continue, accelerator="F8")
        debug_menu.add_command(label="➡ Шаг вперед (F10)", command=self.debug_step_over, accelerator="F10")
        debug_menu.add_command(label="⬇ Шаг внутрь (F11)", command=self.debug_step_into, accelerator="F11")
        debug_menu.add_separator()
        debug_menu.add_command(label="🔴 Установить точку останова (F9)", command=self.toggle_breakpoint, accelerator="F9")
        debug_menu.add_command(label="🧹 Очистить все точки останова", command=self.clear_all_breakpoints)
        
        graphics_menu = tk.Menu(menubar, tearoff=0)
        graphics_menu.add_command(label="🎮 Пример: Рисовалка", command=self.insert_draw_example)
        graphics_menu.add_command(label="🎯 Пример: Цели", command=self.insert_target_example)
        graphics_menu.add_command(label="⌨️ Пример: Клавиатура", command=self.insert_keyboard_example)
        graphics_menu.add_command(label="🏎️ Пример: Машинка", command=self.insert_car_example)
        
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="📖 Справка", command=self.show_help)
        help_menu.add_command(label="🖱️ События мыши", command=self.show_mouse_help)
        help_menu.add_command(label="⌨️ Коды клавиш", command=self.show_keyboard_help)
        help_menu.add_command(label="🐛 Отладка", command=self.show_debug_help)
        help_menu.add_command(label="🐙 Git", command=self.show_git_help)
        help_menu.add_command(label="📚 Примеры", command=self.show_examples)
        help_menu.add_command(label="ℹ️ О программе", command=self.show_about)
        
        menubar.add_cascade(label="Файл", menu=file_menu)
        menubar.add_cascade(label="Проект", menu=project_menu)
        menubar.add_cascade(label="Выполнение", menu=run_menu)
        menubar.add_cascade(label="Отладка", menu=debug_menu)
        menubar.add_cascade(label="Интерактив", menu=graphics_menu)
        menubar.add_cascade(label="Помощь", menu=help_menu)
        
        self.root.config(menu=menubar)
        
        toolbar = ttk.Frame(self.root, relief=tk.RAISED)
        toolbar.pack(fill=tk.X, padx=2, pady=2)
        
        style = ttk.Style()
        style.configure('Green.TButton', background='#4CAF50', foreground='black')
        style.configure('Red.TButton', background='#F44336', foreground='black')
        style.configure('Blue.TButton', background='#2196F3', foreground='black')
        style.configure('Purple.TButton', background='#9C27B0', foreground='black')
        style.configure('Orange.TButton', background='#FF9800', foreground='black')
        
        ttk.Button(toolbar, text="▶ Запуск (F5)", command=self.run_code, style='Green.TButton').pack(side=tk.LEFT, padx=2, pady=2)
        ttk.Button(toolbar, text="▶ Отладка (F6)", command=self.start_debug, style='Orange.TButton').pack(side=tk.LEFT, padx=2, pady=2)
        ttk.Button(toolbar, text="■ Стоп", command=self.stop_execution, style='Red.TButton').pack(side=tk.LEFT, padx=2, pady=2)
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)
        ttk.Button(toolbar, text="🎮 Графика", command=self.open_graphics_window, style='Purple.TButton').pack(side=tk.LEFT, padx=2, pady=2)
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)
        ttk.Button(toolbar, text="📄 Новый", command=self.new_file, style='Blue.TButton').pack(side=tk.LEFT, padx=2, pady=2)
        ttk.Button(toolbar, text="📂 Открыть", command=self.open_file, style='Blue.TButton').pack(side=tk.LEFT, padx=2, pady=2)
        ttk.Button(toolbar, text="💾 Сохранить", command=self.save_file, style='Blue.TButton').pack(side=tk.LEFT, padx=2, pady=2)
        
        event_frame = ttk.Frame(self.root)
        event_frame.pack(fill=tk.X, padx=5, pady=2)
        
        self.mouse_label = ttk.Label(event_frame, text="Мышь: (0, 0) Не нажата")
        self.mouse_label.pack(side=tk.LEFT, padx=10)
        
        self.key_label = ttk.Label(event_frame, text="Клавиши: ")
        self.key_label.pack(side=tk.LEFT, padx=10)
        
        self.debug_label = ttk.Label(event_frame, text="Отладка: выключена", foreground="gray")
        self.debug_label.pack(side=tk.LEFT, padx=10)
        
        self.git_label = ttk.Label(event_frame, text="Git: не инициализирован", foreground="gray")
        self.git_label.pack(side=tk.LEFT, padx=10)
        
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        left_paned = ttk.PanedWindow(main_paned, orient=tk.VERTICAL)
        
        editor_frame = ttk.LabelFrame(left_paned, text="📝 Редактор кода Ri", padding=10)
        
        editor_container = tk.Frame(editor_frame, bg='#1e1e1e')
        editor_container.pack(fill=tk.BOTH, expand=True)
        
        self.code_editor = scrolledtext.ScrolledText(
            editor_container,
            wrap=tk.WORD,
            font=("Consolas", 12),
            bg='#1e1e1e',
            fg='#d4d4d4',
            insertbackground='white',
            undo=True,
            maxundo=-1,
            height=15,
            relief=tk.FLAT,
            highlightthickness=0
        )
        self.code_editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.line_numbers = LineNumbers(
            editor_container,
            self.code_editor,
            bg='#2d2d2d'
        )
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)
        
        self.code_editor.bind('<KeyRelease>', 
                             lambda e: (self.highlight_syntax(), self.line_numbers._redraw()))
        
        console_frame = ttk.LabelFrame(left_paned, text="📊 Консоль (Вывод и Ввод)", padding=10)
        
        self.console_output = scrolledtext.ScrolledText(
            console_frame,
            wrap=tk.WORD,
            font=("Consolas", 11),
            bg='#0c0c0c',
            fg='white',
            height=8
        )
        self.console_output.pack(fill=tk.BOTH, expand=True)
        
        self.input_frame = ttk.Frame(console_frame)
        
        input_label = ttk.Label(self.input_frame, text="Ввод данных:", font=("Arial", 10, "bold"))
        input_label.pack(side=tk.LEFT, padx=5)
        
        self.input_prompt = ttk.Label(self.input_frame, text="", foreground="orange")
        self.input_prompt.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        
        self.input_entry = ttk.Entry(self.input_frame, font=("Arial", 11))
        self.input_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        self.input_button = ttk.Button(
            self.input_frame,
            text="Отправить (Enter)",
            command=self.send_input
        )
        self.input_button.pack(side=tk.LEFT, padx=5)
        
        self.input_frame.pack_forget()
        
        left_paned.add(editor_frame, weight=3)
        left_paned.add(console_frame, weight=1)
        
        right_paned = ttk.PanedWindow(main_paned, orient=tk.VERTICAL)
        right_paned.config(width=350)
        
        debug_frame = ttk.LabelFrame(right_paned, text="🐛 Отладчик", padding=10)
        
        debug_toolbar = tk.Frame(debug_frame)
        debug_toolbar.pack(fill=tk.X, pady=(0, 5))
        
        debug_buttons = [
            ("▶ Продолжить (F8)", self.debug_continue, "#4CAF50"),
            ("⏸ Пауза (F7)", self.debug_pause, "#FF9800"),
            ("➡ Шаг вперед (F10)", self.debug_step_over, "#2196F3"),
            ("⬇ Шаг внутрь (F11)", self.debug_step_into, "#2196F3"),
            ("⬆ Шаг наружу", self.debug_step_out, "#2196F3"),
            ("■ Стоп", self.debug_stop, "#F44336"),
        ]
        
        for text, command, color in debug_buttons:
            btn = tk.Button(
                debug_toolbar,
                text=text,
                command=command,
                bg=color,
                fg='black',
                font=("Arial", 9),
                relief=tk.FLAT,
                padx=8,
                pady=4
            )
            btn.pack(side=tk.LEFT, padx=1, pady=1)
        
        debug_notebook = ttk.Notebook(debug_frame)
        debug_notebook.pack(fill=tk.BOTH, expand=True)
        
        variables_frame = ttk.Frame(debug_notebook)
        
        self.variables_tree = ttk.Treeview(
            variables_frame,
            columns=('value', 'type'),
            show='tree headings',
            height=8
        )
        self.variables_tree.heading('#0', text='Имя')
        self.variables_tree.heading('value', text='Значение')
        self.variables_tree.heading('type', text='Тип')
        
        scrollbar = ttk.Scrollbar(variables_frame, orient="vertical", command=self.variables_tree.yview)
        self.variables_tree.configure(yscrollcommand=scrollbar.set)
        
        self.variables_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        stack_frame = ttk.Frame(debug_notebook)
        self.stack_listbox = tk.Listbox(
            stack_frame,
            font=("Consolas", 10),
            bg='#f0f0f0',
            height=8
        )
        scrollbar_stack = ttk.Scrollbar(stack_frame, orient="vertical", command=self.stack_listbox.yview)
        self.stack_listbox.configure(yscrollcommand=scrollbar_stack.set)
        
        self.stack_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_stack.pack(side=tk.RIGHT, fill=tk.Y)
        
        breakpoints_frame = ttk.Frame(debug_notebook)
        self.breakpoints_listbox = tk.Listbox(
            breakpoints_frame,
            font=("Consolas", 10),
            bg='#f0f0f0',
            height=8
        )
        scrollbar_bp = ttk.Scrollbar(breakpoints_frame, orient="vertical", command=self.breakpoints_listbox.yview)
        self.breakpoints_listbox.configure(yscrollcommand=scrollbar_bp.set)
        
        self.breakpoints_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_bp.pack(side=tk.RIGHT, fill=tk.Y)
        
        debug_notebook.add(variables_frame, text="📊 Переменные")
        debug_notebook.add(stack_frame, text="📚 Стек вызовов")
        debug_notebook.add(breakpoints_frame, text="🔴 Точки останова")
        
        git_frame = ttk.LabelFrame(right_paned, text="🐙 Git", padding=10)
        
        git_buttons_frame = tk.Frame(git_frame)
        git_buttons_frame.pack(fill=tk.X, pady=(0, 5))
        
        git_buttons = [
            ("📁 Инициализировать", self.git_init),
            ("🔄 Статус", self.git_status),
            ("💾 Коммит", self.git_commit),
            ("📚 История", self.git_history),
        ]
        
        for i, (text, command) in enumerate(git_buttons):
            btn = tk.Button(
                git_buttons_frame,
                text=text,
                command=command,
                bg='#6e40c9',
                fg='black',
                font=("Arial", 9),
                relief=tk.FLAT,
                padx=8,
                pady=4
            )
            btn.grid(row=i//2, column=i%2, padx=2, pady=2, sticky="ew")
        
        git_buttons_frame.grid_columnconfigure(0, weight=1)
        git_buttons_frame.grid_columnconfigure(1, weight=1)
        
        self.git_status_text = scrolledtext.ScrolledText(
            git_frame,
            height=6,
            font=("Consolas", 9),
            bg='#f0f0f0'
        )
        self.git_status_text.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        branch_frame = tk.Frame(git_frame)
        branch_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Label(branch_frame, text="Ветка:").pack(side=tk.LEFT)
        self.git_branch_var = tk.StringVar(value="main")
        self.branch_combo = ttk.Combobox(
            branch_frame,
            textvariable=self.git_branch_var,
            values=["main"],
            state="readonly",
            width=15
        )
        self.branch_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            branch_frame,
            text="↺",
            command=self.git_refresh,
            width=3
        ).pack(side=tk.LEFT)
        
        right_paned.add(debug_frame, weight=2)
        right_paned.add(git_frame, weight=1)
        
        main_paned.add(left_paned, weight=3)
        main_paned.add(right_paned, weight=1)
        
        events_frame = ttk.LabelFrame(self.root, text="📡 События", padding=10)
        events_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.events_listbox = tk.Listbox(
            events_frame,
            font=("Consolas", 9),
            bg='#f0f0f0',
            height=2
        )
        scrollbar_events = ttk.Scrollbar(events_frame, orient="horizontal", command=self.events_listbox.xview)
        self.events_listbox.configure(xscrollcommand=scrollbar_events.set)
        
        self.events_listbox.pack(fill=tk.X)
        scrollbar_events.pack(fill=tk.X)
        
        self.status_bar = ttk.Label(
            self.root,
            text=f"✓ Ri IDE v{self.ide_version} готов к работе. Язык Ri {RI_LANGUAGE_VERSION}. Создатель: {RI_LANGUAGE_CREATOR}, {RI_LANGUAGE_YEAR}. Нажмите F5 для запуска!",
            relief=tk.SUNKEN,
            padding=5,
            font=("Arial", 10)
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.current_file = None
        
    def setup_tags(self):
        self.code_editor.tag_configure("keyword", foreground="#569CD6", font=("Consolas", 12))
        self.code_editor.tag_configure("comment", foreground="#6A9955", font=("Consolas", 12, "italic"))
        self.code_editor.tag_configure("string", foreground="#CE9178")
        self.code_editor.tag_configure("number", foreground="#B5CEA8")
        self.code_editor.tag_configure("operator", foreground="#D4D4D4")
        self.code_editor.tag_configure("graphics", foreground="#D7BA7D")
        self.code_editor.tag_configure("events", foreground="#C586C0")
        self.code_editor.tag_configure("function", foreground="#4EC9B0")
        self.code_editor.tag_configure("list", foreground="#9CDCFE")
        
    def highlight_syntax(self, event=None):
        cursor_pos = self.code_editor.index(tk.INSERT)
        code = self.code_editor.get("1.0", tk.END)
        
        for tag in ["keyword", "comment", "string", "number", "operator", 
                   "graphics", "events", "function", "list"]:
            self.code_editor.tag_remove(tag, "1.0", tk.END)
        
        if not code:
            return
        
        lines = code.split('\n')
        pos = 0
        
        for line in lines:
            if '//' in line:
                comment_start = line.find('//')
                start = f"1.{pos + comment_start}"
                end = f"1.{pos + len(line)}"
                self.code_editor.tag_add("comment", start, end)
            
            for match in re.finditer(r'"[^"]*"', line):
                start = f"1.{pos + match.start()}"
                end = f"1.{pos + match.end()}"
                self.code_editor.tag_add("string", start, end)
            
            keywords = ['перем', 'если', 'иначе', 'цикл', 'конец', 'то', 
                       'функция', 'вызвать', 'вывести', 'ввести', 'возврат',
                       'и', 'или', 'не', 'истина', 'ложь']
            for keyword in keywords:
                pattern = r'\b' + re.escape(keyword) + r'\b'
                for match in re.finditer(pattern, line, re.IGNORECASE):
                    start = f"1.{pos + match.start()}"
                    end = f"1.{pos + match.end()}"
                    self.code_editor.tag_add("keyword", start, end)
            
            graphics_cmds = ['окно', 'прямоугольник', 'круг', 'линия', 
                           'текст', 'задержка', 'очистить', 'обновить_экран', 'остановить']
            for cmd in graphics_cmds:
                pattern = r'\b' + re.escape(cmd) + r'\b'
                for match in re.finditer(pattern, line, re.IGNORECASE):
                    start = f"1.{pos + match.start()}"
                    end = f"1.{pos + match.end()}"
                    self.code_editor.tag_add("graphics", start, end)
            
            event_cmds = ['установить_обработчик', 'мышь_х', 'мышь_у', 
                         'мышь_нажата', 'клавиша_нажата']
            for cmd in event_cmds:
                pattern = r'\b' + re.escape(cmd) + r'\b'
                for match in re.finditer(pattern, line, re.IGNORECASE):
                    start = f"1.{pos + match.start()}"
                    end = f"1.{pos + match.end()}"
                    self.code_editor.tag_add("events", start, end)
            
            builtin_funcs = ['случайно', 'длина', 'корень', 'синус', 'косинус',
                           'округлить', 'строка', 'число', 'тип', 'время',
                           'список_длина', 'элемент']
            for func in builtin_funcs:
                pattern = r'\b' + re.escape(func) + r'\b'
                for match in re.finditer(pattern, line, re.IGNORECASE):
                    start = f"1.{pos + match.start()}"
                    end = f"1.{pos + match.end()}"
                    self.code_editor.tag_add("function", start, end)
            
            list_cmds = ['список', 'добавить', 'удалить']
            for cmd in list_cmds:
                pattern = r'\b' + re.escape(cmd) + r'\b'
                for match in re.finditer(pattern, line, re.IGNORECASE):
                    start = f"1.{pos + match.start()}"
                    end = f"1.{pos + match.end()}"
                    self.code_editor.tag_add("list", start, end)
            
            for match in re.finditer(r'\b\d+(\.\d+)?\b', line):
                start = f"1.{pos + match.start()}"
                end = f"1.{pos + match.end()}"
                self.code_editor.tag_add("number", start, end)
            
            operators = ['\+', '-', '\*', '/', '=', '>', '<', '>=', '<=', '==', '!=', '\^']
            for op in operators:
                for match in re.finditer(op, line):
                    start = f"1.{pos + match.start()}"
                    end = f"1.{pos + match.end()}"
                    self.code_editor.tag_add("operator", start, end)
            
            pos += len(line) + 1
        
        self.code_editor.mark_set(tk.INSERT, cursor_pos)
    
    def insert_sample_code(self):
        sample = f"""// Ri {RI_LANGUAGE_VERSION} - Интерактивный язык программирования
// Создано программистом {RI_LANGUAGE_CREATOR} в {RI_LANGUAGE_YEAR} году
// Ri IDE v{self.ide_version} - Полнофункциональная среда разработки

// Встроенные функции
перем случайное_число = случайно(1, 100)
перем список_чисел = [10, 20, 30, 40, 50]
перем длина_списка = длина(список_чисел)

вывести "Язык Ri {RI_LANGUAGE_VERSION} от {RI_LANGUAGE_CREATOR}"
вывести "Случайное число: " + случайное_число
вывести "Длина списка: " + длина_списка

// Работа со списками
перем сумма = 0
перем i = 0

цикл i < длина_списка
    перем элемент = элемент(список_чисел, i)
    перем сумма = сумма + элемент
    вывести "Элемент [" + i + "] = " + элемент
    перем i = i + 1
конец

вывести "Сумма элементов списка: " + сумма

// Отладка: установите точку останова на следующей строке
перем результат = корень(сумма)
вывести "Корень из суммы: " + результат

// Графика с обработкой событий
окно 800 600 "Графика Ri от {RI_LANGUAGE_CREATOR}"

перем x = 400
перем y = 300
перем скорость = 5

цикл истина
    очистить светло-голубой
    
    // Управление стрелками
    если клавиша_нажата("влево") то
        перем x = x - скорость
    конец
    если клавиша_нажата("вправо") то
        перем x = x + скорость
    конец
    если клавиша_нажата("вверх") то
        перем y = y - скорость
    конец
    если клавиша_нажата("вниз") то
        перем y = y + скорость
    конец
    
    // Ограничение границ
    если x < 30 то перем x = 30 конец
    если x > 770 то перем x = 770 конец
    если y < 30 то перем y = 30 конец
    если y > 570 то перем y = 570 конец
    
    // Рисуем объект
    круг x y 30 красный
    круг x y 20 белый
    текст x y-50 "Ri {RI_LANGUAGE_VERSION}" черный
    
    // Показываем информацию
    прямоугольник 10 10 300 120 белый
    текст 160 30 "Ri IDE v{self.ide_version}" черный
    текст 160 50 "Автор: {RI_LANGUAGE_CREATOR}" черный
    текст 160 70 "X: " + x + " Y: " + y черный
    текст 160 90 "F5 - запуск, F6 - отладка" черный
    текст 160 110 "F9 - точка останова, F10 - шаг" черный
    
    // Выход по Escape
    если клавиша_нажата("эскейп") то
        остановить()
    конец
    
    обновить_экран()
    задержка 16
конец
"""
        self.code_editor.delete(1.0, tk.END)
        self.code_editor.insert(1.0, sample)
        self.highlight_syntax()
    
    def setup_shortcuts(self):
        self.root.bind('<Control-n>', lambda e: self.new_file())
        self.root.bind('<Control-o>', lambda e: self.open_file())
        self.root.bind('<Control-s>', lambda e: self.save_file())
        self.root.bind('<F5>', lambda e: self.run_code())
        self.root.bind('<F6>', lambda e: self.start_debug())
        self.root.bind('<F7>', lambda e: self.debug_pause())
        self.root.bind('<F8>', lambda e: self.debug_continue())
        self.root.bind('<F9>', lambda e: self.toggle_breakpoint())
        self.root.bind('<F10>', lambda e: self.debug_step_over())
        self.root.bind('<F11>', lambda e: self.debug_step_into())
        self.root.bind('<Shift-F11>', lambda e: self.debug_step_out())
        self.root.bind('<Return>', lambda e: self.send_input_if_active())
        self.root.bind('<Control-g>', lambda e: self.git_status())
        self.root.bind('<Control-Shift-g>', lambda e: self.git_commit())
    
    def send_input_if_active(self):
        if self.waiting_for_input and self.input_entry.get():
            self.send_input()
    
    def run_code(self):
        if self.is_running:
            messagebox.showwarning("Внимание", "Программа уже выполняется!")
            return
        
        self.is_running = True
        self.debug_mode = False
        self.is_paused = False
        self.status_bar.config(text="▶ Выполнение программы...")
        self.debug_label.config(text="Отладка: выключена", foreground="gray")
        
        self.console_output.config(state=tk.NORMAL)
        self.console_output.delete(1.0, tk.END)
        self.console_output.config(state=tk.DISABLED)
        self.events_listbox.delete(0, tk.END)
        
        self.input_frame.pack_forget()
        self.waiting_for_input = False
        
        self.line_numbers.clear_execution_line()
        self.variables_tree.delete(*self.variables_tree.get_children())
        self.stack_listbox.delete(0, tk.END)
        self.breakpoints_listbox.delete(0, tk.END)
        
        if self.graphics_window:
            self.graphics_window.close()
            self.graphics_window = None
        
        code = self.code_editor.get(1.0, tk.END)
        
        thread = threading.Thread(target=self.execute_code, args=(code,))
        thread.daemon = True
        thread.start()
    
    def start_debug(self):
        if self.is_running:
            messagebox.showwarning("Внимание", "Программа уже выполняется!")
            return
        
        self.is_running = True
        self.debug_mode = True
        self.is_paused = False
        self.status_bar.config(text="🔍 Запуск в режиме отладки...")
        self.debug_label.config(text="Отладка: включена", foreground="green")
        
        self.console_output.config(state=tk.NORMAL)
        self.console_output.delete(1.0, tk.END)
        self.console_output.config(state=tk.DISABLED)
        self.events_listbox.delete(0, tk.END)
        
        self.input_frame.pack_forget()
        self.waiting_for_input = False
        
        self.line_numbers.clear_execution_line()
        self.variables_tree.delete(*self.variables_tree.get_children())
        self.stack_listbox.delete(0, tk.END)
        self.breakpoints_listbox.delete(0, tk.END)
        
        if self.graphics_window:
            self.graphics_window.close()
            self.graphics_window = None
        
        code = self.code_editor.get(1.0, tk.END)
        
        thread = threading.Thread(target=self.execute_code, args=(code,))
        thread.daemon = True
        thread.start()
    
    def execute_code(self, code):
        try:
            def graphics_callback(commands):
                self.graphics_queue.put(commands)
            
            def input_callback(type, prompt):
                if type == "input":
                    self.output_queue.put(("input_request", prompt))
                    return self.input_queue.get()
                return ""
            
            def event_callback(type, data=""):
                if type == "get_mouse_x":
                    if self.graphics_window:
                        return self.graphics_window.get_mouse_x()
                    return 0
                elif type == "get_mouse_y":
                    if self.graphics_window:
                        return self.graphics_window.get_mouse_y()
                    return 0
                elif type == "get_mouse_pressed":
                    if self.graphics_window:
                        return self.graphics_window.get_mouse_pressed()
                    return False
                elif type == "get_key_pressed":
                    if self.graphics_window:
                        return self.graphics_window.get_key_pressed(data)
                    return False
                elif type == "set_handler":
                    parts = data.split(":")
                    if len(parts) == 2:
                        event_type, handler = parts
                        self.event_handlers[event_type] = handler
                return ""
            
            def debug_callback(type, data=""):
                self.debug_queue.put((type, data))
            
            result = run_ri_code(
                code, 
                graphics_callback, 
                input_callback, 
                event_callback,
                debug_callback if self.debug_mode else None
            )
            
            if result:
                self.output_queue.put(("output", "\n" + result))
            
            self.output_queue.put(("status", "✓ Выполнение завершено"))
            self.debug_queue.put(("program_finished", ""))
            
        except Exception as e:
            self.output_queue.put(("error", f"Ошибка выполнения: {str(e)}"))
            self.output_queue.put(("status", f"✗ Ошибка: {str(e)}"))
            self.debug_queue.put(("error", f"Ошибка выполнения: {str(e)}"))
        finally:
            self.is_running = False
            self.debug_mode = False
            self.is_paused = False
    
    def process_queue(self):
        try:
            while not self.output_queue.empty():
                msg_type, data = self.output_queue.get_nowait()
                
                if msg_type == "output":
                    self.console_output.config(state=tk.NORMAL)
                    self.console_output.insert(tk.END, data + "\n")
                    self.console_output.see(tk.END)
                    self.console_output.config(state=tk.DISABLED)
                    
                elif msg_type == "error":
                    self.console_output.config(state=tk.NORMAL)
                    self.console_output.insert(tk.END, "❌ ОШИБКА: " + data + "\n")
                    self.console_output.see(tk.END)
                    self.console_output.config(state=tk.DISABLED)
                    
                elif msg_type == "input_request":
                    self.waiting_for_input = True
                    self.current_input_prompt = data
                    
                    self.input_prompt.config(text=data)
                    self.input_entry.delete(0, tk.END)
                    self.input_frame.pack(fill=tk.X, pady=5)
                    self.input_entry.focus()
                    
                    self.console_output.config(state=tk.NORMAL)
                    self.console_output.insert(tk.END, data + " ", "prompt")
                    self.console_output.see(tk.END)
                    self.console_output.config(state=tk.DISABLED)
                    
                elif msg_type == "status":
                    self.status_bar.config(text=data)
        
        except Exception as e:
            pass
        
        self.root.after(100, self.process_queue)
    
    def process_graphics_queue(self):
        try:
            while not self.graphics_queue.empty():
                commands = self.graphics_queue.get_nowait()
                
                for command in commands:
                    cmd_type = command[0]
                    
                    if cmd_type == 'window':
                        _, width, height, title = command
                        if self.graphics_window:
                            self.graphics_window.close()
                        self.graphics_window = GraphicsWindow(width, height, title, self)
                        
                    elif cmd_type == 'clear' and self.graphics_window:
                        _, color = command
                        self.graphics_window.clear(color)
                        
                    elif cmd_type == 'rectangle' and self.graphics_window:
                        _, x, y, width, height, color = command
                        self.graphics_window.draw_rectangle(x, y, width, height, color)
                        
                    elif cmd_type == 'circle' and self.graphics_window:
                        _, x, y, radius, color = command
                        self.graphics_window.draw_circle(x, y, radius, color)
                        
                    elif cmd_type == 'line' and self.graphics_window:
                        _, x1, y1, x2, y2, color = command
                        self.graphics_window.draw_line(x1, y1, x2, y2, color)
                        
                    elif cmd_type == 'text' and self.graphics_window:
                        _, x, y, text, color = command
                        self.graphics_window.draw_text(x, y, text, color)
                        
                    elif cmd_type == 'update' and self.graphics_window:
                        self.graphics_window.update_screen()
                
                if self.graphics_window:
                    self.graphics_window.window.update()
        
        except Exception as e:
            pass
        
        self.root.after(50, self.process_graphics_queue)
    
    def process_events(self):
        try:
            while not self.event_queue.empty():
                event = self.event_queue.get_nowait()
                event_type = event[0]
                
                if self.graphics_window:
                    self.mouse_label.config(
                        text=f"Мышь: ({self.graphics_window.mouse_x}, {self.graphics_window.mouse_y}) " +
                             f"{'Нажата' if self.graphics_window.mouse_pressed else 'Не нажата'}"
                    )
                    
                    keys_text = "Клавиши: " + ", ".join(sorted(self.graphics_window.keys_pressed))
                    if len(keys_text) > 50:
                        keys_text = keys_text[:47] + "..."
                    self.key_label.config(text=keys_text)
                
                event_str = str(event)
                self.events_listbox.insert(0, event_str)
                if self.events_listbox.size() > 10:
                    self.events_listbox.delete(10, tk.END)
        
        except Exception as e:
            pass
        
        self.root.after(50, self.process_events)
    
    def process_debug_queue(self):
        try:
            while not self.debug_queue.empty():
                msg_type, data = self.debug_queue.get_nowait()
                
                if msg_type == "line_executed":
                    self.current_debug_line = data
                    self.line_numbers.set_execution_line(data)
                    
                elif msg_type == "breakpoint_hit":
                    self.is_paused = True
                    self.current_debug_line = data
                    self.line_numbers.set_execution_line(data)
                    self.status_bar.config(text=f"🔴 Остановлено на точке останова в строке {data}")
                    
                elif msg_type == "step_hit":
                    self.is_paused = True
                    self.current_debug_line = data
                    self.line_numbers.set_execution_line(data)
                    self.status_bar.config(text=f"⏸ Остановлено в строке {data} для пошагового выполнения")
                    
                elif msg_type == "variables_updated":
                    self.variables_tree.delete(*self.variables_tree.get_children())
                    
                    for var_name, var_value in data.items():
                        var_type = type(var_value).__name__
                        if var_type == 'int':
                            var_type = "целое"
                        elif var_type == 'float':
                            var_type = "дробное"
                        elif var_type == 'str':
                            var_type = "строка"
                        elif var_type == 'bool':
                            var_type = "булево"
                        else:
                            var_type = str(var_type)
                        
                        self.variables_tree.insert('', 'end', text=var_name, 
                                                 values=(str(var_value), var_type))
                    
                elif msg_type == "call_stack_updated":
                    self.stack_listbox.delete(0, tk.END)
                    self.call_stack = data
                    
                    for item in data:
                        self.stack_listbox.insert(0, item)
                    
                elif msg_type == "program_stopped":
                    self.status_bar.config(text="■ Программа остановлена пользователем")
                    
                elif msg_type == "program_finished":
                    self.line_numbers.clear_execution_line()
                    self.status_bar.config(text="✓ Отладка завершена")
                    self.debug_label.config(text="Отладка: завершена", foreground="gray")
                    
                elif msg_type == "error":
                    self.status_bar.config(text=f"✗ Ошибка отладки: {data}")
        
        except Exception as e:
            pass
        
        self.root.after(100, self.process_debug_queue)
    
    def send_input(self):
        if not self.waiting_for_input:
            return
        
        user_input = self.input_entry.get().strip()
        if user_input:
            self.input_frame.pack_forget()
            self.waiting_for_input = False
            
            self.input_queue.put(user_input)
            
            self.console_output.config(state=tk.NORMAL)
            self.console_output.insert(tk.END, user_input + "\n")
            self.console_output.see(tk.END)
            self.console_output.config(state=tk.DISABLED)
            
            self.input_entry.delete(0, tk.END)
    
    def debug_continue(self):
        if self.debug_mode and self.is_paused:
            self.is_paused = False
            self.status_bar.config(text="▶ Продолжение выполнения...")
    
    def debug_pause(self):
        if self.debug_mode and self.is_running and not self.is_paused:
            self.is_paused = True
            self.status_bar.config(text="⏸ Выполнение приостановлено")
    
    def debug_step_over(self):
        if self.debug_mode and self.is_paused:
            self.is_paused = False
            self.status_bar.config(text="➡ Шаг вперед...")
    
    def debug_step_into(self):
        if self.debug_mode and self.is_paused:
            self.is_paused = False
            self.status_bar.config(text="⬇ Шаг внутрь...")
    
    def debug_step_out(self):
        if self.debug_mode and self.is_paused:
            self.is_paused = False
            self.status_bar.config(text="⬆ Шаг наружу...")
    
    def debug_stop(self):
        self.stop_execution()
    
    def toggle_breakpoint(self):
        if self.is_running:
            messagebox.showwarning("Внимание", "Нельзя изменять точки останова во время выполнения программы!")
            return
        
        cursor_pos = self.code_editor.index(tk.INSERT)
        line_num = int(cursor_pos.split('.')[0])
        
        if line_num in self.line_numbers.breakpoints:
            self.line_numbers.breakpoints.remove(line_num)
            self.status_bar.config(text=f"✓ Точка останова удалена в строке {line_num}")
        else:
            self.line_numbers.breakpoints.add(line_num)
            self.status_bar.config(text=f"✓ Точка останова установлена в строке {line_num}")
        
        self.line_numbers._redraw()
        self.breakpoints_listbox.delete(0, tk.END)
        for bp in sorted(self.line_numbers.breakpoints):
            self.breakpoints_listbox.insert(tk.END, f"Строка {bp}")
    
    def clear_all_breakpoints(self):
        if self.is_running:
            messagebox.showwarning("Внимание", "Нельзя изменять точки останова во время выполнения программы!")
            return
        
        self.line_numbers.breakpoints.clear()
        self.line_numbers._redraw()
        self.breakpoints_listbox.delete(0, tk.END)
        self.status_bar.config(text="✓ Все точки останова очищены")
    
    def git_init(self):
        if not self.current_project_path:
            messagebox.showwarning("Внимание", "Сначала создайте или откройте проект!")
            return
        
        if self.git_integration:
            if messagebox.askyesno("Подтверждение", "Git уже инициализирован. Переинициализировать?"):
                pass
            else:
                return
        
        try:
            git_dir = os.path.join(self.current_project_path, '.git')
            if os.path.exists(git_dir):
                import shutil
                shutil.rmtree(git_dir)
            
            self.git_integration = GitIntegration(self.current_project_path)
            if self.git_integration.init_repository():
                gitignore_path = os.path.join(self.current_project_path, '.gitignore')
                with open(gitignore_path, 'w', encoding='utf-8') as f:
                    f.write("# Ri IDE\n*.pyc\n__pycache__/\n*.riproj\n")
                
                readme_path = os.path.join(self.current_project_path, 'README.md')
                if not os.path.exists(readme_path):
                    with open(readme_path, 'w', encoding='utf-8') as f:
                        f.write(f"# Ri Project\n\nСоздано в Ri IDE v{self.ide_version} от {RI_LANGUAGE_CREATOR}\n")
                
                self.git_integration.commit_changes("Initial commit")
                
                self.git_label.config(text="Git: инициализирован", foreground="green")
                self.status_bar.config(text="✓ Git репозиторий инициализирован")
                self.git_refresh()
            else:
                messagebox.showerror("Ошибка", "Не удалось инициализировать Git репозиторий")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при инициализации Git: {str(e)}")
    
    def git_status(self):
        if not self.git_integration:
            messagebox.showwarning("Внимание", "Git не инициализирован!")
            return
        
        try:
            status = self.git_integration.get_status()
            branches, current_branch = self.git_integration.get_branches()
            
            self.git_status_text.delete(1.0, tk.END)
            
            if current_branch:
                self.git_status_text.insert(tk.END, f"Текущая ветка: {current_branch}\n\n")
            
            if status:
                self.git_status_text.insert(tk.END, "Измененные файлы:\n")
                for item in status:
                    self.git_status_text.insert(tk.END, f"  {item}\n")
            else:
                self.git_status_text.insert(tk.END, "Нет измененных файлов\n")
            
            if branches:
                self.branch_combo['values'] = branches
                if current_branch:
                    self.git_branch_var.set(current_branch)
            
            self.status_bar.config(text="✓ Статус Git обновлен")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при получении статуса Git: {str(e)}")
    
    def git_commit(self):
        if not self.git_integration:
            messagebox.showwarning("Внимание", "Git не инициализирован!")
            return
        
        commit_dialog = tk.Toplevel(self.root)
        commit_dialog.title("Создание коммита")
        commit_dialog.geometry("400x200")
        commit_dialog.transient(self.root)
        commit_dialog.grab_set()
        
        tk.Label(commit_dialog, text="Введите сообщение коммита:", font=("Arial", 11)).pack(pady=10)
        
        commit_message = tk.Text(commit_dialog, height=5, width=40, font=("Arial", 10))
        commit_message.pack(pady=10, padx=20)
        commit_message.insert(1.0, "Обновление кода")
        commit_message.focus()
        
        def do_commit():
            message = commit_message.get(1.0, tk.END).strip()
            if message:
                try:
                    if self.git_integration.commit_changes(message):
                        self.git_status()
                        self.status_bar.config(text=f"✓ Коммит создан: {message}")
                        commit_dialog.destroy()
                    else:
                        messagebox.showerror("Ошибка", "Не удалось создать коммит")
                except Exception as e:
                    messagebox.showerror("Ошибка", f"Ошибка при создании коммита: {str(e)}")
        
        button_frame = tk.Frame(commit_dialog)
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="Создать коммит", command=do_commit, 
                 bg='#4CAF50', fg='black', padx=20).pack(side=tk.LEFT, padx=10)
        tk.Button(button_frame, text="Отмена", command=commit_dialog.destroy,
                 bg='#f44336', fg='black', padx=20).pack(side=tk.LEFT)
    
    def git_history(self):
        if not self.git_integration:
            messagebox.showwarning("Внимание", "Git не инициализирован!")
            return
        
        try:
            history = self.git_integration.get_history(20)
            
            history_dialog = tk.Toplevel(self.root)
            history_dialog.title("История коммитов")
            history_dialog.geometry("600x400")
            
            text = scrolledtext.ScrolledText(history_dialog, wrap=tk.WORD, font=("Consolas", 10))
            text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            if history:
                text.insert(tk.END, "Последние 20 коммитов:\n\n")
                for i, commit in enumerate(history, 1):
                    text.insert(tk.END, f"{i}. {commit}\n")
            else:
                text.insert(tk.END, "История коммитов пуста\n")
            
            text.config(state=tk.DISABLED)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при получении истории Git: {str(e)}")
    
    def git_branches(self):
        if not self.git_integration:
            messagebox.showwarning("Внимание", "Git не инициализирован!")
            return
        
        branches_dialog = tk.Toplevel(self.root)
        branches_dialog.title("Управление ветками Git")
        branches_dialog.geometry("400x300")
        branches_dialog.transient(self.root)
        
        try:
            branches, current_branch = self.git_integration.get_branches()
            
            tk.Label(branches_dialog, text="Текущая ветка:", font=("Arial", 11, "bold")).pack(pady=10)
            tk.Label(branches_dialog, text=current_branch or "не определена", 
                    font=("Arial", 11), fg="blue").pack()
            
            tk.Label(branches_dialog, text="\nВсе ветки:", font=("Arial", 11, "bold")).pack(pady=10)
            
            listbox = tk.Listbox(branches_dialog, height=8, font=("Arial", 10))
            scrollbar = tk.Scrollbar(branches_dialog)
            
            listbox.config(yscrollcommand=scrollbar.set)
            scrollbar.config(command=listbox.yview)
            
            for branch in branches:
                listbox.insert(tk.END, branch)
            
            listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 10))
            
            def switch_branch():
                selection = listbox.curselection()
                if selection:
                    branch_name = listbox.get(selection[0])
                    if branch_name != current_branch:
                        if self.git_integration.checkout_branch(branch_name):
                            self.git_status()
                            self.status_bar.config(text=f"✓ Переключено на ветку: {branch_name}")
                            branches_dialog.destroy()
                        else:
                            messagebox.showerror("Ошибка", f"Не удалось переключиться на ветку {branch_name}")
            
            def create_branch():
                new_branch = tk.simpledialog.askstring("Новая ветка", "Введите имя новой ветки:")
                if new_branch:
                    if self.git_integration.create_branch(new_branch):
                        branches.append(new_branch)
                        listbox.insert(tk.END, new_branch)
                        self.status_bar.config(text=f"✓ Создана ветка: {new_branch}")
                    else:
                        messagebox.showerror("Ошибка", f"Не удалось создать ветку {new_branch}")
            
            button_frame = tk.Frame(branches_dialog)
            button_frame.pack(pady=10)
            
            tk.Button(button_frame, text="Переключиться", command=switch_branch,
                     bg='#2196F3', fg='black').pack(side=tk.LEFT, padx=5)
            tk.Button(button_frame, text="Создать ветку", command=create_branch,
                     bg='#4CAF50', fg='black').pack(side=tk.LEFT, padx=5)
            tk.Button(button_frame, text="Закрыть", command=branches_dialog.destroy,
                     bg='#f44336', fg='black').pack(side=tk.LEFT, padx=5)
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при работе с ветками Git: {str(e)}")
            branches_dialog.destroy()
    
    def git_refresh(self):
        if self.git_integration:
            self.git_status()
    
    def create_project(self):
        project_path = filedialog.askdirectory(title="Выберите папку для проекта")
        if project_path:
            try:
                project_name = os.path.basename(project_path)
                
                project_file = os.path.join(project_path, f"{project_name}.riproj")
                with open(project_file, 'w', encoding='utf-8') as f:
                    project_data = {
                        "name": project_name,
                        "created": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "ide_version": self.ide_version,
                        "language_version": RI_LANGUAGE_VERSION,
                        "creator": RI_LANGUAGE_CREATOR,
                        "year": RI_LANGUAGE_YEAR,
                        "files": ["main.ri"]
                    }
                    json.dump(project_data, f, indent=2, ensure_ascii=False)
                
                main_file = os.path.join(project_path, "main.ri")
                with open(main_file, 'w', encoding='utf-8') as f:
                    f.write(f"// {project_name}\n// Создано в Ri IDE v{self.ide_version} от {RI_LANGUAGE_CREATOR}\n\n")
                    f.write(self.code_editor.get(1.0, tk.END))
                
                self.current_project_path = project_path
                self.git_integration = None
                self.git_label.config(text="Git: не инициализирован", foreground="gray")
                
                self.code_editor.delete(1.0, tk.END)
                with open(main_file, 'r', encoding='utf-8') as f:
                    self.code_editor.insert(1.0, f.read())
                
                self.highlight_syntax()
                self.status_bar.config(text=f"✓ Проект '{project_name}' создан в {project_path}")
                
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось создать проект: {str(e)}")
    
    def open_project(self):
        project_file = filedialog.askopenfilename(
            title="Открыть проект",
            filetypes=[("Ri проекты", "*.riproj"), ("Все файлы", "*.*")]
        )
        
        if project_file:
            try:
                with open(project_file, 'r', encoding='utf-8') as f:
                    project_data = json.load(f)
                
                project_path = os.path.dirname(project_file)
                self.current_project_path = project_path
                
                if os.path.exists(os.path.join(project_path, '.git')):
                    self.git_integration = GitIntegration(project_path)
                    branches, current_branch = self.git_integration.get_branches()
                    if current_branch:
                        self.git_label.config(text=f"Git: {current_branch}", foreground="green")
                    else:
                        self.git_label.config(text="Git: инициализирован", foreground="green")
                else:
                    self.git_integration = None
                    self.git_label.config(text="Git: не инициализирован", foreground="gray")
                
                main_file = os.path.join(project_path, "main.ri")
                if os.path.exists(main_file):
                    with open(main_file, 'r', encoding='utf-8') as f:
                        self.code_editor.delete(1.0, tk.END)
                        self.code_editor.insert(1.0, f.read())
                
                self.highlight_syntax()
                self.status_bar.config(text=f"✓ Проект '{project_data['name']}' загружен")
                
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось открыть проект: {str(e)}")
    
    def open_graphics_window(self):
        if not self.graphics_window:
            self.graphics_window = GraphicsWindow(ide=self)
        else:
            self.graphics_window.window.lift()
    
    def clear_graphics(self):
        if self.graphics_window:
            self.graphics_window.clear()
    
    def insert_draw_example(self):
        example = f"""// Пример: Интерактивная рисовалка
// Создано программистом {RI_LANGUAGE_CREATOR} в {RI_LANGUAGE_YEAR} году

окно 800 600 "Рисовалка Ri"

перем цвет = "черный"
перем размер = 5
перем рисовать = ложь
перем последний_х = 0
перем последний_у = 0

очистить белый
текст 300 30 "Рисуй мышью! Ri IDE от {RI_LANGUAGE_CREATOR}" черный

цикл истина
    перем х = мышь_х()
    перем у = мышь_у()
    
    если мышь_нажата() то
        если не рисовать то
            перем рисовать = истина
            перем последний_х = х
            перем последний_у = у
        конец
        
        линия последний_х последний_у х у цвет
        перем последний_х = х
        перем последний_у = у
    иначе
        перем рисовать = ложь
    конец
    
    если клавиша_нажата("1") то
        перем цвет = "черный"
    конец
    если клавиша_нажата("2") то
        перем цвет = "красный"
    конец
    если клавиша_нажата("3") то
        перем цвет = "синий"
    конец
    если клавиша_нажата("4") то
        перем цвет = "зеленый"
    конец
    
    если клавиша_нажата("пробел") то
        очистить белый
        текст 300 30 "Рисуй мышью! Ri IDE от {RI_LANGUAGE_CREATOR}" черный
    конец
    
    если клавиша_нажата("эскейп") то
        остановить()
    конец
    
    обновить_экран()
    задержка 16
конец
"""
        self.code_editor.delete(1.0, tk.END)
        self.code_editor.insert(1.0, example)
        self.highlight_syntax()
        self.status_bar.config(text="✓ Пример 'Рисовалка' загружен")
    
    def insert_target_example(self):
        example = f"""// Пример: Игра "Стрельба по мишеням"
// Создано программистом {RI_LANGUAGE_CREATOR} в {RI_LANGUAGE_YEAR} году

окно 800 600 "Стрельба по мишеням"

перем счет = 0
перем мишени = [300, 200, 100, 400, 250]
перем радиусы = [30, 40, 35, 45, 25]
перем цвета = ["красный", "синий", "зеленый", "фиолетовый", "оранжевый"]
перем скорость = 3

цикл истина
    очистить светло-голубой
    
    перем i = 0
    цикл i < длина(мишени)
        перем x = мишени[i]
        перем y = радиусы[i] * 2
        
        перем x = x + скорость
        если x > 800 то
            перем x = 0
        конец
        мишени[i] = x
        
        круг x 100 радиусы[i] цвета[i]
        круг x 100 радиусы[i]-5 белый
        
        перем i = i + 1
    конец
    
    перем х = мышь_х()
    перем у = мышь_у()
    
    круг х у 10 черный
    линия х-15 у х+15 у красный
    линия х у-15 х у+15 красный
    
    если мышь_нажата() то
        перем i = 0
        цикл i < длина(мишени)
            перем мишень_x = мишени[i]
            перем расстояние = корень((х - мишень_x)^2 + (у - 100)^2)
            
            если расстояние < радиусы[i] то
                перем счет = счет + 1
                мишени[i] = 900
            конец
            
            перем i = i + 1
        конец
        
        задержка 200
    конец
    
    прямоугольник 10 10 200 60 белый
    текст 110 30 "Счет: " + счет черный
    текст 110 50 "Ri IDE от {RI_LANGUAGE_CREATOR}" черный
    
    если клавиша_нажата("эскейп") то
        остановить()
    конец
    
    обновить_экран()
    задержка 16
конец
"""
        self.code_editor.delete(1.0, tk.END)
        self.code_editor.insert(1.0, example)
        self.highlight_syntax()
        self.status_bar.config(text="✓ Пример 'Стрельба по мишеням' загружен")
    
    def insert_keyboard_example(self):
        example = f"""// Пример: Управление объектом клавиатурой
// Создано программистом {RI_LANGUAGE_CREATOR} в {RI_LANGUAGE_YEAR} году

окно 800 600 "Управление клавиатурой"

перем x = 400
перем y = 300
перем скорость = 5
перем цвет = "красный"

очистить белый
текст 300 30 "Ri IDE от {RI_LANGUAGE_CREATOR} - Управление клавиатурой" черный

цикл истина
    очистить белый
    текст 300 30 "Ri IDE от {RI_LANGUAGE_CREATOR} - Управление клавиатурой" черный
    
    если клавиша_нажата("влево") то
        перем x = x - скорость
    конец
    если клавиша_нажата("вправо") то
        перем x = x + скорость
    конец
    если клавиша_нажата("вверх") то
        перем y = y - скорость
    конец
    если клавиша_нажата("вниз") то
        перем y = y + скорость
    конец
    
    если клавиша_нажата("пробел") то
        перем y = y - 50
        задержка 100
        перем y = y + 50
    конец
    
    если клавиша_нажата("1") то
        перем цвет = "красный"
    конец
    если клавиша_нажата("2") то
        перем цвет = "синий"
    конец
    если клавиша_нажата("3") то
        перем цвет = "зеленый"
    конец
    если клавиша_нажата("4") то
        перем цвет = "желтый"
    конец
    
    если x < 50 то
        перем x = 50
    конец
    если x > 750 то
        перем x = 750
    конец
    если y < 50 то
        перем y = 50
    конец
    если y > 550 то
        перем y = 550
    конец
    
    круг x y 30 цвет
    круг x-10 y-10 5 черный
    круг x+10 y-10 5 черный
    
    прямоугольник 10 10 200 80 светло-голубой
    текст 110 30 "X: " + x черный
    текст 110 50 "Y: " + y черный
    текст 110 70 "Автор: {RI_LANGUAGE_CREATOR}" черный
    
    если клавиша_нажата("эскейп") то
        остановить()
    конец
    
    обновить_экран()
    задержка 16
конец
"""
        self.code_editor.delete(1.0, tk.END)
        self.code_editor.insert(1.0, example)
        self.highlight_syntax()
        self.status_bar.config(text="✓ Пример 'Управление клавиатурой' загружен")
    
    def insert_car_example(self):
        example = f"""// Пример: Вождение машинки
// Создано программистом {RI_LANGUAGE_CREATOR} в {RI_LANGUAGE_YEAR} году

окно 800 600 "Вождение машинки"

перем x = 400
перем y = 500
перем скорость = 0
перем поворот = 0

очистить светло-зеленый

цикл истина
    прямоугольник 200 0 400 600 серый
    
    перем i = 0
    цикл i < 12
        прямоугольник 390 i*50 20 30 желтый
        перем i = i + 1
    конец
    
    если клавиша_нажата("влево") то
        перем поворот = поворот - 2
    конец
    если клавиша_нажата("вправо") то
        перем поворот = поворот + 2
    конец
    если клавиша_нажата("вверх") то
        перем скорость = скорость + 0.2
    конец
    если клавиша_нажата("вниз") то
        перем скорость = скорость - 0.2
    конец
    
    если клавиша_нажата("пробел") то
        перем скорость = скорость * 0.9
    конец
    
    если скорость > 10 то
        перем скорость = 10
    конец
    если скорость < -3 то
        перем скорость = -3
    конец
    если поворот > 30 то
        перем поворот = 30
    конец
    если поворот < -30 то
        перем поворот = -30
    конец
    
    перем x = x + скорость * синус(поворот)
    перем y = y - скорость * косинус(поворот)
    
    если x < 250 то
        перем x = 250
        перем скорость = скорость * 0.5
    конец
    если x > 550 то
        перем x = 550
        перем скорость = скорость * 0.5
    конец
    если y < 0 то
        перем y = 600
    конец
    если y > 600 то
        перем y = 0
    конец
    
    прямоугольник x-30 y-15 60 30 красный
    прямоугольник x-40 y+15 80 10 темно-серый
    круг x-25 y+25 10 черный
    круг x+25 y+25 10 черный
    
    прямоугольник x-20 y-10 40 10 голубой
    
    если скорость > 0 то
        круг x+35 y 5 желтый
    конец
    если скорость < 0 то
        круг x-35 y 5 желтый
    конец
    
    прямоугольник 10 10 200 100 белый
    текст 110 30 "Скорость: " + округлить(скорость, 1) черный
    текст 110 50 "Поворот: " + округлить(поворот, 1) черный
    текст 110 70 "Автор: {RI_LANGUAGE_CREATOR}" черный
    
    если клавиша_нажата("эскейп") то
        остановить()
    конец
    
    перем поворот = поворот * 0.95
    
    обновить_экран()
    задержка 16
конец
"""
        self.code_editor.delete(1.0, tk.END)
        self.code_editor.insert(1.0, example)
        self.highlight_syntax()
        self.status_bar.config(text="✓ Пример 'Вождение машинки' загружен")
    
    def new_file(self):
        self.code_editor.delete(1.0, tk.END)
        self.current_file = None
        self.status_bar.config(text="✓ Новый файл создан")
        self.highlight_syntax()
    
    def open_file(self):
        filename = filedialog.askopenfilename(
            defaultextension=".ri",
            filetypes=[("Ri файлы", "*.ri"), ("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")]
        )
        if filename:
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    content = f.read()
                self.code_editor.delete(1.0, tk.END)
                self.code_editor.insert(1.0, content)
                self.current_file = filename
                self.status_bar.config(text=f"✓ Открыт файл: {filename}")
                self.highlight_syntax()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось открыть файл:\n{str(e)}")
    
    def save_file(self):
        if not self.current_file:
            self.save_as_file()
        else:
            try:
                with open(self.current_file, "w", encoding="utf-8") as f:
                    f.write(self.code_editor.get(1.0, tk.END))
                self.status_bar.config(text=f"✓ Файл сохранен: {self.current_file}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{str(e)}")
    
    def save_as_file(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".ri",
            filetypes=[("Ri файлы", "*.ri"), ("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")]
        )
        if filename:
            self.current_file = filename
            self.save_file()
    
    def stop_execution(self):
        self.is_running = False
        self.debug_mode = False
        self.is_paused = False
        self.input_frame.pack_forget()
        self.waiting_for_input = False
        self.status_bar.config(text="■ Выполнение остановлено")
        self.debug_label.config(text="Отладка: выключена", foreground="gray")
        self.line_numbers.clear_execution_line()
    
    def clear_console(self):
        self.console_output.config(state=tk.NORMAL)
        self.console_output.delete(1.0, tk.END)
        self.console_output.config(state=tk.DISABLED)
    
    def show_help(self):
        help_window = tk.Toplevel(self.root)
        help_window.title(f"Справка по языку Ri {RI_LANGUAGE_VERSION}")
        help_window.geometry("800x600")
        
        text = scrolledtext.ScrolledText(help_window, wrap=tk.WORD, font=("Arial", 11))
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        content = f"""Ri {RI_LANGUAGE_VERSION} - Интерактивный язык программирования!
Создано программистом {RI_LANGUAGE_CREATOR} в {RI_LANGUAGE_YEAR} году
Ri IDE v{self.ide_version} - Полнофункциональная среда разработки

ВОЗМОЖНОСТИ:

1. ОТЛАДКА:
   • F6 - Запуск в режиме отладки
   • F9 - Установить/снять точку останова
   • F10 - Шаг вперед
   • F11 - Шаг внутрь функции
   • Shift+F11 - Шаг наружу
   • F7 - Пауза
   • F8 - Продолжить

2. ВСТРОЕННЫЕ ФУНКЦИИ:
   • случайно(min, max) - случайное число
   • длина(value) - длина строки или списка
   • корень(value) - квадратный корень
   • синус(value), косинус(value) - тригонометрия
   • округлить(value, decimals) - округление
   • строка(value), число(value) - преобразование типов
   • тип(value) - тип переменной
   • время() - текущее время

3. СПИСКИ:
   • список имя = [1, 2, 3] - создание списка
   • добавить(имя_списка, значение) - добавление элемента
   • удалить(имя_списка, индекс) - удаление элемента
   • элемент(имя_списка, индекс) - доступ к элементу

4. ОБРАБОТКА СОБЫТИЙ:
   • мышь_х(), мышь_у() - координаты мыши
   • мышь_нажата() - состояние левой кнопки
   • клавиша_нажата("код") - проверка нажатия клавиши

5. ГРАФИКА:
   • окно ширина высота "заголовок"
   • прямоугольник x y ширина высота цвет
   • круг x y радиус цвет
   • линия x1 y1 x2 y2 цвет
   • текст x y "текст" цвет
   • очистить цвет
   • обновить_экран()

6. GIT ИНТЕГРАЦИЯ:
   • Создание проектов с метаданными
   • Инициализация Git репозиториев
   • Коммиты, ветки, история
   • Управление версиями кода

ПРИМЕР:
окно 800 600 "Игра"
перем х = мышь_х()
перем у = мышь_у()

если мышь_нажата() то
    круг х у 20 красный
конец

обновить_экран()
"""
        text.insert(1.0, content)
        text.config(state=tk.DISABLED)
    
    def show_mouse_help(self):
        messagebox.showinfo(
            "События мыши",
            "🖱️ ОБРАБОТКА МЫШИ В Ri:\n\n"
            "1. мышь_х() - координата X курсора мыши\n"
            "2. мышь_у() - координата Y курсора мыши\n"
            "3. мышь_нажата() - нажата ли левая кнопка мыши\n\n"
            "ПРИМЕР:\n"
            "цикл истина\n"
            "    перем х = мышь_х()\n"
            "    перем у = мышь_у()\n"
            "    \n"
            "    если мышь_нажата() то\n"
            "        круг х у 10 красный\n"
            "    конец\n"
            "конец"
        )
    
    def show_keyboard_help(self):
        messagebox.showinfo(
            "Коды клавиш",
            "⌨️ КОДЫ КЛАВИШ В Ri:\n\n"
            "БУКВЫ И ЦИФРЫ:\n"
            "\"a\", \"b\", \"c\", ... \"z\"\n"
            "\"1\", \"2\", \"3\", ... \"0\"\n\n"
            "СПЕЦИАЛЬНЫЕ КЛАВИШИ:\n"
            "\"пробел\" - пробел\n"
            "\"ввод\" - Enter\n"
            "\"эскейп\" - Escape\n"
            "\"таб\" - Tab\n"
            "\"бэкспейс\" - Backspace\n\n"
            "СТРЕЛКИ:\n"
            "\"влево\", \"вправо\", \"вверх\", \"вниз\"\n\n"
            "ФУНКЦИОНАЛЬНЫЕ КЛАВИШИ:\n"
            "\"ф1\", \"ф2\", ... \"ф12\"\n\n"
            "ПРИМЕР:\n"
            "если клавиша_нажата(\"влево\") то\n"
            "    перем x = x - 5\n"
            "конец"
        )
    
    def show_debug_help(self):
        messagebox.showinfo(
            "Отладка в Ri IDE",
            f"🐛 ОТЛАДКА В Ri IDE v{self.ide_version}:\n\n"
            "ГОРЯЧИЕ КЛАВИШИ:\n"
            "F5 - Запуск программы\n"
            "F6 - Запуск в режиме отладки\n"
            "F7 - Пауза выполнения\n"
            "F8 - Продолжить выполнение\n"
            "F9 - Установить/снять точку останова\n"
            "F10 - Шаг вперед (не заходя в функции)\n"
            "F11 - Шаг внутрь функции\n"
            "Shift+F11 - Шаг наружу из функции\n\n"
            "КАК РАБОТАТЬ С ОТЛАДКОЙ:\n"
            "1. Установите точки останова (клик на номере строки)\n"
            "2. Нажмите F6 для запуска в режиме отладки\n"
            "3. Используйте F10/F11 для пошагового выполнения\n"
            "4. Смотрите переменные в панели отладки\n"
            "5. Используйте F8 для продолжения до следующей точки останова\n\n"
            "ПАНЕЛЬ ОТЛАДКИ:\n"
            "• Переменные - текущие значения переменных\n"
            "• Стек вызовов - текущая цепочка вызовов\n"
            "• Точки останова - список установленных точек останова"
        )
    
    def show_git_help(self):
        messagebox.showinfo(
            "Git в Ri IDE",
            "🐙 GIT ИНТЕГРАЦИЯ В Ri IDE:\n\n"
            "ВОЗМОЖНОСТИ:\n"
            "• Создание и управление проектами\n"
            "• Инициализация Git репозиториев\n"
            "• Создание коммитов с сообщениями\n"
            "• Просмотр истории изменений\n"
            "• Управление ветками\n"
            "• Отслеживание статуса файлов\n\n"
            "КАК НАЧАТЬ:\n"
            "1. Создайте проект (Проект → Создать проект)\n"
            "2. Инициализируйте Git (Проект → Инициализировать Git)\n"
            "3. Пишите код и создавайте коммиты (Проект → Коммит)\n"
            "4. Используйте ветки для экспериментов (Проект → Управление ветками)\n\n"
            "ПАНЕЛЬ GIT:\n"
            "• Кнопки управления Git\n"
            "• Статус репозитория\n"
            "• Выбор текущей ветки\n"
            "• Обновление информации"
        )
    
    def show_examples(self):
        examples_window = tk.Toplevel(self.root)
        examples_window.title("Примеры интерактивных программ")
        examples_window.geometry("800x600")
        
        notebook = ttk.Notebook(examples_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        examples = {
            "Рисовалка": f"""окно 800 600 "Рисовалка"
// Создано {RI_LANGUAGE_CREATOR} в {RI_LANGUAGE_YEAR}

цикл истина
    перем х = мышь_х()
    перем у = мышь_у()
    
    если мышь_нажата() то
        круг х у 10 красный
    конец
    
    обновить_экран()
конец""",
            
            "Управление": f"""окно 600 400 "Управление"
// Создано {RI_LANGUAGE_CREATOR} в {RI_LANGUAGE_YEAR}

перем x = 300
перем y = 200

цикл истина
    очистить белый
    
    если клавиша_нажата("влево") то
        перем x = x - 5
    конец
    если клавиша_нажата("вправо") то
        перем x = x + 5
    конец
    
    круг x y 30 синий
    обновить_экран()
конец""",
            
            "Игра": f"""окно 800 600 "Ловля шариков"
// Создано {RI_LANGUAGE_CREATOR} в {RI_LANGUAGE_YEAR}

перем счет = 0
перем шарик_x = 400
перем шарик_y = 50

цикл истина
    очистить белый
    
    перем шарик_y = шарик_y + 3
    если шарик_y > 600 то
        перем шарик_y = 0
        перем шарик_x = случайно(100, 700)
    конец
    
    круг шарик_x шарик_y 30 красный
    
    перем х = мышь_х()
    перем у = мышь_у()
    
    прямоугольник х-50 550 100 20 синий
    
    если шарик_y > 530 и шарик_y < 570 и 
       шарик_x > х-50 и шарик_x < х+50 то
        перем счет = счет + 1
        перем шарик_y = 0
        перем шарик_x = случайно(100, 700)
    конец
    
    текст 100 50 "Счет: " + счет черный
    
    обновить_экран()
    задержка 16
конец"""
        }
        
        for name, code in examples.items():
            frame = ttk.Frame(notebook)
            text = scrolledtext.ScrolledText(frame, wrap=tk.WORD, font=("Consolas", 11))
            text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            text.insert(1.0, code)
            
            btn_frame = ttk.Frame(frame)
            btn_frame.pack(fill=tk.X, padx=5, pady=5)
            
            ttk.Button(btn_frame, text="📋 Вставить", 
                      command=lambda c=code: self.insert_example(c, examples_window)).pack()
            
            notebook.add(frame, text=name)
    
    def insert_example(self, code, window):
        self.code_editor.delete(1.0, tk.END)
        self.code_editor.insert(1.0, code)
        self.highlight_syntax()
        window.destroy()
        self.status_bar.config(text="✓ Пример загружен в редактор")
    
    def show_about(self):
        messagebox.showinfo(
            f"О программе Ri IDE v{self.ide_version}",
            f"Ri IDE v{self.ide_version}\n"
            f"Язык программирования Ri {RI_LANGUAGE_VERSION}\n"
            f"Создатель: {RI_LANGUAGE_CREATOR}\n"
            f"Год создания: {RI_LANGUAGE_YEAR}\n\n"
            "Полнофункциональная среда разработки с:\n"
            "• Интерактивной графикой и обработкой событий\n"
            "• Продвинутым отладчиком с точками останова\n"
            "• Автодополнением кода (IntelliSense)\n"
            "• Интеграцией с Git для управления версиями\n"
            "• Проектной структурой и метаданными\n\n"
            "Добавлено в этой версии:\n"
            "• Нумерация строк с точками останова\n"
            "• Пошаговая отладка (F10, F11, Shift+F11)\n"
            "• Встроенные функции (случайно, длина, корень и др.)\n"
            "• Поддержка списков и массивов\n"
            "• Git интеграция с коммитами и ветками\n"
            "• Улучшенный редактор с подсветкой синтаксиса\n\n"
            f"© {RI_LANGUAGE_YEAR} {RI_LANGUAGE_CREATOR}. Все права защищены."
        )

def main():
    root = tk.Tk()
    app = RiIDE(root)
    root.mainloop()

if __name__ == "__main__":
    main()
