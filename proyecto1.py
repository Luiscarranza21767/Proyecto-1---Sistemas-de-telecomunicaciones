import tkinter as tk
from tkinter import messagebox, ttk
from tkcalendar import DateEntry
import requests
import json
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime

# Constantes para los colores y estilos de la interfaz
DARK_BG = "#1e1e1e"  # Fondo oscuro
LIGHT_BG = "#2e2e2e"  # Fondo claro para entradas de texto
ACCENT_COLOR = "#00bcd4"  # Color de acento para botones y pestañas
TEXT_COLOR = "#e0e0e0"  # Color del texto
ENTRY_TEXT_COLOR = "#000000"  # Color del texto en entradas
BUTTON_TEXT_COLOR = "#000000"  # Color del texto en botones
TAB_TEXT_COLOR = "#000000"  # Color del texto en las pestañas

widgets = {}  # Diccionario para almacenar los widgets de la interfaz

# Funciones para crear y configurar la interfaz gráfica

def create_time_input(parent):
    """ Crea los controles de entrada para hora, minuto y segundo """
    time_frame = ttk.Frame(parent, style='TFrame')
    time_frame.pack(pady=5)
    
    time_width = 6
    # Crear controles de entrada para hora, minuto y segundo
    spin_hour = ttk.Spinbox(time_frame, from_=0, to=23, format="%02.0f", width=time_width, background=LIGHT_BG, foreground=ENTRY_TEXT_COLOR)
    spin_hour.grid(row=0, column=0, padx=1)
    spin_minute = ttk.Spinbox(time_frame, from_=0, to=59, format="%02.0f", width=time_width, background=LIGHT_BG, foreground=ENTRY_TEXT_COLOR)
    spin_minute.grid(row=0, column=1, padx=1)
    spin_second = ttk.Spinbox(time_frame, from_=0, to=59, format="%02.0f", width=time_width, background=LIGHT_BG, foreground=ENTRY_TEXT_COLOR)
    spin_second.grid(row=0, column=2, padx=1)
    
    return spin_hour, spin_minute, spin_second

def create_labeled_entry(parent, label_text, entry_width=30):
    """ Crea una entrada de texto con una etiqueta encima """
    ttk.Label(parent, text=label_text).pack(pady=(5, 0))
    entry = ttk.Entry(parent, width=entry_width)
    entry.pack(pady=5)
    return entry

def create_tab(notebook, tab_name, callback):
    """ Crea una pestaña en el notebook con una imagen de fondo y un marco interno """
    frame = ttk.Frame(notebook, style='TFrame')
    notebook.add(frame, text=tab_name)
    
    canvas = tk.Canvas(frame, bg=DARK_BG)
    canvas.pack(fill='both', expand=True)
    #canvas.create_image(0, 0, anchor="nw",  image=fondo_img)
    canvas.create_image(0, 0, anchor="nw")
    
    inner_frame = tk.Frame(canvas, bg=DARK_BG, bd=10, relief='flat')
    inner_frame.place(relx=0.5, rely=0.5, anchor='center', width=650, height=500)
    
    ttk.Label(inner_frame, text=tab_name, font=('Arial', 14, 'bold')).pack(pady=10)
    
    return inner_frame

# Funciones para manejo de datos y gráficos

def format_timestamp(date, time):
    """ Formatea la fecha y hora en el formato requerido por la API (YYYY-MM-DDTHH:MM:SS) """
    date_str = datetime.strptime(date, "%m/%d/%y").strftime("%Y-%m-%d")
    return f"{date_str}T{time}"

def generate_graph(url):
    """Genera un gráfico de red mejorado con variación en el tono de color de las aristas."""
    try:
        response = requests.get(url)
        response.raise_for_status()

        data = response.json()
        G = nx.DiGraph()
        main_node = None

        # Agregar aristas y encontrar el nodo principal
        for entry in data['data']['bgp_state']:
            path = entry['path']
            if not main_node:
                main_node = path[-1]  # Suponemos que el último nodo en el primer camino es el principal
            for i in range(len(path) - 1):
                G.add_edge(path[i+1], path[i])

        # Usar el layout de Spring para una disposición más ordenada
        pos = nx.spring_layout(G, k=500, iterations=10, scale=4)

        fig, ax = plt.subplots(figsize=(10, 10))

        # Dibujar los nodos
        node_sizes = [100 if node == main_node else 80 for node in G.nodes()]
        node_colors = ['red' if node == main_node else 'skyblue' for node in G.nodes()]

        nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color=node_colors, alpha=0.8, ax=ax)
        
        # Crear una gama de colores para las aristas
        edges = list(G.edges())
        num_edges = len(edges)
        cmap = plt.get_cmap('coolwarm')  # Puedes elegir un colormap diferente
        edge_colors = [cmap(i / num_edges) for i in range(num_edges)]
        
        nx.draw_networkx_edges(G, pos, width=0.5, alpha=0.7, arrows=True, edge_color=edge_colors, arrowsize=10, ax=ax)
        nx.draw_networkx_labels(G, pos, font_size=6, font_color='black', ax=ax)
        ax.set_title("Gráfico de red de nodos y caminos", fontsize=16)
        ax.axis('off')
        return fig
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP Error: {http_err}")
    except Exception as err:
        print(f"Error: {err}")
    return None

