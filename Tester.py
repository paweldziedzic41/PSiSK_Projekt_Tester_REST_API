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
import matplotlib.pyplot as plt
import tkinter as tk

def main():
    
    thread_local = local()
    root = tk.Tk()

    start = 0.0
    end = 0.0
    l_request_body = []
    l_request_time = []
    l_request = []
    l_response = []
    l_response_data = []
    l_status = []
    l_request_size = []
    l_errors = []
    l_json_format = []
    df_time_req = pd.DataFrame()


    ### Ustalamy nagłówek zapytania wysylanego do serwera
    headers = {'User-Agent': 'python-requests/3.28.1',
                'Accept-Encoding': 'gzip, deflate',
                'Accept': '*/*',
                'Connection': 'keep-alive',
                'content-type': 'application/json',
                'x-test': 'true'} 


    def dane(response):
        l_request_body.append(response.request.body)
        l_request_time.append(round(float(response.elapsed.microseconds)*pow(10,-3),2))
        l_status.append(response.status_code)
        l_response_data.append(float(response.headers['Content-Length']))
        l_json_format.append(response.json())
        l_response.append(response.headers)
        l_request.append(response.request.headers)
        l_request_size.append(float(response.request.headers['Content-Length']))


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
            body = 'GET', url ,' GET data, [no cookies]'
            body = str(body)
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
        ### Ustalamy cialo zapytania wysylanego na serwer
        with ThreadPoolExecutor(max_workers=350) as executor:
            executor.map(get_method,urls)

    def prepare_graph_data():
        df_time_req["Nr_pakietu"] = list(range(0,len(l_request_time)))
        df_time_req["Czas_wysyłania_pakietow"] = l_request_time    
        df_time_req["Ilosc_Kb_odppowedzi"] = l_response_data
        df_time_req["Ilosc_Kb/s"] = df_time_req["Ilosc_Kb_odppowedzi"]/df_time_req["Czas_wysyłania_pakietow"]
        return df_time_req


    def graph_throughput(): 
        plt.plot(df_time_req["Nr_pakietu"],df_time_req["Ilosc_Kb/s"], '-', label = 'Przepustowość', color = 'green')
        plt.xlabel("Ilość pakietów")
        plt.ylabel("Czas (ms)")
        plt.title('Wykres przepustowości')
        plt.legend(loc = "upper left")
        plt.show()



    def graph_packet_sent_time():
        plt.plot(df_time_req['Nr_pakietu'],df_time_req['Czas_wysyłania_pakietow'],'ro', label = 'Pakiet', color = "Darkblue")
        plt.plot(df_time_req['Nr_pakietu'],df_time_req['Czas_wysyłania_pakietow'],'-', label = 'Różnice czasowe',color = "Lightblue")            
        plt.xlabel("Ilość pakietów")
        plt.ylabel("Czas (ms)")
        plt.title('Wykres czasu odpowiedzi pakietow')
        plt.legend(loc = "upper left")
        plt.show()

    def show_info(start, end, url_list):
        tk.Label(root,text=f'Wyslano {len(url_list)} zapytan w {round(end - start,2)} sekund', anchor=tk.W).grid()
        tk.Label(root,text=f"Sredni czas wysylania pakietu: {round(sum(l_request_time)/len(l_request_time),2)} ms  |  Maksymalny czas wysylania pakietu: {max(l_request_time)} ms   |   Minmalny czas wysylania pakietu: {min(l_request_time)} ms").grid()
        tk.Label(root,text=f"Ilosc pakietow dostarczonych i otrzymanych: {len(l_status)}  |  Ilosc bledow:  {len(l_errors)}").grid()
        tk.Label(root,text=f"Ilosc pakietow wyslanych na sekunde: {round((len(l_status)+len(l_errors))/round(end - start,2),2)}   |  Ilosc KB/s:  {round((sum(l_response_data)/1024)/round(end - start,2),2)}   |  Wyslano KB/s: {round((sum(l_request_size)/1024)/round(end - start,2),2)}").grid()
        b1 = tk.Button(root, text="Wykres 2", command = graph_throughput)
        b1.place(x=340, y=305)
        b2 = tk.Button(root, text="Dodatkowe informacje", command = show_additional_info)
        b2.place(x=410, y=305)
        b3 = tk.Button(root, text="Wykres 1", command = graph_packet_sent_time)
        b3.place(x=270, y=305)
        frame1 = tk.Frame(root, width=780, height=5, bd=5, relief="sunken")
        frame1.grid(pady = (40,15))
        b4 = tk.Button(root, text="Odśwież okno", command = refresh_window)
        b4.grid()
        

    def show_additional_info():
        new_window = tk.Toplevel(root)
        new_window.title("Dodatkowe informacje")
        new_window.resizable(False, False)
        main_frame = tk.Frame(new_window)
        main_frame.pack(fill=tk.BOTH, expand = 1)

        my_canvas = tk.Canvas(main_frame)
        my_canvas.pack(side=tk.LEFT,fill=tk.BOTH,expand=1)

        scrollbar = tk.Scrollbar(main_frame, orient=tk.VERTICAL, command=my_canvas.yview)
        scrollbar.pack(side=tk.RIGHT,fill=tk.Y)

        my_canvas.configure(yscrollcommand=scrollbar.set)
        my_canvas.bind('<Configure>', lambda e: my_canvas.configure(scrollregion=my_canvas.bbox("all")))

        second_frame = tk.Frame(my_canvas)

        my_canvas.create_window((0,0), window = second_frame, anchor=tk.N)

        new_window.geometry('540x480')
        tk.Label(second_frame,text=f"Przykład formatu JSON:", justify="center", font= 12).pack(pady= (0,2))
        tk.Label(second_frame, text=f"{l_json_format[0]}", wraplength=500).pack()
        tk.Label(second_frame,text=f"Przykladowy opis zwroconego zapytania:", justify="center", font= 12).pack(pady= (0,2))
        tk.Label(second_frame, text=f"{l_response[0]}", wraplength=500).pack()
        tk.Label(second_frame,text=f"Przykladowy header zapytania wysylanego na serwer:", justify="center", font= 12).pack(pady= (0,2))
        tk.Label(second_frame, text=f"{l_request[0]}", wraplength=500).pack()
        tk.Label(second_frame,text=f"Przykladowe body zapytania wysylanego na serwer:", justify="center", font= 12).pack(pady= (0,2))
        tk.Label(second_frame, text=f"{l_request_body[0]}", wraplength=500).pack()
        if len(l_errors) > 0:
            tk.Label(second_frame,text=f"Przykldowy opis bledu:",  justify="left", font= 12).pack(pady= (0,2))
            tk.Label(second_frame, text=f"{l_errors[0]}", wraplength=500).pack()


    def function_time():
        b["state"] = tk.DISABLED
        e_value = e.get()
        e1_value = e1.get()
        e1_value = int(e1_value)
        url_list = [e_value]*e1_value
        start = time.time()
        download_all(url_list)
        end = time.time()
        prepare_graph_data()
        show_info(start, end, url_list)


    def refresh_window():
        # Odśwież okno
        root.destroy()
        root.update()
        main()



    ### Rozmiar okna
    root.geometry('780x480')
    root.title("Test wydajnościowy")
    ### Rozszerzanie ekranu
    root.resizable(False, False)

    ### Nagłówek
    l = tk.Label(root, text = 'Test wydajnościowy', anchor="center")
    l.config(font = ("Helvetica", 20))
    l.grid(pady= (0,15))
    ### Wczytaj nagłowek

    ### Wpisz Adres serwera
    l1 = tk.Label(root, text="Wpisz adres servera:", justify="left")
    l1.config(font = ("Helvetica", 8))

    e = tk.Entry(root, justify="left")
    l1.grid()
    e.grid(pady = (0,10))

    ### Wpisz ilosc zapytań

    l2 = tk.Label(root, text="Wpisz ilość zapytań:", justify="left")
    l2.config(font = ("Helvetica", 8))
    e1 = tk.Entry(root, justify="left")

    l2.grid()
    e1.grid(pady = (0,15))

    ### Przycisk
    b = tk.Button(root, text= 'Testuj', command = function_time)
    b.grid(pady = (0,15))

    ### Pasek
    frame = tk.Frame(root, width=780, height=5, bd=5, relief="sunken")
    frame.grid(pady = (0,15))


    root.mainloop()

main()
