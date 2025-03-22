### Пример использования

```python
import cappa_sqlplag

raw_code1 = "Select distinct maker, price From Product, Printer Where Product.model = Printer.model and color = 'y' and price = (Select min(price) From Printer Where color = 'y')"
raw_code2 = "Select distinct maker, price From Product, Printer Where color='y' and price=(Select min(price) From Printer Where color='y') and Product.model = Printer.model"

sqlplag = cappa_sqlplag.SQLPlag(ref_code=raw_code1, candidate_code=raw_code2) 
similarity = sqlplag.cte_similarity_percentage()

print("Процент схожести:", similarity)
```

### Совместимость с версиями Python

* [Python](http://www.python.com) - v3