def generate_graph_bgp_play(url, filter_asn):
    """Genera un gráfico de red específico para la funcionalidad de BGP Play."""
    try:
        response = requests.get(url)
        response.raise_for_status()

        data = response.json()

        # Extraer el estado inicial y los eventos de actualización
        initial_state = data['data']['initial_state']
        d = data['data']

        # Crear un gráfico dirigido
        G = nx.DiGraph()

        # Añadir nodos y aristas al gráfico a partir del estado inicial
        for entry in initial_state:
            path = entry['path']
            for i in range(len(path) - 1):
                if path[0] == filter_asn:  # Filtrar los caminos que comienzan con 51519
                    G.add_edge(path[i+1], path[i], color='blue')

        # Dibujar el gráfico inicial una vez
        plt.figure(figsize=(12, 8))
        pos = nx.spring_layout(G)
        edges = G.edges(data=True)
        colors = [edge[2]['color'] for edge in edges]
        nx.draw(G, pos, with_labels=True, node_size=500, node_color='skyblue', font_size=10, font_weight='bold', arrowsize=15, edge_color=colors)
        plt.suptitle(f"Estado Inicial de las Conexiones entre AS con el origen {d['resource']} en tiempo {d['query_starttime']}")
        plt.show()



        # Verificar si hay eventos y mostrar su estructura
        if 'events' in data['data']:
            events = data['data']['events']
            
            
            for event in events:
                if 'path' in event['attrs']:  # Verificar si el evento tiene un 'path'
                    path2 = event['attrs']['path']                    
                    if path2[0] == filter_asn:  # Filtrar los caminos que comienzan con 51519
                        print("Evento coincide con el filtro:", event['attrs']['path'], "En el tiempo:", event['timestamp'])  # Verificar la estructura del evento
                        R = nx.DiGraph()
                        if 'path' in event['attrs']:
                            path = event['attrs']['path']
                            if event['type'] == 'A':  # Anuncio
                                color = 'green'
                                for i in range(len(path) - 1):
                                    R.add_edge(path[i+1], path[i], color=color)
                                    edges = R.edges(data=True)
                        pos = nx.spring_layout(R)
                        colors = [edge[2]['color'] for edge in edges]
                        plt.figure(figsize=(12, 8))
                        nx.draw(R, pos, with_labels=True, node_size=500, node_color='skyblue', font_size=10, font_weight='bold', arrowsize=15, edge_color=colors)
                        #plt.title(f"Actualización de las Conexiones entre AS - Tiempo: {event['timestamp']}")
                        plt.suptitle(f"Actualización de las Conexiones entre AS - Tiempo: {event['timestamp']}")
                        plt.show()

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP Error: {http_err}")
    except Exception as err:
        print(f"Error: {err}")
    return None

def show_graph_window(fig):
    """ Muestra la gráfica en una nueva ventana """
    if fig:
        graph_window = tk.Toplevel(root)
        graph_window.title("Gráfico BGP State")
        canvas = FigureCanvasTkAgg(fig, master=graph_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)

def consultar_bgp_state():
    """ Maneja la consulta de BGP State y muestra la gráfica """
    prefix = widgets['entry_prefix_state'].get()
    date = widgets['date_entry_state'].get()
    time = f"{widgets['spin_hour_state'].get()}:{widgets['spin_minute_state'].get()}:{widgets['spin_second_state'].get()}"

    # Formatear el timestamp
    timestamp = format_timestamp(date, time)
    
    # Construir la URL con el formato correcto
    url = f"https://stat.ripe.net/data/bgp-state/data.json?resource={prefix}&timestamp={timestamp}"
    
    print(f"URL de la solicitud: {url}")  # Para verificar que la URL es correcta

    fig = generate_graph(url)
    show_graph_window(fig)

