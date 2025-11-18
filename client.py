from cycletls import CycleTLS


cycle = CycleTLS()
result = cycle.get("https://ja3er.com/json")
print(result)
cycle.close()
