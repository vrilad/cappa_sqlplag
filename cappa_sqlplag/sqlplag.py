import re

class SQLPlag:

    def __init__(self, ref_code: str, candidate_code: str):
        
        self.ref_code = ref_code
        self.candidate_code = candidate_code

    def process_match(self, match: str) -> list:

        matches = []

        group_match = match.group(1)
        processed_match = group_match.strip().split(',')

        for fragment in processed_match:
            elem = fragment.strip()
            matches.append(elem) 

        return matches

    def split_sql_statement(self, raw_code: str) -> list:

        select_pattern = re.compile(r'SELECT(.*?)FROM', re.IGNORECASE | re.DOTALL)
        from_pattern = re.compile(r'FROM(.*?)WHERE|GROUP BY|ORDER BY|LIMIT', re.IGNORECASE | re.DOTALL)
        where_pattern = re.compile(r'WHERE(.*)', re.IGNORECASE | re.DOTALL)

        select_match = select_pattern.search(raw_code)
        from_match = from_pattern.search(raw_code)
        where_match = where_pattern.search(raw_code)

        columns = self.process_match(select_match)
        tables_and_conditions = self.process_match(from_match)

        where_body = where_match.group(1).strip() if where_match else ''

        statements = [columns, tables_and_conditions, where_body]

        return statements   
    
    
    def levenshtein_distance(self, s1: str, s2: str) -> int:
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
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    def similarity_percentage(self) -> int:

        query1 = self.ref_code.lower()
        query2 = self.candidate_code.lower()

        if query1.startswith('select') and query2.startswith('select'):
            parsed_query1 = self.split_sql_statement(query1)
            parsed_query2 = self.split_sql_statement(query2) 
                
        distance = self.levenshtein_distance(parsed_query1, parsed_query2)
        max_length = max(len(parsed_query1), len(parsed_query2))
        
        similarity = 1 - distance / max_length
        return int(similarity * 100)