def consultar_bgp_play():
    """ Maneja la consulta de BGP Play y muestra la gráfica """
    prefix = widgets['entry_prefix_play'].get()
    asn = widgets['entry_asn_play'].get()
    start_date = widgets['date_entry_start_play'].get()
    start_time = f"{widgets['spin_hour_start_play'].get()}:{widgets['spin_minute_start_play'].get()}:{widgets['spin_second_start_play'].get()}"
    end_date = widgets['date_entry_end_play'].get()
    end_time = f"{widgets['spin_hour_end_play'].get()}:{widgets['spin_minute_end_play'].get()}:{widgets['spin_second_end_play'].get()}"
    
    # Formatear los timestamps
    start_timestamp = format_timestamp(start_date, start_time)
    end_timestamp = format_timestamp(end_date, end_time)

    # Construir la URL con el formato correcto
    url = f"https://stat.ripe.net/data/bgplay/data.json?resource={prefix}&starttime={start_timestamp}&endtime={end_timestamp}"
    
    print(f"URL de la solicitud: {url}")  # Para verificar que la URL es correcta

    fig = generate_graph_bgp_play(url, int(asn))
    show_graph_window(fig)

# Configuración de la aplicación principal

root = tk.Tk()  # Crear la ventana principal
root.title("Consulta de Prefijo y ASN")  # Título de la ventana
root.geometry('800x600')  # Tamaño de la ventana

# Configurar estilos para los widgets
style = ttk.Style(root)
style.configure('TFrame', background=DARK_BG)
style.configure('TLabel', background=DARK_BG, foreground=TEXT_COLOR, font=('Arial', 10))
style.configure('TButton', background=ACCENT_COLOR, foreground=BUTTON_TEXT_COLOR, font=('Arial', 10), padding=5)
style.configure('TEntry', fieldbackground=LIGHT_BG, foreground=ENTRY_TEXT_COLOR, font=('Arial', 10))
style.configure('TNotebook', background=DARK_BG, borderwidth=0)
style.configure('TNotebook.Tab', background=DARK_BG, foreground=TAB_TEXT_COLOR, font=('Arial', 10), padding=[10, 5])
style.map('TNotebook.Tab', background=[('selected', ACCENT_COLOR)], foreground=[('selected', TEXT_COLOR)])

root.configure(bg=DARK_BG)  # Establecer el fondo de la ventana principal

# Crear el notebook y añadir las pestañas
notebook = ttk.Notebook(root, style='TNotebook')
notebook.pack(padx=10, pady=10, fill='both', expand=True)

# Cargar la imagen de fondo
# fondo_img = tk.PhotoImage(file="fondo.png")

# Configuración de la pestaña BGP State
frame_state_content = create_tab(notebook, "BGP State", consultar_bgp_state)
widgets['entry_prefix_state'] = create_labeled_entry(frame_state_content, "Prefijo")
ttk.Label(frame_state_content, text="Fecha").pack(pady=(5, 0))  # Añadir etiqueta de Fecha
widgets['date_entry_state'] = DateEntry(frame_state_content, background=LIGHT_BG, foreground=ENTRY_TEXT_COLOR, borderwidth=1, width=28)
widgets['date_entry_state'].pack(pady=5)
ttk.Label(frame_state_content, text="Hora").pack(pady=(5, 0))
widgets['spin_hour_state'], widgets['spin_minute_state'], widgets['spin_second_state'] = create_time_input(frame_state_content)
ttk.Button(frame_state_content, text="Consultar BGP State", command=consultar_bgp_state).pack(pady=10)

# Configuración de la pestaña BGP Play
frame_play_content = create_tab(notebook, "BGP Play", consultar_bgp_play)
widgets['entry_prefix_play'] = create_labeled_entry(frame_play_content, "Prefijo")
widgets['entry_asn_play'] = create_labeled_entry(frame_play_content, "ASN")
ttk.Label(frame_play_content, text="Fecha de inicio").pack(pady=(5, 0))  # Añadir etiqueta de Fecha de inicio
widgets['date_entry_start_play'] = DateEntry(frame_play_content, background=LIGHT_BG, foreground=ENTRY_TEXT_COLOR, borderwidth=1, width=28)
widgets['date_entry_start_play'].pack(pady=5)
ttk.Label(frame_play_content, text="Hora de Inicio").pack(pady=(5, 0))
widgets['spin_hour_start_play'], widgets['spin_minute_start_play'], widgets['spin_second_start_play'] = create_time_input(frame_play_content)
ttk.Label(frame_play_content, text="Fecha de fin").pack(pady=(5, 0))  # Añadir etiqueta de Fecha de fin
widgets['date_entry_end_play'] = DateEntry(frame_play_content, background=LIGHT_BG, foreground=ENTRY_TEXT_COLOR, borderwidth=1, width=28)
widgets['date_entry_end_play'].pack(pady=5)
ttk.Label(frame_play_content, text="Hora de Fin").pack(pady=(5, 0))
widgets['spin_hour_end_play'], widgets['spin_minute_end_play'], widgets['spin_second_end_play'] = create_time_input(frame_play_content)
ttk.Button(frame_play_content, text="Consultar BGP Play", command=consultar_bgp_play).pack(pady=10)

# Iniciar la aplicación
root.mainloop()
