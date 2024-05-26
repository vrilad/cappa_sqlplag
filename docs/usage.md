### Пример использования

```python
import cappa_sqlplag

raw_code1 = "Select name, id_author From users join authors on id_user = id_author where id_user in (Select max(id_user) From users) Group by id_user"
raw_code2 = "Select name, id_author From authors join users on id_user = id_author where id_user = (Select max(id_user) From users) Group by id_user"

sqlplag = cappa_sqlplag.SQLPlag(ref_code=raw_code1, candidate_code=raw_code2) 
similarity = sqlplag.similarity_percentage()
print("Процент схожести:", similarity)
```

### Совместимость с версиями Python

* [Python](http://www.python.com) - v3
