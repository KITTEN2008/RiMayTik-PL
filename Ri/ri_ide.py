import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog, Canvas
import threading
import queue
import re
import time
class GraphicsWindow:
    """Окно для графики с обработкой событий"""
    def __init__(self, width=800, height=600, title="Графика Ri", ide=None):
        self.window = tk.Toplevel()
        self.window.title(title)
        self.window.geometry(f"{width}x{height}")
        self.ide = ide
        
        self.canvas = Canvas(self.window, width=width, height=height, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Устанавливаем фокус для событий клавиатуры
        self.canvas.focus_set()
        
        # Состояние мыши и клавиатуры
        self.mouse_x = 0
        self.mouse_y = 0
        self.mouse_pressed = False
        self.keys_pressed = set()
        self.last_key = ""
        
        # Привязываем события
        self.bind_events()
        
        self.objects = []
        self.is_open = True
        
        self.window.protocol("WM_DELETE_WINDOW", self.close)
    
    def bind_events(self):
        """Привязывает события мыши и клавиатуры"""
        # События мыши
        self.canvas.bind("<Motion>", self.on_mouse_move)
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_release)
        self.canvas.bind("<ButtonPress-2>", self.on_mouse_press_middle)
        self.canvas.bind("<ButtonRelease-2>", self.on_mouse_release_middle)
        self.canvas.bind("<ButtonPress-3>", self.on_mouse_press_right)
        self.canvas.bind("<ButtonRelease-3>", self.on_mouse_release_right)
        
        # События клавиатуры
        self.canvas.bind("<KeyPress>", self.on_key_press)
        self.canvas.bind("<KeyRelease>", self.on_key_release)
        
        # События колесика мыши
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
    
    def on_mouse_move(self, event):
        """Движение мыши"""
        self.mouse_x = event.x
        self.mouse_y = event.y
        if self.ide:
            self.ide.event_queue.put(("mouse_move", self.mouse_x, self.mouse_y))
    
    def on_mouse_press(self, event):
        """Нажатие левой кнопки мыши"""
        self.mouse_pressed = True
        self.mouse_x = event.x
        self.mouse_y = event.y
        if self.ide:
            self.ide.event_queue.put(("mouse_press", "левая", self.mouse_x, self.mouse_y))
    
    def on_mouse_release(self, event):
        """Отпускание левой кнопки мыши"""
        self.mouse_pressed = False
        self.mouse_x = event.x
        self.mouse_y = event.y
        if self.ide:
            self.ide.event_queue.put(("mouse_release", "левая", self.mouse_x, self.mouse_y))
    
    def on_mouse_press_middle(self, event):
        """Нажатие средней кнопки мыши"""
        self.mouse_x = event.x
        self.mouse_y = event.y
        if self.ide:
            self.ide.event_queue.put(("mouse_press", "средняя", self.mouse_x, self.mouse_y))
    
    def on_mouse_release_middle(self, event):
        """Отпускание средней кнопки мыши"""
        self.mouse_x = event.x
        self.mouse_y = event.y
        if self.ide:
            self.ide.event_queue.put(("mouse_release", "средняя", self.mouse_x, self.mouse_y))
    
    def on_mouse_press_right(self, event):
        """Нажатие правой кнопки мыши"""
        self.mouse_x = event.x
        self.mouse_y = event.y
        if self.ide:
            self.ide.event_queue.put(("mouse_press", "правая", self.mouse_x, self.mouse_y))
    
    def on_mouse_release_right(self, event):
        """Отпускание правой кнопки мыши"""
        self.mouse_x = event.x
        self.mouse_y = event.y
        if self.ide:
            self.ide.event_queue.put(("mouse_release", "правая", self.mouse_x, self.mouse_y))
    
    def on_key_press(self, event):
        """Нажатие клавиши"""
        key = self.translate_key(event.keysym)
        self.keys_pressed.add(key)
        self.last_key = key
        
        # Отправляем событие
        if self.ide:
            self.ide.event_queue.put(("key_press", key))
    
    def on_key_release(self, event):
        """Отпускание клавиши"""
        key = self.translate_key(event.keysym)
        if key in self.keys_pressed:
            self.keys_pressed.remove(key)
        
        if self.ide:
            self.ide.event_queue.put(("key_release", key))
    
    def on_mouse_wheel(self, event):
        """Колесико мыши"""
        direction = "вверх" if event.delta > 0 else "вниз"
        if self.ide:
            self.ide.event_queue.put(("mouse_wheel", direction, self.mouse_x, self.mouse_y))
    
    def translate_key(self, keysym):
        """Переводит символ клавиши в русское название"""
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
        
        # Если клавиша уже в переводе, возвращаем
        if keysym in translations:
            return translations[keysym]
        
        # Для букв и цифр возвращаем как есть (в нижнем регистре)
        if len(keysym) == 1:
            return keysym.lower()
        
        # Убираем префикс для специальных клавиш
        if keysym.startswith("KP_"):  # Клавиши numpad
            return keysym[3:].lower()
        
        return keysym.lower()
    
    def get_mouse_x(self):
        """Возвращает X координату мыши"""
        return self.mouse_x
    
    def get_mouse_y(self):
        """Возвращает Y координату мыши"""
        return self.mouse_y
    
    def get_mouse_pressed(self):
        """Возвращает состояние левой кнопки мыши"""
        return self.mouse_pressed
    
    def get_key_pressed(self, key_code):
        """Проверяет, нажата ли указанная клавиша"""
        return key_code in self.keys_pressed
    
    def close(self):
        """Закрывает окно"""
        self.is_open = False
        self.window.destroy()
    
    def clear(self, color="white"):
        """Очищает холст"""
        self.canvas.delete("all")
        self.canvas.config(bg=self._translate_color(color))
        self.objects.clear()
    
    def draw_rectangle(self, x, y, width, height, color="black"):
        """Рисует прямоугольник"""
        obj = self.canvas.create_rectangle(
            x, y, x + width, y + height,
            fill=self._translate_color(color),
            outline=self._translate_color(color)
        )
        self.objects.append(obj)
        return obj
    
    def draw_circle(self, x, y, radius, color="black"):
        """Рисует круг"""
        obj = self.canvas.create_oval(
            x - radius, y - radius,
            x + radius, y + radius,
            fill=self._translate_color(color),
            outline=self._translate_color(color)
        )
        self.objects.append(obj)
        return obj
    
    def draw_line(self, x1, y1, x2, y2, color="black"):
        """Рисует линию"""
        obj = self.canvas.create_line(
            x1, y1, x2, y2,
            fill=self._translate_color(color),
            width=2
        )
        self.objects.append(obj)
        return obj
    
    def draw_text(self, x, y, text, color="black"):
        """Рисует текст"""
        obj = self.canvas.create_text(
            x, y,
            text=text,
            fill=self._translate_color(color),
            font=("Arial", 14)
        )
        self.objects.append(obj)
        return obj
    
    def update_screen(self):
        """Обновляет экран"""
        self.window.update()
    
    def _translate_color(self, color_name):
        """Переводит название цвета на русском в hex"""
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
        self.root.title("Ri IDE v6.0 - Интерактивная графика!")
        self.root.geometry("1100x750")
        
        # Очереди
        self.output_queue = queue.Queue()
        self.input_queue = queue.Queue()
        self.graphics_queue = queue.Queue()
        self.event_queue = queue.Queue()
        
        # Обработчики событий
        self.event_handlers = {
            "mouse_move": None,
            "mouse_press": None,
            "mouse_release": None,
            "key_press": None,
            "key_release": None,
            "mouse_wheel": None
        }
        
        # Состояние
        self.waiting_for_input = False
        self.current_input_prompt = ""
        self.graphics_window = None
        self.is_running = False
        
        # Настройка интерфейса
        self.setup_ui()
        self.setup_tags()
        self.insert_sample_code()
        
        # Запускаем обработчики
        self.root.after(100, self.process_queue)
        self.root.after(100, self.process_graphics_queue)
        self.root.after(50, self.process_events)
        
        # Горячие клавиши
        self.setup_shortcuts()
        
    def setup_ui(self):
        # Меню
        menubar = tk.Menu(self.root)
        
        # Меню Файл
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="📄 Новый", command=self.new_file, accelerator="Ctrl+N")
        file_menu.add_command(label="📂 Открыть", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="💾 Сохранить", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_command(label="💾 Сохранить как", command=self.save_as_file)
        file_menu.add_separator()
        file_menu.add_command(label="🚪 Выход", command=self.root.quit)
        
        # Меню Выполнение
        run_menu = tk.Menu(menubar, tearoff=0)
        run_menu.add_command(label="▶ Запустить", command=self.run_code, accelerator="F5")
        run_menu.add_command(label="■ Остановить", command=self.stop_execution)
        run_menu.add_separator()
        run_menu.add_command(label="🎨 Открыть графику", command=self.open_graphics_window)
        run_menu.add_command(label="🧹 Очистить графику", command=self.clear_graphics)
        run_menu.add_separator()
        run_menu.add_command(label="🧹 Очистить консоль", command=self.clear_console)
        
        # Меню Графика
        graphics_menu = tk.Menu(menubar, tearoff=0)
        graphics_menu.add_command(label="🎮 Пример: Рисовалка", command=self.insert_draw_example)
        graphics_menu.add_command(label="🎯 Пример: Цели", command=self.insert_target_example)
        graphics_menu.add_command(label="⌨️ Пример: Клавиатура", command=self.insert_keyboard_example)
        graphics_menu.add_command(label="🏎️ Пример: Машинка", command=self.insert_car_example)
        
        # Меню Помощь
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="📖 Справка", command=self.show_help)
        help_menu.add_command(label="🖱️ События мыши", command=self.show_mouse_help)
        help_menu.add_command(label="⌨️ Коды клавиш", command=self.show_keyboard_help)
        help_menu.add_command(label="📚 Примеры", command=self.show_examples)
        help_menu.add_command(label="ℹ️ О программе", command=self.show_about)
        
        menubar.add_cascade(label="Файл", menu=file_menu)
        menubar.add_cascade(label="Выполнение", menu=run_menu)
        menubar.add_cascade(label="Интерактив", menu=graphics_menu)
        menubar.add_cascade(label="Помощь", menu=help_menu)
        
        self.root.config(menu=menubar)
        
        # Панель инструментов
        toolbar = ttk.Frame(self.root, relief=tk.RAISED)
        toolbar.pack(fill=tk.X, padx=2, pady=2)
        
        # Кнопки
        style = ttk.Style()
        style.configure('Green.TButton', background='#4CAF50', foreground='white')
        style.configure('Red.TButton', background='#F44336', foreground='white')
        style.configure('Blue.TButton', background='#2196F3', foreground='white')
        style.configure('Purple.TButton', background='#9C27B0', foreground='white')
        
        ttk.Button(toolbar, text="▶ Запуск (F5)", command=self.run_code, style='Green.TButton').pack(side=tk.LEFT, padx=2, pady=2)
        ttk.Button(toolbar, text="■ Стоп", command=self.stop_execution, style='Red.TButton').pack(side=tk.LEFT, padx=2, pady=2)
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)
        ttk.Button(toolbar, text="🎮 Графика", command=self.open_graphics_window, style='Purple.TButton').pack(side=tk.LEFT, padx=2, pady=2)
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)
        ttk.Button(toolbar, text="📄 Новый", command=self.new_file, style='Blue.TButton').pack(side=tk.LEFT, padx=2, pady=2)
        ttk.Button(toolbar, text="📂 Открыть", command=self.open_file, style='Blue.TButton').pack(side=tk.LEFT, padx=2, pady=2)
        ttk.Button(toolbar, text="💾 Сохранить", command=self.save_file, style='Blue.TButton').pack(side=tk.LEFT, padx=2, pady=2)
        
        # Панель состояния событий
        event_frame = ttk.Frame(self.root)
        event_frame.pack(fill=tk.X, padx=5, pady=2)
        
        self.mouse_label = ttk.Label(event_frame, text="Мышь: (0, 0) Не нажата")
        self.mouse_label.pack(side=tk.LEFT, padx=10)
        
        self.key_label = ttk.Label(event_frame, text="Клавиши: ")
        self.key_label.pack(side=tk.LEFT, padx=10)
        
        # Основной контейнер
        main_paned = ttk.PanedWindow(self.root, orient=tk.VERTICAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Верхняя панель - редактор
        editor_frame = ttk.LabelFrame(main_paned, text="📝 Редактор кода Ri", padding=10)
        
        self.code_editor = scrolledtext.ScrolledText(
            editor_frame,
            wrap=tk.WORD,
            font=("Consolas", 12),
            bg='#1e1e1e',
            fg='#d4d4d4',
            insertbackground='white',
            undo=True,
            maxundo=-1,
            height=15
        )
        self.code_editor.pack(fill=tk.BOTH, expand=True)
        self.code_editor.bind('<KeyRelease>', lambda e: self.highlight_syntax())
        
        # Нижняя панель - консоль
        console_frame = ttk.LabelFrame(main_paned, text="📊 Консоль (Вывод и Ввод)", padding=10)
        
        # Консоль вывода
        self.console_output = scrolledtext.ScrolledText(
            console_frame,
            wrap=tk.WORD,
            font=("Consolas", 11),
            bg='#0c0c0c',
            fg='white',
            height=8
        )
        self.console_output.pack(fill=tk.BOTH, expand=True)
        
        # Панель ввода
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
        
        # Добавляем панели
        main_paned.add(editor_frame, weight=3)
        main_paned.add(console_frame, weight=1)
        
        # Панель событий
        events_frame = ttk.LabelFrame(self.root, text="📡 События", padding=10)
        events_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.events_listbox = tk.Listbox(
            events_frame,
            font=("Consolas", 9),
            bg='#f0f0f0',
            height=3
        )
        self.events_listbox.pack(fill=tk.X)
        
        # Статус бар
        self.status_bar = ttk.Label(
            self.root,
            text="✓ Готов к работе. Нажмите F5 для запуска интерактивной программы!",
            relief=tk.SUNKEN,
            padding=5,
            font=("Arial", 10)
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.current_file = None
        
    def setup_tags(self):
        """Настраивает теги для подсветки"""
        self.code_editor.tag_configure("keyword", foreground="#569CD6", font=("Consolas", 12))
        self.code_editor.tag_configure("comment", foreground="#6A9955", font=("Consolas", 12, "italic"))
        self.code_editor.tag_configure("string", foreground="#CE9178")
        self.code_editor.tag_configure("number", foreground="#B5CEA8")
        self.code_editor.tag_configure("operator", foreground="#D4D4D4")
        self.code_editor.tag_configure("graphics", foreground="#D7BA7D")
        self.code_editor.tag_configure("events", foreground="#C586C0")
        
    def highlight_syntax(self, event=None):
        """Подсвечивает синтаксис"""
        cursor_pos = self.code_editor.index(tk.INSERT)
        code = self.code_editor.get("1.0", tk.END)
        
        for tag in ["keyword", "comment", "string", "number", "operator", "graphics", "events"]:
            self.code_editor.tag_remove(tag, "1.0", tk.END)
        
        if not code:
            return
        
        lines = code.split('\n')
        pos = 0
        
        for line in lines:
            # Комментарии
            if '//' in line:
                comment_start = line.find('//')
                start = f"1.{pos + comment_start}"
                end = f"1.{pos + len(line)}"
                self.code_editor.tag_add("comment", start, end)
            
            # Строки
            for match in re.finditer(r'"[^"]*"', line):
                start = f"1.{pos + match.start()}"
                end = f"1.{pos + match.end()}"
                self.code_editor.tag_add("string", start, end)
            
            # Ключевые слова
            keywords = ['перем', 'если', 'иначе', 'цикл', 'конец', 'то', 
                       'функция', 'вызвать', 'вывести', 'ввести', 'возврат',
                       'и', 'или', 'не', 'истина', 'ложь']
            for keyword in keywords:
                pattern = r'\b' + re.escape(keyword) + r'\b'
                for match in re.finditer(pattern, line, re.IGNORECASE):
                    start = f"1.{pos + match.start()}"
                    end = f"1.{pos + match.end()}"
                    self.code_editor.tag_add("keyword", start, end)
            
            # Графические команды
            graphics_cmds = ['окно', 'прямоугольник', 'круг', 'линия', 
                           'текст', 'задержка', 'очистить', 'обновить_экран']
            for cmd in graphics_cmds:
                pattern = r'\b' + re.escape(cmd) + r'\b'
                for match in re.finditer(pattern, line, re.IGNORECASE):
                    start = f"1.{pos + match.start()}"
                    end = f"1.{pos + match.end()}"
                    self.code_editor.tag_add("graphics", start, end)
            
            # Команды событий
            event_cmds = ['установить_обработчик', 'мышь_х', 'мышь_у', 
                         'мышь_нажата', 'клавиша_нажата', 'остановить']
            for cmd in event_cmds:
                pattern = r'\b' + re.escape(cmd) + r'\b'
                for match in re.finditer(pattern, line, re.IGNORECASE):
                    start = f"1.{pos + match.start()}"
                    end = f"1.{pos + match.end()}"
                    self.code_editor.tag_add("events", start, end)
            
            # Числа
            for match in re.finditer(r'\b\d+(\.\d+)?\b', line):
                start = f"1.{pos + match.start()}"
                end = f"1.{pos + match.end()}"
                self.code_editor.tag_add("number", start, end)
            
            # Операторы
            operators = ['\+', '-', '\*', '/', '=', '>', '<', '>=', '<=', '==', '!=']
            for op in operators:
                for match in re.finditer(op, line):
                    start = f"1.{pos + match.start()}"
                    end = f"1.{pos + match.end()}"
                    self.code_editor.tag_add("operator", start, end)
            
            pos += len(line) + 1
        
        self.code_editor.mark_set(tk.INSERT, cursor_pos)
        
    def insert_sample_code(self):
        """Вставляет пример кода"""
        sample = """// Ri 3.0 - Интерактивная графика с мышью и клавиатурой!
// Пример программы для рисования мышью
окно 800 600 "Рисовалка"
перем цвет = "черный"
перем размер = 5
перем рисовать = ложь
очистить белый
текст 300 30 "Рисовалка: ЛКМ - рисовать, ПКМ - менять цвет, колесико - размер" черный
текст 300 550 "Пробел - очистить, Escape - выход" черный
цикл истина
    // Получаем позицию мыши
    перем х = мышь_х()
    перем у = мышь_у()
    
    // Проверяем нажатие мыши
    если мышь_нажата() то
        перем рисовать = истина
        круг х у размер цвет
    иначе
        перем рисовать = ложь
    конец
    
    // Обработка клавиш
    если клавиша_нажата("пробел") то
        очистить белый
        текст 300 30 "Рисовалка: ЛКМ - рисовать, ПКМ - менять цвет, колесико - размер" черный
        текст 300 550 "Пробел - очистить, Escape - выход" черный
    конец
    
    если клавиша_нажата("эскейп") то
        остановить()
    конец
    
    // Меняем цвет правой кнопкой
    если клавиша_нажата("правая") то
        если цвет == "черный" то
            перем цвет = "красный"
        иначе если цвет == "красный" то
            перем цвет = "синий"
        иначе если цвет == "синий" то
            перем цвет = "зеленый"
        иначе если цвет == "зеленый" то
            перем цвет = "фиолетовый"
        иначе
            перем цвет = "черный"
        конец
        
        // Пауза чтобы не менялось слишком быстро
        задержка 200
    конец
    
    // Меняем размер колесиком
    если клавиша_нажата("вверх") то
        перем размер = размер + 1
        задержка 50
    конец
    
    если клавиша_нажата("вниз") то
        если размер > 1 то
            перем размер = размер - 1
        конец
        задержка 50
    конец
    
    // Показываем информацию
    прямоугольник 10 10 200 100 светло-голубой
    текст 110 40 "Позиция: (" + х + ", " + у + ")" черный
    текст 110 60 "Цвет: " + цвет черный
    текст 110 80 "Размер: " + размер черный
    текст 110 100 "Рисовать: " + рисовать черный
    
    обновить_экран()
    задержка 16  // ~60 FPS
конец
"""
        self.code_editor.delete(1.0, tk.END)
        self.code_editor.insert(1.0, sample)
        self.highlight_syntax()
    
    def setup_shortcuts(self):
        """Настраивает горячие клавиши"""
        self.root.bind('<Control-n>', lambda e: self.new_file())
        self.root.bind('<Control-o>', lambda e: self.open_file())
        self.root.bind('<Control-s>', lambda e: self.save_file())
        self.root.bind('<F5>', lambda e: self.run_code())
        self.root.bind('<Return>', lambda e: self.send_input_if_active())
        
    def send_input_if_active(self):
        """Отправляет ввод, если активно поле ввода"""
        if self.waiting_for_input and self.input_entry.get():
            self.send_input()
    
    def run_code(self):
        """Запускает выполнение кода"""
        if self.is_running:
            messagebox.showwarning("Внимание", "Программа уже выполняется!")
            return
        
        self.is_running = True
        self.status_bar.config(text="▶ Выполнение программы...")
        
        # Очищаем консоль и события
        self.console_output.config(state=tk.NORMAL)
        self.console_output.delete(1.0, tk.END)
        self.console_output.config(state=tk.DISABLED)
        self.events_listbox.delete(0, tk.END)
        
        # Скрываем панель ввода
        self.input_frame.pack_forget()
        self.waiting_for_input = False
        
        # Закрываем старое графическое окно
        if self.graphics_window:
            self.graphics_window.close()
            self.graphics_window = None
        
        # Получаем код
        code = self.code_editor.get(1.0, tk.END)
        
        # Запускаем в отдельном потоке
        thread = threading.Thread(target=self.execute_code, args=(code,))
        thread.daemon = True
        thread.start()
    
    def execute_code(self, code):
        """Выполняет код в отдельном потоке"""
        try:
            from ri_compiler import run_ri_code
            
            # Callback для графики
            def graphics_callback(commands):
                self.graphics_queue.put(commands)
            
            # Callback для ввода
            def input_callback(type, prompt):
                if type == "input":
                    self.output_queue.put(("input_request", prompt))
                    return self.input_queue.get()
                return ""
            
            # Callback для событий
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
                    # Сохраняем обработчик
                    parts = data.split(":")
                    if len(parts) == 2:
                        event_type, handler = parts
                        self.event_handlers[event_type] = handler
                return ""
            
            # Запускаем выполнение кода
            result = run_ri_code(code, graphics_callback, input_callback, event_callback)
            
            # Отправляем финальный результат
            if result:
                self.output_queue.put(("output", "\n" + result))
            
            # Обновляем статус
            self.output_queue.put(("status", "✓ Выполнение завершено"))
            
        except Exception as e:
            self.output_queue.put(("error", f"Ошибка выполнения: {str(e)}"))
            self.output_queue.put(("status", f"✗ Ошибка: {str(e)}"))
        finally:
            self.is_running = False
    
    def process_queue(self):
        """Обрабатывает очередь вывода"""
        try:
            while not self.output_queue.empty():
                msg_type, data = self.output_queue.get_nowait()
                
                if msg_type == "output":
                    self.console_output.config(state=tk.NORMAL)
                    self.console_output.insert(tk.END, data + "\n", "output")
                    self.console_output.see(tk.END)
                    self.console_output.config(state=tk.DISABLED)
                    
                elif msg_type == "error":
                    self.console_output.config(state=tk.NORMAL)
                    self.console_output.insert(tk.END, "❌ ОШИБКА: " + data + "\n", "error")
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
        """Обрабатывает очередь графических команд"""
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
        """Обрабатывает события мыши и клавиатуры"""
        try:
            while not self.event_queue.empty():
                event = self.event_queue.get_nowait()
                event_type = event[0]
                
                # Обновляем метки состояния
                if self.graphics_window:
                    self.mouse_label.config(
                        text=f"Мышь: ({self.graphics_window.mouse_x}, {self.graphics_window.mouse_y}) " +
                             f"{'Нажата' if self.graphics_window.mouse_pressed else 'Не нажата'}"
                    )
                    
                    keys_text = "Клавиши: " + ", ".join(sorted(self.graphics_window.keys_pressed))
                    if len(keys_text) > 50:
                        keys_text = keys_text[:47] + "..."
                    self.key_label.config(text=keys_text)
                
                # Добавляем событие в список
                event_str = str(event)
                self.events_listbox.insert(0, event_str)
                if self.events_listbox.size() > 10:
                    self.events_listbox.delete(10, tk.END)
                
                # Если есть обработчик, можно вызвать его
                # (здесь можно расширить для вызова функций Ri)
        
        except Exception as e:
            pass
        
        self.root.after(50, self.process_events)
    
    def send_input(self):
        """Отправляет введенные данные"""
        if not self.waiting_for_input:
            return
        
        user_input = self.input_entry.get().strip()
        if user_input:
            self.input_frame.pack_forget()
            self.waiting_for_input = False
            
            self.input_queue.put(user_input)
            
            self.console_output.config(state=tk.NORMAL)
            self.console_output.insert(tk.END, user_input + "\n", "input")
            self.console_output.see(tk.END)
            self.console_output.config(state=tk.DISABLED)
            
            self.input_entry.delete(0, tk.END)
    
    def open_graphics_window(self):
        """Открывает графическое окно"""
        if not self.graphics_window:
            self.graphics_window = GraphicsWindow(ide=self)
        else:
            self.graphics_window.window.lift()
    
    def clear_graphics(self):
        """Очищает графическое окно"""
        if self.graphics_window:
            self.graphics_window.clear()
    
    def insert_draw_example(self):
        """Вставляет пример рисовалки"""
        example = """// Пример: Интерактивная рисовалка
окно 800 600 "Рисовалка мышью"
перем цвет = "черный"
перем размер = 5
перем рисовать = ложь
перем последний_х = 0
перем последний_у = 0
очистить белый
текст 300 30 "Рисуй мышью! ЛКМ - рисовать, ПКМ - цвет, колесико - размер" черный
цикл истина
    // Получаем позицию мыши
    перем х = мышь_х()
    перем у = мышь_у()
    
    // Рисуем при нажатой мыши
    если мышь_нажата() то
        если не рисовать то
            перем рисовать = истина
            перем последний_х = х
            перем последний_у = у
        конец
        
        // Рисуем линию от предыдущей точки
        линия последний_х последний_у х у цвет
        перем последний_х = х
        перем последний_у = у
    иначе
        перем рисовать = ложь
    конец
    
    // Смена цвета по клавишам
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
    
    // Очистка
    если клавиша_нажата("пробел") то
        очистить белый
        текст 300 30 "Рисуй мышью! ЛКМ - рисовать, ПКМ - цвет, колесико - размер" черный
    конец
    
    // Выход
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
    
    def insert_target_example(self):
        """Вставляет пример игры-стрелялки"""
        example = """// Пример: Игра "Стрельба по мишеням"
окно 800 600 "Стрельба по мишеням"
перем счет = 0
перем мишени = []
перем время = 0
// Создаем мишени
перем i = 0
цикл i < 10
    перем x = случайно(100, 700)
    перем y = случайно(100, 500)
    перем радиус = случайно(20, 40)
    перем цвет = случайно_цвет()
    добавить(мишени, [x, y, радиус, цвет])
    перем i = i + 1
конец
цикл истина
    очистить светло-голубой
    
    // Рисуем мишени
    перем i = 0
    цикл i < длина(мишени)
        перем мишень = мишени[i]
        круг мишень[0] мишень[1] мишень[2] мишень[3]
        перем i = i + 1
    конец
    
    // Получаем позицию мыши
    перем х = мышь_х()
    перем у = мышь_у()
    
    // Прицел
    круг х у 10 черный
    линия х-15 у х+15 у красный
    линия х у-15 х у+15 красный
    
    // Стрельба при нажатии мыши
    если мышь_нажата() то
        // Проверяем попадание
        перем i = 0
        цикл i < длина(мишени)
            перем мишень = мишени[i]
            перем расстояние = корень((х - мишень[0])^2 + (у - мишень[1])^2)
            
            если расстояние < мишень[2] то
                // Попали!
                перем счет = счет + 1
                удалить(мишени, i)
                
                // Создаем новую мишень
                перем новый_x = случайно(100, 700)
                перем новый_y = случайно(100, 500)
                перем новый_радиус = случайно(20, 40)
                перем новый_цвет = случайно_цвет()
                добавить(мишени, [новый_x, новый_y, новый_радиус, новый_цвет])
                
                выйти  // Выходим из цикла после попадания
            конец
            
            перем i = i + 1
        конец
        
        // Пауза чтобы не стрелять слишком быстро
        задержка 100
    конец
    
    // Показываем счет
    прямоугольник 10 10 200 60 белый
    текст 110 30 "Счет: " + счет черный
    текст 110 50 "Мишеней: " + длина(мишени) черный
    
    // Выход
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
    
    def insert_keyboard_example(self):
        """Вставляет пример управления клавиатурой"""
        example = """// Пример: Управление объектом клавиатурой
окно 800 600 "Управление клавиатурой"
перем x = 400
перем y = 300
перем скорость = 5
перем цвет = "красный"
очистить белый
текст 300 30 "Используй стрелки для движения, 1-4 для цвета, пробел для прыжка" черный
цикл истина
    очистить белый
    текст 300 30 "Используй стрелки для движения, 1-4 для цвета, пробел для прыжка" черный
    
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
    
    // Прыжок
    если клавиша_нажата("пробел") то
        перем y = y - 50
        задержка 100
        перем y = y + 50
    конец
    
    // Смена цвета
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
    
    // Ограничение границ
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
    
    // Рисуем персонажа
    круг x y 30 цвет  // Тело
    круг x-10 y-10 5 черный  // Левый глаз
    круг x+10 y-10 5 черный  // Правый глаз
    
    // Показываем координаты
    прямоугольник 10 10 200 80 светло-голубой
    текст 110 30 "X: " + x черный
    текст 110 50 "Y: " + y черный
    текст 110 70 "Цвет: " + цвет черный
    
    // Выход
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
    
    def insert_car_example(self):
        """Вставляет пример вождения машинки"""
        example = """// Пример: Вождение машинки
окно 800 600 "Вождение машинки"
перем x = 400
перем y = 500
перем скорость = 0
перем поворот = 0
очистить светло-зеленый
цикл истина
    // Дорога
    прямоугольник 200 0 400 600 серый
    
    // Разметка
    перем i = 0
    цикл i < 12
        прямоугольник 390 i*50 20 30 желтый
        перем i = i + 1
    конец
    
    // Управление
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
    
    // Торможение
    если клавиша_нажата("пробел") то
        перем скорость = скорость * 0.9
    конец
    
    // Ограничения
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
    
    // Движение
    перем x = x + скорость * синус(поворот)
    перем y = y - скорость * косинус(поворот)
    
    // Ограничение дороги
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
    
    // Машинка
    прямоугольник x-30 y-15 60 30 красный  // Кузов
    прямоугольник x-40 y+15 80 10 темно-серый  // Основание
    круг x-25 y+25 10 черный  // Левое колесо
    круг x+25 y+25 10 черный  // Правое колесо
    
    // Стекло
    прямоугольник x-20 y-10 40 10 голубой
    
    // Фары
    если скорость > 0 то
        круг x+35 y 5 желтый  // Передняя фара
    конец
    если скорость < 0 то
        круг x-35 y 5 желтый  // Задняя фара
    конец
    
    // Информация
    прямоугольник 10 10 200 100 белый
    текст 110 30 "Скорость: " + скорость черный
    текст 110 50 "Поворот: " + поворот черный
    текст 110 70 "X: " + x + " Y: " + y черный
    
    // Выход
    если клавиша_нажата("эскейп") то
        остановить()
    конец
    
    // Автоматическое выравнивание
    перем поворот = поворот * 0.95
    
    обновить_экран()
    задержка 16
конец
"""
        self.code_editor.delete(1.0, tk.END)
        self.code_editor.insert(1.0, example)
        self.highlight_syntax()
    
    def new_file(self):
        """Создает новый файл"""
        self.code_editor.delete(1.0, tk.END)
        self.current_file = None
        self.status_bar.config(text="✓ Новый файл создан")
        self.highlight_syntax()
    
    def open_file(self):
        """Открывает файл"""
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
        """Сохраняет файл"""
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
        """Сохраняет файл как"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".ri",
            filetypes=[("Ri файлы", "*.ri"), ("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")]
        )
        if filename:
            self.current_file = filename
            self.save_file()
    
    def stop_execution(self):
        """Останавливает выполнение"""
        self.is_running = False
        self.input_frame.pack_forget()
        self.waiting_for_input = False
        self.status_bar.config(text="■ Выполнение остановлено")
    
    def clear_console(self):
        """Очищает консоль"""
        self.console_output.config(state=tk.NORMAL)
        self.console_output.delete(1.0, tk.END)
        self.console_output.config(state=tk.DISABLED)
    
    def show_help(self):
        """Показывает справку"""
        help_window = tk.Toplevel(self.root)
        help_window.title("Справка по языку Ri 6.0")
        help_window.geometry("800x600")
        
        text = scrolledtext.ScrolledText(help_window, wrap=tk.WORD, font=("Arial", 11))
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        content = """Ri 6.0 - Интерактивная графика!
НОВЫЕ ВОЗМОЖНОСТИ:
1. ОБРАБОТКА МЫШИ:
   • мышь_х() - возвращает X координату мыши
   • мышь_у() - возвращает Y координату мыши
   • мышь_нажата() - возвращает истина, если нажата левая кнопка
2. ОБРАБОТКА КЛАВИАТУРЫ:
   • клавиша_нажата("код") - проверяет нажатие клавиши
3. КОДЫ КЛАВИШ:
   • "пробел", "ввод", "эскейп", "таб"
   • "влево", "вправо", "вверх", "вниз"
   • "1", "2", "3", ... "0"
   • "a", "b", "c", ... "z"
   • "ф1", "ф2", ... "ф12"
4. УПРАВЛЕНИЕ ОКНОМ:
   • обновить_экран() - обновляет графическое окно
   • остановить() - останавливает выполнение программы
ПРИМЕР:
окно 800 600 "Игра"
перем х = мышь_х()
перем у = мышь_у()
если мышь_нажата() то
    круг х у 20 красный
конец
если клавиша_нажата("пробел") то
    очистить белый
конец
обновить_экран()
"""
        text.insert(1.0, content)
        text.config(state=tk.DISABLED)
    
    def show_mouse_help(self):
        """Показывает справку по мыши"""
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
        """Показывает справку по клавиатуре"""
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
    
    def show_examples(self):
        """Показывает примеры"""
        examples_window = tk.Toplevel(self.root)
        examples_window.title("Примеры интерактивных программ")
        examples_window.geometry("800x600")
        
        notebook = ttk.Notebook(examples_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        examples = {
            "Рисовалка": """окно 800 600 "Рисовалка"
цикл истина
    перем х = мышь_х()
    перем у = мышь_у()
    
    если мышь_нажата() то
        круг х у 10 красный
    конец
    
    обновить_экран()
конец""",
            
            "Управление": """окно 600 400 "Управление"
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
            
            "Игра": """окно 800 600 "Ловля шариков"
перем счет = 0
перем шарик_x = 400
перем шарик_y = 50
цикл истина
    очистить белый
    
    // Движение шарика
    перем шарик_y = шарик_y + 3
    если шарик_y > 600 то
        перем шарик_y = 0
        перем шарик_x = случайно(100, 700)
    конец
    
    // Рисуем шарик
    круг шарик_x шарик_y 30 красный
    
    // Получаем позицию мыши
    перем х = мышь_х()
    перем у = мышь_у()
    
    // Рисуем корзину
    прямоугольник х-50 550 100 20 синий
    
    // Проверка попадания
    если шарик_y > 530 и шарик_y < 570 и 
       шарик_x > х-50 и шарик_x < х+50 то
        перем счет = счет + 1
        перем шарик_y = 0
        перем шарик_x = случайно(100, 700)
    конец
    
    // Счет
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
        """Вставляет пример"""
        self.code_editor.delete(1.0, tk.END)
        self.code_editor.insert(1.0, code)
        self.highlight_syntax()
        window.destroy()
    
    def show_about(self):
        """Показывает информацию о программе"""
        messagebox.showinfo(
            "О программе Ri IDE",
            "Ri IDE v3.0\n\n"
            "Язык программирования с интерактивной графикой!\n\n"
            "Добавлено в этой версии:\n"
            "• Обработка мыши (координаты, нажатия)\n"
            "• Обработка клавиатуры (проверка нажатия клавиш)\n"
            "• Интерактивные примеры (игры, рисовалки)\n"
            "• Панель состояния событий\n\n"
            "Теперь можно создавать:\n"
            "• Игры с управлением\n"
            "• Программы для рисования\n"
            "• Интерактивные симуляции\n"
            "• Образовательные программы\n\n"
            "© 2025 Для обучения программированию"
        )
def main():
    root = tk.Tk()
    app = RiIDE(root)
    root.mainloop()
if __name__ == "__main__":
    main()

