# Ri Language v4.7.1 - Компилятор с поддержкой отладки (ИСПРАВЛЕННАЯ ВЕРСИЯ)
# Copyright (c) 2024 Ri Development Team

import re
import sys
import math
import time
import random
from typing import List, Dict, Any, Optional

RI_LANGUAGE_VERSION = "4.7.1"
RI_LANGUAGE_FEATURES = [
    "Переменные и типы данных",
    "Условные операторы и циклы", 
    "Графические примитивы",
    "Обработка событий мыши/клавиатуры",
    "Базовые математические операции",
    "Отладка (новое в 4.7.0)",
    "Встроенные функции (новое в 4.7.1)",
    "Списки и массивы (новое в 4.7.1)"
]

class RiCompiler:
    def __init__(self):
        self.variables = {}
        self.output_lines = []
        self.graphics_commands = []
        self.has_graphics = False
        self.event_handlers = {}  # Обработчики событий
        self.last_mouse_x = 0
        self.last_mouse_y = 0
        self.last_mouse_pressed = False
        self.last_key = ""
        
        # Отладочные переменные
        self.debug_mode = False
        self.is_paused = False
        self.current_line_num = 0
        self.call_stack = []
        self.breakpoints = set()
        self.debug_callback = None
        self.step_mode = "run"  # 'run', 'step_over', 'step_into', 'step_out'
        self.step_depth = 0
        
        # Списки (новое в 4.7.1)
        self.lists = {}
        
        # Для немедленной отправки графических команд
        self.graphics_callback = None
        
    def execute(self, code: str, graphics_callback=None, input_callback=None, 
                event_callback=None, debug_callback=None):
        """Выполняет код на Ri с поддержкой отладки"""
        self.debug_callback = debug_callback
        self.graphics_callback = graphics_callback  # Сохраняем callback для немедленной отправки
        self.variables = {}
        self.output_lines = []
        self.graphics_commands = []
        self.has_graphics = False
        self.event_handlers = {}
        self.lists = {}
        
        lines = code.strip().split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            self.current_line_num = i + 1
            
            # Проверка точки останова
            if self._check_breakpoint(self.current_line_num):
                if self.debug_callback:
                    self.debug_callback("breakpoint_hit", self.current_line_num)
                # Ждем, пока отладчик не разрешит продолжение
                while self.is_paused:
                    time.sleep(0.01)
                    if not self.debug_mode:
                        break
            
            # Проверка режима пошагового выполнения
            if self.debug_mode and self.step_mode != "run":
                if self._should_step():
                    self.is_paused = True
                    if self.debug_callback:
                        self.debug_callback("step_hit", self.current_line_num)
                    while self.is_paused:
                        time.sleep(0.01)
            
            if not line or line.startswith('//'):
                i += 1
                continue
            
            if '//' in line:
                line = line.split('//')[0].strip()
            
            try:
                # Обновляем отладочную информацию
                if self.debug_callback:
                    self.debug_callback("line_executed", self.current_line_num)
                    self.debug_callback("variables_updated", self.variables)
                
                if line.startswith('перем '):
                    self.handle_var_declaration(line[5:].strip())
                    
                elif line.startswith('вывести '):
                    self.handle_print(line[7:].strip())
                    
                elif line.startswith('ввести '):
                    var_name = line[6:].strip()
                    if input_callback:
                        user_input = input_callback("input", f"Введите значение для '{var_name}': ")
                        try:
                            if '.' in user_input:
                                self.variables[var_name] = float(user_input)
                            elif user_input.isdigit():
                                self.variables[var_name] = int(user_input)
                            else:
                                self.variables[var_name] = user_input
                        except:
                            self.variables[var_name] = user_input
                    else:
                        self.variables[var_name] = ""
                        
                elif line.startswith('если '):
                    i = self.handle_if(lines, i, input_callback, event_callback)
                    
                elif line.startswith('цикл '):
                    i = self.handle_while(lines, i, input_callback, event_callback)
                    
                elif line.startswith('функция '):
                    # Сохраняем позицию для отладки
                    func_name = line[8:].strip().split('(')[0]
                    self.call_stack.append(f"функция {func_name} (строка {i+1})")
                    if self.debug_callback:
                        self.debug_callback("call_stack_updated", self.call_stack)
                    
                    # Пропускаем определение функции (упрощенная реализация)
                    end_pos = self.find_block_end(lines, i, 'функция')
                    i = end_pos
                    self.call_stack.pop()
                    
                elif line.startswith('список '):
                    self.handle_list_declaration(line[6:].strip())
                    
                elif line.startswith('добавить '):
                    self.handle_list_append(line[8:].strip())
                    
                elif line.startswith('удалить '):
                    self.handle_list_remove(line[7:].strip())
                    
                elif line.startswith('окно '):
                    self.handle_window_command(line[4:].strip())
                    
                elif line.startswith('прямоугольник '):
                    self.handle_rectangle_command(line[13:].strip())
                    
                elif line.startswith('круг '):
                    self.handle_circle_command(line[4:].strip())
                    
                elif line.startswith('линия '):
                    self.handle_line_command(line[5:].strip())
                    
                elif line.startswith('текст '):
                    self.handle_text_command(line[5:].strip())
                    
                elif line.startswith('задержка '):
                    self.handle_delay_command(line[8:].strip())
                    
                elif line.startswith('очистить '):
                    self.handle_clear_command(line[8:].strip())
                    
                elif line.startswith('установить_обработчик '):
                    self.handle_set_handler(line[20:].strip(), event_callback)
                    
                elif line.startswith('мышь_х()'):
                    if event_callback:
                        self.last_mouse_x = event_callback("get_mouse_x", "")
                        self.variables['мышь_х'] = self.last_mouse_x
                    
                elif line.startswith('мышь_у()'):
                    if event_callback:
                        self.last_mouse_y = event_callback("get_mouse_y", "")
                        self.variables['мышь_у'] = self.last_mouse_y
                    
                elif line.startswith('мышь_нажата()'):
                    if event_callback:
                        self.last_mouse_pressed = event_callback("get_mouse_pressed", "")
                        self.variables['мышь_нажата'] = self.last_mouse_pressed
                    
                elif line.startswith('клавиша_нажата('):
                    if ')' in line:
                        key_code = line[14:].split(')')[0].strip().strip('"\'')
                        if event_callback:
                            key_pressed = event_callback("get_key_pressed", key_code)
                            self.variables[f'клавиша_{key_code}'] = key_pressed
                    
                elif line.startswith('обновить_экран()'):
                    command = ('update',)
                    self.graphics_commands.append(command)
                    # Немедленно отправляем команду обновления
                    if self.graphics_callback:
                        self.graphics_callback([command])
                    
                elif line.startswith('остановить()'):
                    if self.debug_callback:
                        self.debug_callback("program_stopped", "")
                    break
                    
                elif line == 'конец':
                    pass
                    
                elif line == 'иначе':
                    pass
                    
                else:
                    # Проверяем, является ли строка вызовом функции
                    if '(' in line and ')' in line and not line.startswith('//'):
                        func_name = line.split('(')[0].strip()
                        if func_name in self.builtin_functions:
                            result = self.call_builtin_function(line)
                            if result is not None:
                                # Ищем присваивание
                                if '=' in line:
                                    var_name = line.split('=')[0].strip()
                                    self.variables[var_name] = result
                    elif '=' in line:
                        parts = line.split('=')
                        if len(parts) == 2:
                            var_name = parts[0].strip()
                            expr = parts[1].strip()
                            value = self.evaluate_expression(expr)
                            self.variables[var_name] = value
                            
            except Exception as e:
                error_msg = f"Ошибка в строке {i+1}: {str(e)}"
                self.output_lines.append(error_msg)
                if self.debug_callback:
                    self.debug_callback("error", error_msg)
                
            i += 1
        
        # В конце выполнения отправляем все команды для надежности
        if self.has_graphics and self.graphics_callback and self.graphics_commands:
            self.graphics_callback(self.graphics_commands)
        
        return '\n'.join(self.output_lines)
    
    def _check_breakpoint(self, line_num):
        """Проверяет, нужно ли остановиться на точке останова"""
        return line_num in self.breakpoints and self.debug_mode and not self.is_paused
    
    def _should_step(self):
        """Определяет, нужно ли остановиться для пошагового выполнения"""
        if self.step_mode == "step_over":
            return len(self.call_stack) <= self.step_depth
        elif self.step_mode == "step_into":
            return True
        elif self.step_mode == "step_out":
            return len(self.call_stack) < self.step_depth
        return False
    
    def find_block_end(self, lines, start_idx, block_type):
        """Находит конец блока (функции, если, цикла)"""
        depth = 0
        for j in range(start_idx, len(lines)):
            line = lines[j].strip()
            if line.startswith(block_type) or line.startswith('если ') or line.startswith('цикл '):
                depth += 1
            elif line == 'конец':
                depth -= 1
                if depth == 0:
                    return j
        return len(lines) - 1
    
    def handle_var_declaration(self, line):
        """Обработка объявления переменной"""
        if '=' in line:
            parts = line.split('=')
            var_name = parts[0].strip()
            expr = parts[1].strip()
            value = self.evaluate_expression(expr)
            self.variables[var_name] = value
    
    def handle_list_declaration(self, line):
        """Обработка объявления списка (новое в 4.7.1)"""
        if '=' in line:
            parts = line.split('=')
            list_name = parts[0].strip()
            expr = parts[1].strip()
            
            if expr.startswith('[') and expr.endswith(']'):
                # Парсим список
                items_str = expr[1:-1].strip()
                if items_str:
                    items = []
                    for item in items_str.split(','):
                        item = item.strip()
                        items.append(self.evaluate_expression(item))
                    self.lists[list_name] = items
                else:
                    self.lists[list_name] = []
            else:
                # Инициализация пустым списком
                self.lists[list_name] = []
    
    def handle_list_append(self, line):
        """Добавление элемента в список"""
        parts = line.split(',')
        if len(parts) >= 2:
            list_name = parts[0].strip()
            value_expr = parts[1].strip()
            value = self.evaluate_expression(value_expr)
            
            if list_name in self.lists:
                self.lists[list_name].append(value)
    
    def handle_list_remove(self, line):
        """Удаление элемента из списка"""
        parts = line.split(',')
        if len(parts) >= 2:
            list_name = parts[0].strip()
            index_expr = parts[1].strip()
            
            try:
                index = self.evaluate_expression(index_expr)
                if list_name in self.lists and 0 <= index < len(self.lists[list_name]):
                    del self.lists[list_name][index]
            except:
                pass
    
    def handle_print(self, expr):
        """Обработка команды вывода"""
        value = self.evaluate_expression(expr)
        self.output_lines.append(str(value))
    
    def handle_if(self, lines, start_idx, input_callback, event_callback):
        """Обработка условного оператора"""
        line = lines[start_idx].strip()
        condition_part = line[3:].strip()
        
        if ' то' in condition_part:
            condition_expr = condition_part.split(' то')[0].strip()
            condition = self.evaluate_expression(condition_expr)
            
            # Находим блоки if/else
            else_pos = -1
            end_pos = -1
            depth = 0
            j = start_idx + 1
            
            while j < len(lines):
                check_line = lines[j].strip()
                if check_line.startswith('//') or not check_line:
                    j += 1
                    continue
                    
                if check_line == 'конец':
                    if depth == 0:
                        end_pos = j
                        break
                    depth -= 1
                elif check_line.startswith('если '):
                    depth += 1
                elif check_line == 'иначе' and depth == 0:
                    else_pos = j
                    
                j += 1
            
            if condition:
                # Выполняем блок then
                block_end = else_pos if else_pos != -1 else end_pos
                k = start_idx + 1
                while k < block_end:
                    self.execute_single_line(lines[k].strip(), input_callback, event_callback)
                    k += 1
                return end_pos
            else:
                # Выполняем блок else если есть
                if else_pos != -1:
                    k = else_pos + 1
                    while k < end_pos:
                        self.execute_single_line(lines[k].strip(), input_callback, event_callback)
                        k += 1
                return end_pos
        
        return start_idx + 1
    
    def handle_while(self, lines, start_idx, input_callback, event_callback):
        """Обработка цикла while"""
        line = lines[start_idx].strip()
        condition_expr = line[4:].strip()
        
        # Находим конец цикла
        end_pos = -1
        depth = 0
        j = start_idx + 1
        
        while j < len(lines):
            check_line = lines[j].strip()
            if check_line.startswith('//') or not check_line:
                j += 1
                continue
                
            if check_line == 'конец':
                if depth == 0:
                    end_pos = j
                    break
                depth -= 1
            elif check_line.startswith('цикл ') or check_line.startswith('если '):
                depth += 1
                
            j += 1
        
        if end_pos == -1:
            return start_idx + 1
        
        # Выполняем цикл
        iteration_count = 0
        max_iterations = 10000
        
        while self.evaluate_expression(condition_expr) and iteration_count < max_iterations:
            # Добавляем информацию в стек вызовов
            self.call_stack.append(f"цикл (строка {start_idx+1}, итерация {iteration_count+1})")
            if self.debug_callback:
                self.debug_callback("call_stack_updated", self.call_stack)
            
            # Выполняем тело цикла
            k = start_idx + 1
            while k < end_pos:
                self.execute_single_line(lines[k].strip(), input_callback, event_callback)
                k += 1
            
            self.call_stack.pop()
            iteration_count += 1
            
            if not self.evaluate_expression(condition_expr):
                break
        
        if iteration_count >= max_iterations:
            self.output_lines.append("Предупреждение: Превышено максимальное количество итераций цикла")
        
        return end_pos
    
    def execute_single_line(self, line, input_callback, event_callback):
        """Выполняет одну строку кода"""
        if not line or line.startswith('//'):
            return
            
        if line.startswith('перем '):
            self.handle_var_declaration(line[5:].strip())
        elif line.startswith('вывести '):
            self.handle_print(line[7:].strip())
        elif line.startswith('ввести '):
            var_name = line[6:].strip()
            if input_callback:
                user_input = input_callback("input", f"Введите значение для '{var_name}': ")
                try:
                    if '.' in user_input:
                        self.variables[var_name] = float(user_input)
                    elif user_input.isdigit():
                        self.variables[var_name] = int(user_input)
                    else:
                        self.variables[var_name] = user_input
                except:
                    self.variables[var_name] = user_input
        elif line.startswith('окно '):
            self.handle_window_command(line[4:].strip())
        elif line.startswith('прямоугольник '):
            self.handle_rectangle_command(line[13:].strip())
        elif line.startswith('круг '):
            self.handle_circle_command(line[4:].strip())
        elif line.startswith('линия '):
            self.handle_line_command(line[5:].strip())
        elif line.startswith('текст '):
            self.handle_text_command(line[5:].strip())
        elif line.startswith('задержка '):
            self.handle_delay_command(line[8:].strip())
        elif line.startswith('очистить '):
            self.handle_clear_command(line[8:].strip())
        elif line.startswith('установить_обработчик '):
            self.handle_set_handler(line[20:].strip(), event_callback)
        elif line.startswith('мышь_х()'):
            if event_callback:
                self.last_mouse_x = event_callback("get_mouse_x", "")
                self.variables['мышь_х'] = self.last_mouse_x
        elif line.startswith('мышь_у()'):
            if event_callback:
                self.last_mouse_y = event_callback("get_mouse_y", "")
                self.variables['мышь_у'] = self.last_mouse_y
        elif line.startswith('мышь_нажата()'):
            if event_callback:
                self.last_mouse_pressed = event_callback("get_mouse_pressed", "")
                self.variables['мышь_нажата'] = self.last_mouse_pressed
        elif line.startswith('обновить_экран()'):
            command = ('update',)
            self.graphics_commands.append(command)
            if self.graphics_callback:
                self.graphics_callback([command])
    
    # Графические команды с немедленной отправкой
    def handle_window_command(self, params):
        """окно ширина высота [заголовок]"""
        parts = params.split()
        if len(parts) >= 2:
            width = self.evaluate_expression(parts[0])
            height = self.evaluate_expression(parts[1])
            title = "Окно Ri" if len(parts) < 3 else " ".join(parts[2:])
            command = ('window', width, height, title)
            self.graphics_commands.append(command)
            self.has_graphics = True
            # Немедленно отправляем команду
            if self.graphics_callback:
                self.graphics_callback([command])
    
    def handle_rectangle_command(self, params):
        """прямоугольник x y ширина высота [цвет]"""
        parts = params.split()
        if len(parts) >= 4:
            x = self.evaluate_expression(parts[0])
            y = self.evaluate_expression(parts[1])
            width = self.evaluate_expression(parts[2])
            height = self.evaluate_expression(parts[3])
            color = "черный" if len(parts) < 5 else parts[4]
            command = ('rectangle', x, y, width, height, color)
            self.graphics_commands.append(command)
            self.has_graphics = True
            # Немедленно отправляем команду
            if self.graphics_callback:
                self.graphics_callback([command])
    
    def handle_circle_command(self, params):
        """круг x y радиус [цвет]"""
        parts = params.split()
        if len(parts) >= 3:
            x = self.evaluate_expression(parts[0])
            y = self.evaluate_expression(parts[1])
            radius = self.evaluate_expression(parts[2])
            color = "черный" if len(parts) < 4 else parts[4]
            command = ('circle', x, y, radius, color)
            self.graphics_commands.append(command)
            self.has_graphics = True
            # Немедленно отправляем команду
            if self.graphics_callback:
                self.graphics_callback([command])
    
    def handle_line_command(self, params):
        """линия x1 y1 x2 y2 [цвет]"""
        parts = params.split()
        if len(parts) >= 4:
            x1 = self.evaluate_expression(parts[0])
            y1 = self.evaluate_expression(parts[1])
            x2 = self.evaluate_expression(parts[2])
            y2 = self.evaluate_expression(parts[3])
            color = "черный" if len(parts) < 5 else parts[4]
            command = ('line', x1, y1, x2, y2, color)
            self.graphics_commands.append(command)
            self.has_graphics = True
            # Немедленно отправляем команду
            if self.graphics_callback:
                self.graphics_callback([command])
    
    def handle_text_command(self, params):
        """текст x y "текст" [цвет]"""
        text_match = re.search(r'"([^"]*)"', params)
        if text_match:
            text = text_match.group(1)
            params_without_text = params.replace(f'"{text}"', '').strip()
            parts = params_without_text.split()
            if len(parts) >= 2:
                x = self.evaluate_expression(parts[0])
                y = self.evaluate_expression(parts[1])
                color = "черный" if len(parts) < 3 else parts[2]
                command = ('text', x, y, text, color)
                self.graphics_commands.append(command)
                self.has_graphics = True
                # Немедленно отправляем команду
                if self.graphics_callback:
                    self.graphics_callback([command])
    
    def handle_delay_command(self, params):
        """задержка миллисекунды"""
        try:
            ms = self.evaluate_expression(params)
            time.sleep(ms / 1000.0)
        except:
            pass
    
    def handle_clear_command(self, params):
        """очистить [цвет]"""
        color = "белый" if not params else params
        command = ('clear', color)
        self.graphics_commands.append(command)
        self.has_graphics = True
        # Немедленно отправляем команду
        if self.graphics_callback:
            self.graphics_callback([command])
    
    def handle_set_handler(self, params, event_callback):
        """установить_обработчик событие функция"""
        parts = params.split()
        if len(parts) >= 2:
            event_type = parts[0]
            handler_name = parts[1]
            if event_callback:
                event_callback("set_handler", f"{event_type}:{handler_name}")
    
    # Встроенные функции (новое в 4.7.1)
    @property
    def builtin_functions(self):
        return {
            'случайно': self.builtin_random,
            'длина': self.builtin_length,
            'корень': self.builtin_sqrt,
            'синус': self.builtin_sin,
            'косинус': self.builtin_cos,
            'округлить': self.builtin_round,
            'строка': self.builtin_str,
            'число': self.builtin_num,
            'тип': self.builtin_type,
            'время': self.builtin_time,
            'список_длина': self.builtin_list_length,
            'элемент': self.builtin_list_element,
        }
    
    def call_builtin_function(self, line):
        """Вызывает встроенную функцию"""
        func_name = line.split('(')[0].strip()
        args_str = line.split('(')[1].split(')')[0].strip()
        
        if func_name in self.builtin_functions:
            args = []
            if args_str:
                for arg in args_str.split(','):
                    args.append(self.evaluate_expression(arg.strip()))
            
            return self.builtin_functions[func_name](*args)
        return None
    
    def builtin_random(self, min_val=0, max_val=1):
        """случайно(min, max) - случайное число в диапазоне"""
        return random.randint(int(min_val), int(max_val))
    
    def builtin_length(self, value):
        """длина(value) - длина строки или списка"""
        if isinstance(value, str):
            return len(value)
        elif value in self.lists:
            return len(self.lists[value])
        return 0
    
    def builtin_sqrt(self, value):
        """корень(value) - квадратный корень"""
        return math.sqrt(float(value))
    
    def builtin_sin(self, value):
        """синус(value) - синус угла в радианах"""
        return math.sin(float(value))
    
    def builtin_cos(self, value):
        """косинус(value) - косинус угла в радианах"""
        return math.cos(float(value))
    
    def builtin_round(self, value, decimals=0):
        """округлить(value, decimals) - округление числа"""
        return round(float(value), int(decimals))
    
    def builtin_str(self, value):
        """строка(value) - преобразование в строку"""
        return str(value)
    
    def builtin_num(self, value):
        """число(value) - преобразование в число"""
        try:
            if '.' in str(value):
                return float(value)
            return int(value)
        except:
            return 0
    
    def builtin_type(self, value):
        """тип(value) - тип переменной"""
        if isinstance(value, int):
            return "целое"
        elif isinstance(value, float):
            return "дробное"
        elif isinstance(value, str):
            return "строка"
        elif isinstance(value, bool):
            return "булево"
        return "неизвестно"
    
    def builtin_time(self):
        """время() - текущее время в миллисекундах"""
        return int(time.time() * 1000)
    
    def builtin_list_length(self, list_name):
        """список_длина(имя_списка) - длина списка"""
        if list_name in self.lists:
            return len(self.lists[list_name])
        return 0
    
    def builtin_list_element(self, list_name, index):
        """элемент(имя_списка, индекс) - элемент списка по индексу"""
        if list_name in self.lists and 0 <= index < len(self.lists[list_name]):
            return self.lists[list_name][index]
        return 0
    
    def evaluate_expression(self, expr: str):
        """Вычисляет значение выражения"""
        expr = expr.strip()
        
        # Проверяем, является ли выражение вызовом функции
        if '(' in expr and ')' in expr:
            func_name = expr.split('(')[0].strip()
            if func_name in self.builtin_functions:
                return self.call_builtin_function(expr)
        
        # Проверяем, является ли выражение доступом к элементу списка
        if '[' in expr and ']' in expr:
            list_name = expr.split('[')[0].strip()
            index_expr = expr.split('[')[1].split(']')[0].strip()
            
            if list_name in self.lists:
                try:
                    index = self.evaluate_expression(index_expr)
                    if 0 <= index < len(self.lists[list_name]):
                        return self.lists[list_name][index]
                except:
                    pass
        
        # Обработка скобок
        if '(' in expr and ')' in expr:
            while '(' in expr and ')' in expr:
                start = expr.rfind('(')
                end = expr.find(')', start)
                if start != -1 and end != -1:
                    inner = expr[start+1:end]
                    inner_result = self.evaluate_expression(inner)
                    expr = expr[:start] + str(inner_result) + expr[end+1:]
        
        # Логические операторы
        if ' не ' in expr or expr.startswith('не '):
            if ' не ' in expr:
                parts = expr.split(' не ')
                if len(parts) == 2:
                    value = self.evaluate_expression(parts[1].strip())
                    return not self._to_bool(value)
            elif expr.startswith('не '):
                value = self.evaluate_expression(expr[3:].strip())
                return not self._to_bool(value)
        
        if ' и ' in expr:
            parts = expr.split(' и ')
            result = True
            for part in parts:
                value = self.evaluate_expression(part.strip())
                result = result and self._to_bool(value)
                if not result:
                    break
            return result
        
        if ' или ' in expr:
            parts = expr.split(' или ')
            result = False
            for part in parts:
                value = self.evaluate_expression(part.strip())
                result = result or self._to_bool(value)
                if result:
                    break
            return result
        
        # Сравнения
        comparisons = ['>=', '<=', '==', '!=', '>', '<']
        for op in comparisons:
            if op in expr:
                parts = expr.split(op)
                if len(parts) == 2:
                    left = self._evaluate_simple(parts[0].strip())
                    right = self._evaluate_simple(parts[1].strip())
                    
                    if op == '>':
                        return left > right
                    elif op == '<':
                        return left < right
                    elif op == '>=':
                        return left >= right
                    elif op == '<=':
                        return left <= right
                    elif op == '==':
                        return left == right
                    elif op == '!=':
                        return left != right
        
        # Арифметические операции
        if '+' in expr:
            parts = expr.split('+')
            result = 0
            for part in parts:
                result += self._evaluate_simple(part.strip())
            return result
        
        if '-' in expr and expr.count('-') == 1 and not expr.startswith('-'):
            parts = expr.split('-')
            if len(parts) == 2:
                return self._evaluate_simple(parts[0].strip()) - self._evaluate_simple(parts[1].strip())
        
        if '*' in expr:
            parts = expr.split('*')
            result = 1
            for part in parts:
                result *= self._evaluate_simple(part.strip())
            return result
        
        if '/' in expr:
            parts = expr.split('/')
            if len(parts) == 2:
                denominator = self._evaluate_simple(parts[1].strip())
                if denominator != 0:
                    return self._evaluate_simple(parts[0].strip()) / denominator
                return 0
        
        if '^' in expr:
            parts = expr.split('^')
            if len(parts) == 2:
                base = self._evaluate_simple(parts[0].strip())
                exponent = self._evaluate_simple(parts[1].strip())
                return base ** exponent
        
        # Если ничего не подошло, пробуем как простое значение
        return self._evaluate_simple(expr)
    
    def _evaluate_simple(self, expr: str):
        """Вычисляет простое значение"""
        expr = expr.strip()
        
        if expr.startswith('"') and expr.endswith('"'):
            return expr[1:-1]
        
        if expr.startswith("'") and expr.endswith("'"):
            return expr[1:-1]
        
        # Проверяем, является ли выражение списком
        if expr.startswith('[') and expr.endswith(']'):
            # Это список, но мы его уже обработали в handle_list_declaration
            # Здесь просто возвращаем строковое представление
            return expr
        
        try:
            if '.' in expr:
                return float(expr)
            else:
                return int(expr)
        except:
            pass
        
        if expr in self.variables:
            return self.variables[expr]
        
        # Проверяем списки
        if expr in self.lists:
            return f"список[{len(self.lists[expr])} элементов]"
        
        if expr.lower() == 'истина':
            return True
        elif expr.lower() == 'ложь':
            return False
        
        # Проверяем функции мыши
        if expr == 'мышь_х':
            return self.last_mouse_x
        elif expr == 'мышь_у':
            return self.last_mouse_y
        elif expr == 'мышь_нажата':
            return self.last_mouse_pressed
        
        return 0
    
    def _to_bool(self, value):
        """Преобразует значение в булево"""
        if isinstance(value, bool):
            return value
        elif isinstance(value, (int, float)):
            return value != 0
        elif isinstance(value, str):
            return value.lower() not in ['', '0', 'ложь', 'false']
        else:
            return bool(value)
    
    # Методы отладки
    def add_breakpoint(self, line_num):
        """Добавляет точку останова"""
        self.breakpoints.add(line_num)
    
    def remove_breakpoint(self, line_num):
        """Удаляет точку останова"""
        if line_num in self.breakpoints:
            self.breakpoints.remove(line_num)
    
    def pause_execution(self):
        """Приостанавливает выполнение"""
        self.is_paused = True
    
    def continue_execution(self):
        """Продолжает выполнение"""
        self.is_paused = False
        self.step_mode = "run"
    
    def step_over(self):
        """Шаг вперед (не заходя в функции)"""
        self.is_paused = False
        self.step_mode = "step_over"
        self.step_depth = len(self.call_stack)
    
    def step_into(self):
        """Шаг внутрь (заходит в функции)"""
        self.is_paused = False
        self.step_mode = "step_into"
    
    def step_out(self):
        """Шаг наружу (выходит из функции)"""
        self.is_paused = False
        self.step_mode = "step_out"
        self.step_depth = max(0, len(self.call_stack) - 1)
    
    def get_variables(self):
        """Возвращает текущие переменные для отладчика"""
        return self.variables.copy()
    
    def get_lists(self):
        """Возвращает текущие списки для отладчика"""
        return self.lists.copy()
    
    def get_call_stack(self):
        """Возвращает стек вызовов"""
        return self.call_stack.copy()

def run_ri_code(code: str, graphics_callback=None, input_callback=None, 
                event_callback=None, debug_callback=None) -> str:
    """Запускает код на Ri"""
    compiler = RiCompiler()
    return compiler.execute(code, graphics_callback, input_callback, 
                          event_callback, debug_callback)
