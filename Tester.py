import requests
from requests.sessions import Session
import time
### 
# Biblioteka concurrent.futures zapewnia wysokiej klasy interface 
# pozwalający na asynchroniczne wykonywanie operacji
# ThreadPoolExecutor - klasa pozwalająca na utworzenie wielu wątków
### 
from concurrent.futures import ThreadPoolExecutor
from threading import Thread,local
from requests.exceptions import Timeout
import json
import pandas as pd

i = 0
l_body_zapytania = []
l_czas_zapytan = []
l_zapytan = []
l_odpowiedzi = []
lista_rozmiaru_danych = []
lista_bit = []
lista_stat = []
lista_czas = []
lista_bled = []
l_json = []
url_list = ["https://api.github.com/some/endpoint"]*2000

### Zmienna thread_local będzie przechowywać obiekty sesji
thread_local = local()

### Ustalamy nagłówek zapytania wysylanego do serwera
headers = {'User-Agent': 'python-requests/3.28.1',
            'Accept-Encoding': 'gzip, deflate',
            'Accept': '*/*',
            'Connection': 'keep-alive',
            'content-type': 'application/json',
            'x-test': 'true'} 

### Ustalamy cialo zapytania wysylanego na serwer
body = 'GET', url_list[0] ,' GET data, [no cookies]'
body = str(body)

def dane(response):
    l_body_zapytania.append(response.request.body)
    lista_rozmiaru_danych.append(response.headers['Content-Length'])
    lista_czas.append(round(float(response.elapsed.microseconds)*pow(10,-3),2))
    lista_stat.append(response.status_code)
    lista_bit.append(float(response.headers['Content-Length']))
    l_json.append(response.json())
    l_odpowiedzi.append(response.headers)
    l_zapytan.append(response.request.headers)
    l_czas_zapytan.append(float(response.request.headers['Content-Length']))

###
# Funkcja get_session pozwala na utworzenie jednego obiektu Session 
# z pakietu threading dzięki czemu n-wątków będzie dzielić
# jeden obiekt Session zamiast tworzyć dla każdego wątku pojedynczy obiekt
###
def get_session() -> Session:
    if not hasattr(thread_local,'session'):
        thread_local.session = requests.Session()
    return thread_local.session

def download_link(url:str):
        session = get_session()
        try:
            with session.get(url,timeout=(3,0.2), headers=headers, data=body) as response:
                dane(response)
        except requests.exceptions.ReadTimeout as e:        
            lista_bled.append(e)
        except requests.exceptions.ConnectionError as cr:
            lista_bled.append(cr)
            
###
# urls:list - ta czesc kodu mowi ze argumentem przekazywanym do funkcji
# powinna byc lista.
# ThreadPoolExecutor(max_workers=60) - tworzymy wątki 
# funkcja executor.map - przyjmuje jako argumnety funkcje download_link
# oraz całą liste linków url jak iteratory
###
def download_all(urls:list):
    with ThreadPoolExecutor(max_workers=350) as executor:
        executor.map(download_link,url_list)


start = time.time()
download_all(url_list)
end = time.time()
print(i)
print("\n")
print(f'Wyslano {len(url_list)} zapytan w {round(end - start,2)} sekund')
print("Sredni czas wysylania pakietu: ",round(sum(lista_czas)/len(lista_czas),2)," ms")
print("Maksymalny czas wysylania pakietu: ",max(lista_czas)," ms")
print("Minmalny czas wysylania pakietu: ",min(lista_czas)," ms")
print("Ilosc pakietow dostarczonych i otrzymanych",len(lista_stat))
print("Ilosc bledow: ", len(lista_bled))
print("Ilosc pakietow wyslanych na sekunde: ", round((len(lista_stat)+len(lista_bled))/round(end - start,2),2))
print("Ilosc KB/s: ", round((sum(lista_bit)/1024)/round(end - start,2),2))
print("Wyslano KB/s: ", round((sum(l_czas_zapytan)/1024)/round(end - start,2),2),"\n")
print("Przykład formatu JSON: \n", l_json[0],"\n")
print("Przykladowy opis zwroconego zapytania: \n", l_odpowiedzi[0], "\n")
print("Przykladowy header zapytania wysylanego na serwer: \n", l_zapytan[0], "\n" )
print("Przykladowe body zapytania wysylanego na serwer: \n", l_body_zapytania[0], "\n" )
if len(lista_bled) > 0:
    df_errors = pd.DataFrame(columns=["Opis_bledu"])
    df_errors["Opis_bledu"] = lista_bled
    print(df_errors)
    #df_errors.to_csv(r'C:\Users\gosc\Documents\PSISK_Projekt\REST_API\lista_bledow.csv')
    #print("Przykladowy opis bledu: \n", lista_bled[0],"\n")
    

### kb = bytes / 1024

