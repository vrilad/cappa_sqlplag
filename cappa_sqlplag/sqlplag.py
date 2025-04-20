import re
from difflib import SequenceMatcher
from typing import List, Tuple, Union

class SQLPlag:

    def __init__(self, ref_code: str, candidate_code: str):
        
        """
        Инициализирует объект SQLPlag с двумя SQL-запросами:
        эталонным (ref_code) и кандидатом на сравнение (candidate_code).
        """

        self.ref_code = ref_code
        self.candidate_code = candidate_code

    def normalize_sql(self, query: str) -> str:
        
        """
        Приводит SQL-запрос к нормализованному виду:
        - удаляет комментарии
        - удаляет лишние пробелы
        - приводит к нижнему регистру
        - стандартизирует кавычки и пробелы вокруг операторов
        """

        query_nocomments = re.sub(r'--.*?$', '', query, flags=re.MULTILINE) 
        query_nocomments = re.sub(r'/\*.*?\*/', '', query_nocomments, flags=re.DOTALL) 
        query_nospaces = re.sub(r'\s+', ' ', query_nocomments).strip()      
        query_lowercase = query_nospaces.lower()       
        query_noquotes = re.sub(r'["`]', "'", query_lowercase)         
        normalized_query = re.sub(r'\s*([=+\-*/%<>!()])\s*', r'\1', query_noquotes) 
        return normalized_query

    def tokenize_sql(self, query: str) -> List[str]:
        
        """
        Делит SQL-запрос на токены, корректно обрабатывая строковые литералы в кавычках.
        """

        tokens = []
        current_token = ""
        in_string = False
        string_quote = ""

        for char in query:
            match (char, in_string):
                case ("'", False) | ('"', False):
                    in_string = True
                    string_quote = char
                    if current_token:
                        tokens.append(current_token)
                        current_token = ""
                    current_token += char
                case (c, True) if c == string_quote:
                    in_string = False
                    current_token += c
                    tokens.append(current_token)
                    current_token = ""
                case (_, True):
                    current_token += char
                case (c, False) if c.isspace():
                    if current_token:
                        tokens.append(current_token)
                        current_token = ""
                case (_, False):
                    current_token += char

        if current_token:
            tokens.append(current_token)

        return tokens

    def parse_sql_structure(self, query: str) -> dict:
       
        """
        Извлекает основные части SQL-запроса: SELECT, FROM, WHERE, GROUP BY, ORDER BY, LIMIT
        Возвращает словарь с соответствующими списками или значениями.
        """

        structure = {
            'select': self._parse_section(query, r'select(.*?)from'),
            'from': self._parse_section(query, r'from(.*?)(where|group by|order by|limit|$)'),
            'where': self._parse_conditions_section(query, r'where(.*?)(group by|order by|limit|$)'),
            'group_by': self._parse_section(query, r'group by(.*?)(order by|limit|$)'),
            'order_by': self._parse_section(query, r'order by(.*?)(limit|$)'),
            'limit': self._parse_single_value(query, r'limit(.*)$')
        }
        return structure

    def _parse_section(self, query: str, pattern: str) -> List[str]:
        
        """
        Универсальный парсер секций (SELECT, FROM, GROUP BY, ORDER BY)
        по регулярному выражению, возвращает список элементов.
        """

        match = re.search(pattern, query, re.IGNORECASE | re.DOTALL)
        if match:
            return [item.strip() for item in match.group(1).split(',')]
        return []

    def _parse_conditions_section(self, query: str, pattern: str) -> List[Tuple[str, str, str]]:
        
        """
        Обрабатывает секцию WHERE с использованием parse_conditions().
        Возвращает список разобранных условий.
        """

        match = re.search(pattern, query, re.IGNORECASE | re.DOTALL)
        if match:
            return self.parse_conditions(match.group(1))
        return []

    def _parse_single_value(self, query: str, pattern: str) -> Union[str, None]:
       
        """
        Извлекает одиночное значение (например, LIMIT) по регулярному выражению.
        """

        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None

    def parse_conditions(self, conditions: str) -> List[Tuple[str, str, str]]:
        
        """
        Разбивает строку WHERE на отдельные условия и парсит каждое условие
        на левую и правую часть и оператор.
        """

        conditions = conditions.strip()
        if not conditions:
            return []

        fragments = self._split_logical_conditions(conditions)
        parsed_conditions = [self._parse_single_condition(cond) for cond in fragments]
        return parsed_conditions

    def _split_logical_conditions(self, condition_str: str) -> List[str]:
        
        """
        Разделяет строку условий WHERE по логическим операторам (&, |),
        игнорируя вложенные скобки.
        """

        fragments = []
        current = ""
        depth = 0

        for char in condition_str:
            if char == '(':
                depth += 1
            elif char == ')':
                depth -= 1

            if depth == 0 and char in ('&', '|') and current.strip():
                fragments.append(current.strip())
                current = ""
            else:
                current += char

        if current.strip():
            fragments.append(current.strip())

        return fragments

    def _parse_single_condition(self, condition: str) -> Tuple[str, str, str]:
        
        """
        Разбирает одно логическое условие на части: левая часть, оператор, правая часть.
        Возвращает кортеж (left, operator, right) или (cond, None, None), если не найдено.
        """

        for op in ('!=', '<=', '>=', '<>', '=', '<', '>', 'like', 'in'):
            if op in condition.lower():
                parts = condition.split(op)
                if len(parts) == 2:
                    left = parts[0].strip()
                    right = parts[1].strip()
                    return (left, op, right)
        return (condition.strip(), None, None)

    def weighted_levenshtein(self, s1: List[str], s2: List[str], weights: dict) -> float:
        
        """
        Вычисляет взвешенное расстояние Левенштейна между двумя списками токенов,
        учитывая веса разных типов токенов.
        """

        if len(s1) < len(s2):
            return self.weighted_levenshtein(s2, s1, weights)

        if len(s2) == 0:
            return sum(weights.get(type_, 1.0) for type_ in s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + weights.get(type(c1), 1.0)
                deletions = current_row[j] + weights.get(type(c2), 1.0)
                substitutions = previous_row[j] + (weights.get(type(c1), 1.0) if c1 != c2 else 0)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    def calculate_similarity(self) -> float:
        
        """
        Вычисляет итоговую метрику схожести между двумя SQL-запросами
        на основе структуры и токенов.
        """

        norm_ref = self.normalize_sql(self.ref_code)
        norm_candidate = self.normalize_sql(self.candidate_code)

        if norm_ref == norm_candidate:
            return 1.0

        tokens_ref = self.tokenize_sql(norm_ref)
        tokens_candidate = self.tokenize_sql(norm_candidate)

        struct_ref = self.parse_sql_structure(norm_ref)
        struct_candidate = self.parse_sql_structure(norm_candidate)

        structure_similarity = self._calculate_structure_similarity(struct_ref, struct_candidate)
        token_similarity = self._calculate_token_similarity(tokens_ref, tokens_candidate)

        total_similarity = 0.5 * structure_similarity + 0.5 * token_similarity
        return total_similarity

    def _calculate_structure_similarity(self, struct_ref: dict, struct_candidate: dict) -> float:
        
        """
        Вычисляет взвешенную структурную схожесть между двумя разобранными SQL-запросами.
        Сравниваются секции SELECT, FROM, WHERE и т.д.
        """
        
        weights = {
            'select': 0.3,
            'from': 0.3,
            'where': 0.3,
            'group_by': 0.1,
            'order_by': 0.1,
            'limit': 0.05
        }

        similarities = []
        for component, weight in weights.items():
            ref_comp = struct_ref.get(component, [])
            cand_comp = struct_candidate.get(component, [])

            if not ref_comp and not cand_comp:
                similarity = 1.0
            elif not ref_comp or not cand_comp:
                similarity = 0.0
            else:
                if isinstance(ref_comp, list) and isinstance(cand_comp, list):
                    set_ref = set(ref_comp)
                    set_cand = set(cand_comp)
                    intersection = set_ref & set_cand
                    union = set_ref | set_cand
                    similarity = len(intersection) / len(union) if union else 1.0
                else:
                    max_len = max(len(str(ref_comp)), len(str(cand_comp))) or 1
                    distance = self.levenshtein_distance(str(ref_comp), str(cand_comp))
                    similarity = 1 - distance / max_len

            similarities.append(similarity * weight)

        return sum(similarities)

    def _calculate_token_similarity(self, tokens_ref: List[str], tokens_candidate: List[str]) -> float:
        
        """
        Вычисляет схожесть между двумя списками токенов
        на основе нормализованного расстояния Левенштейна.
        """

        max_len = max(len(tokens_ref), len(tokens_candidate)) or 1
        distance = self.levenshtein_distance(tokens_ref, tokens_candidate)
        return 1 - distance / max_len

    def levenshtein_distance(self, s1: Union[str, List[str]], s2: Union[str, List[str]]) -> int:
        
        """
        Вычисляет обычное расстояние Левенштейна между строками или списками.
        """

        if len(s1) < len(s2):
            return self.levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (0 if c1 == c2 else 1)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    def similarity_percentage(self) -> int:
        
        """
        Возвращает итоговый процент схожести между SQL-запросами на основе calculate_similarity().
        """

        similarity = self.calculate_similarity()
        return int(round(similarity * 100))

    def tokenize(self, sql_query) -> List[str]:
        
        """
        Простая токенизация SQL-запроса с использованием регулярных выражений.
        """
        
        tokens = re.findall(r"\w+|[^\w\s]", sql_query.lower())
        return tokens

    def cte_similarity_percentage(self) -> int:
        
        """
        Альтернативный способ расчёта схожести SQL-запросов на основе SequenceMatcher
        и лексем, включая CTE (если есть).
        """
        query1 = self.ref_code.lower()
        query2 = self.candidate_code.lower()

        tokens1 = self.tokenize(query1)
        tokens2 = self.tokenize(query2)

        matcher = SequenceMatcher(None, tokens1, tokens2)
        similarity_ratio = matcher.ratio()

        similarity = similarity_ratio * 100

        return int(similarity)
