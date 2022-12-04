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

l_request_body = []
l_request_time = []
l_request = []
l_response = []
l_response_data = []
l_status = []
l_reqeust_time = []
l_errors = []
l_json_format = []
url_list = ["http://127.0.0.1:3000/drinks"]*1000

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
    l_request_body.append(response.request.body)
    l_reqeust_time.append(round(float(response.elapsed.microseconds)*pow(10,-3),2))
    l_status.append(response.status_code)
    l_response_data.append(float(response.headers['Content-Length']))
    l_json_format.append(response.json())
    l_response.append(response.headers)
    l_request.append(response.request.headers)
    l_request_time.append(float(response.request.headers['Content-Length']))

###
# Funkcja get_session pozwala na utworzenie jednego obiektu Session 
# z pakietu threading dzięki czemu n-wątków będzie dzielić
# jeden obiekt Session zamiast tworzyć dla każdego wątku pojedynczy obiekt
###
def get_session():
    if not hasattr(thread_local,'session'):
        thread_local.session = requests.Session()
    return thread_local.session

def get_method(url):
        session = get_session()
        try:
            with session.get(url,timeout=(3,0.5), headers=headers, data=body) as response:
                dane(response)
        except requests.exceptions.ReadTimeout as e:        
            l_errors.append(e)
        except requests.exceptions.ConnectionError as cr:
            l_errors.append(cr)
            
###
# urls:list - ta czesc kodu mowi ze argumentem przekazywanym do funkcji
# powinna byc lista.
# ThreadPoolExecutor(max_workers=60) - tworzymy wątki 
# funkcja executor.map - przyjmuje jako argumnety funkcje get_method
# oraz całą liste linków url jak iteratory
###
def download_all(urls):
    with ThreadPoolExecutor(max_workers=350) as executor:
        executor.map(get_method,url_list)


start = time.time()
download_all(url_list)
end = time.time()
print("\n")
print(f'Wyslano {len(url_list)} zapytan w {round(end - start,2)} sekund')
print("Sredni czas wysylania pakietu: ",round(sum(l_reqeust_time)/len(l_reqeust_time),2)," ms")
print("Maksymalny czas wysylania pakietu: ",max(l_reqeust_time)," ms")
print("Minmalny czas wysylania pakietu: ",min(l_reqeust_time)," ms")
print("Ilosc pakietow dostarczonych i otrzymanych",len(l_status))
print("Ilosc bledow: ", len(l_errors))
print("Ilosc pakietow wyslanych na sekunde: ", round((len(l_status)+len(l_errors))/round(end - start,2),2))
print("Ilosc KB/s: ", round((sum(l_response_data)/1024)/round(end - start,2),2))
print("Wyslano KB/s: ", round((sum(l_request_time)/1024)/round(end - start,2),2),"\n")
print("Przykład formatu JSON: \n", l_json_format[0],"\n")
print("Przykladowy opis zwroconego zapytania: \n", l_response[0], "\n")
print("Przykladowy header zapytania wysylanego na serwer: \n", l_request[0], "\n" )
print("Przykladowe body zapytania wysylanego na serwer: \n", l_request_body[0], "\n" )
if len(l_errors) > 0:
    df_errors = pd.DataFrame(columns=["Opis_bledu"])
    df_errors["Opis_bledu"] = l_errors
    print("Przykldowy opis bledu: \n",df_errors["Opis_bledu"][1],"\n" )
    print(df_errors)
    df_errors.to_csv(r'C:\Users\gosc\Documents\PSISK_Projekt\REST_API\l_errorsow.csv')
    




