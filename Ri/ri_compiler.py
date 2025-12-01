import re
import sys
import math
import time
from typing import List, Dict, Any, Optional
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
        
    def execute(self, code: str, graphics_callback=None, input_callback=None, event_callback=None):
        """Выполняет код на Ri"""
        self.variables = {}
        self.output_lines = []
        self.graphics_commands = []
        self.has_graphics = False
        self.event_handlers = {}
        
        lines = code.strip().split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            if not line or line.startswith('//'):
                i += 1
                continue
            
            if '//' in line:
                line = line.split('//')[0].strip()
            
            try:
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
                    
                elif line.startswith('окно '):
                    self.handle_window_command(line[4:].strip())
                    self.has_graphics = True
                    
                elif line.startswith('прямоугольник '):
                    self.handle_rectangle_command(line[13:].strip())
                    self.has_graphics = True
                    
                elif line.startswith('круг '):
                    self.handle_circle_command(line[4:].strip())
                    self.has_graphics = True
                    
                elif line.startswith('линия '):
                    self.handle_line_command(line[5:].strip())
                    self.has_graphics = True
                    
                elif line.startswith('текст '):
                    self.handle_text_command(line[5:].strip())
                    self.has_graphics = True
                    
                elif line.startswith('задержка '):
                    self.handle_delay_command(line[8:].strip())
                    
                elif line.startswith('очистить '):
                    self.handle_clear_command(line[8:].strip())
                    self.has_graphics = True
                    
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
                    # Извлекаем код клавиши
                    if ')' in line:
                        key_code = line[14:].split(')')[0].strip().strip('"\'')
                        if event_callback:
                            key_pressed = event_callback("get_key_pressed", key_code)
                            self.variables[f'клавиша_{key_code}'] = key_pressed
                    
                elif line.startswith('обновить_экран()'):
                    self.graphics_commands.append(('update',))
                    
                elif line.startswith('остановить()'):
                    break
                    
                elif line == 'конец':
                    pass
                    
                elif line == 'иначе':
                    pass
                    
                else:
                    # Пытаемся обработать как присваивание без 'перем'
                    if '=' in line:
                        parts = line.split('=')
                        if len(parts) == 2:
                            var_name = parts[0].strip()
                            expr = parts[1].strip()
                            value = self.evaluate_expression(expr)
                            self.variables[var_name] = value
                            
            except Exception as e:
                self.output_lines.append(f"Ошибка в строке {i+1}: {str(e)}")
                
            i += 1
        
        # Если есть графика, отправляем команды
        if self.has_graphics and graphics_callback:
            graphics_callback(self.graphics_commands)
        
        return '\n'.join(self.output_lines)
    
    def handle_var_declaration(self, line):
        """Обработка объявления переменной"""
        if '=' in line:
            parts = line.split('=')
            var_name = parts[0].strip()
            expr = parts[1].strip()
            value = self.evaluate_expression(expr)
            self.variables[var_name] = value
    
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
        max_iterations = 10000  # Увеличили для игр
        
        while self.evaluate_expression(condition_expr) and iteration_count < max_iterations:
            # Выполняем тело цикла
            k = start_idx + 1
            while k < end_pos:
                self.execute_single_line(lines[k].strip(), input_callback, event_callback)
                k += 1
            
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
            self.has_graphics = True
        elif line.startswith('прямоугольник '):
            self.handle_rectangle_command(line[13:].strip())
            self.has_graphics = True
        elif line.startswith('круг '):
            self.handle_circle_command(line[4:].strip())
            self.has_graphics = True
        elif line.startswith('линия '):
            self.handle_line_command(line[5:].strip())
            self.has_graphics = True
        elif line.startswith('текст '):
            self.handle_text_command(line[5:].strip())
            self.has_graphics = True
        elif line.startswith('задержка '):
            self.handle_delay_command(line[8:].strip())
        elif line.startswith('очистить '):
            self.handle_clear_command(line[8:].strip())
            self.has_graphics = True
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
            self.graphics_commands.append(('update',))
    
    # Графические команды
    def handle_window_command(self, params):
        """окно ширина высота [заголовок]"""
        parts = params.split()
        if len(parts) >= 2:
            width = self.evaluate_expression(parts[0])
            height = self.evaluate_expression(parts[1])
            title = "Окно Ri" if len(parts) < 3 else " ".join(parts[2:])
            self.graphics_commands.append(('window', width, height, title))
    
    def handle_rectangle_command(self, params):
        """прямоугольник x y ширина высота [цвет]"""
        parts = params.split()
        if len(parts) >= 4:
            x = self.evaluate_expression(parts[0])
            y = self.evaluate_expression(parts[1])
            width = self.evaluate_expression(parts[2])
            height = self.evaluate_expression(parts[3])
            color = "черный" if len(parts) < 5 else parts[4]
            self.graphics_commands.append(('rectangle', x, y, width, height, color))
    
    def handle_circle_command(self, params):
        """круг x y радиус [цвет]"""
        parts = params.split()
        if len(parts) >= 3:
            x = self.evaluate_expression(parts[0])
            y = self.evaluate_expression(parts[1])
            radius = self.evaluate_expression(parts[2])
            color = "черный" if len(parts) < 4 else parts[3]
            self.graphics_commands.append(('circle', x, y, radius, color))
    
    def handle_line_command(self, params):
        """линия x1 y1 x2 y2 [цвет]"""
        parts = params.split()
        if len(parts) >= 4:
            x1 = self.evaluate_expression(parts[0])
            y1 = self.evaluate_expression(parts[1])
            x2 = self.evaluate_expression(parts[2])
            y2 = self.evaluate_expression(parts[3])
            color = "черный" if len(parts) < 5 else parts[4]
            self.graphics_commands.append(('line', x1, y1, x2, y2, color))
    
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
                self.graphics_commands.append(('text', x, y, text, color))
    
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
        self.graphics_commands.append(('clear', color))
    
    def handle_set_handler(self, params, event_callback):
        """установить_обработчик событие функция"""
        parts = params.split()
        if len(parts) >= 2:
            event_type = parts[0]
            handler_name = parts[1]
            if event_callback:
                event_callback("set_handler", f"{event_type}:{handler_name}")
    
    def evaluate_expression(self, expr: str):
        """Вычисляет значение выражения"""
        expr = expr.strip()
        
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
        
        # Если ничего не подошло, пробуем как простое значение
        return self._evaluate_simple(expr)
    
    def _evaluate_simple(self, expr: str):
        """Вычисляет простое значение"""
        expr = expr.strip()
        
        if expr.startswith('"') and expr.endswith('"'):
            return expr[1:-1]
        
        try:
            if '.' in expr:
                return float(expr)
            else:
                return int(expr)
        except:
            pass
        
        if expr in self.variables:
            return self.variables[expr]
        
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
def run_ri_code(code: str, graphics_callback=None, input_callback=None, event_callback=None) -> str:
    """Запускает код на Ri"""
    compiler = RiCompiler()
    return compiler.execute(code, graphics_callback, input_callback, event_callback)
