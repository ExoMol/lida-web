import requests

exomol_all_raw = requests.get('https://www.exomol.com/db/exomol.all').text

print(exomol_all_raw)
