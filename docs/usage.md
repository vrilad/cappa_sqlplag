### Пример использования

```python
import cappa_sqlplag

raw_code1 = "Select distinct maker, price From Product, Printer Where Product.model = Printer.model and color = 'y' and price = (Select min(price) From Printer Where color = 'y')"
raw_code2 = "Select distinct maker, price From Product, Printer Where color='y' and price=(Select min(price) From Printer Where color='y') and Product.model = Printer.model"

sqlplag = cappa_sqlplag.SQLPlag(ref_code=raw_code1, candidate_code=raw_code2) 
similarity = sqlplag.similarity_percentage()

print("Процент схожести:", similarity)

query1 = "with x as (select id_psg, count(town_to) to_m , min(date(date) + time_out::time), min(town_from) as home from pass_in_trip join trip on pass_in_trip.trip_no = trip.trip_no where town_to = 'Moscow' group by id_psg having min(town_from) != 'Moscow') select name, to_m from x join passenger on x.id_psg = passenger.id_psg where to_m > 1"
query2 = "With a as (Select id_psg, town_from, town_to, date::date+time_out::time as dt From Pass_in_trip join Trip on Trip.trip_no = Pass_in_trip.trip_no Where not town_from = 'Moscow'), b as (Select id_psg, count(town_to) to_Moscow From a Where dt in (Select min(dt) From a Group by id_psg) and town_to = 'Moscow' Group by id_psg) Select name, to_Moscow From Passenger join b on Passenger.id_psg = b.id_psg Where to_Moscow > 1"

sqlplag = cappa_sqlplag.SQLPlag(ref_code=query1, candidate_code=query2) 
similarity = sqlplag.cte_similarity_percentage()

print("Процент схожести:", similarity)

```

### Совместимость с версиями Python

* [Python](http://www.python.com) - v3
