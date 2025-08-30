import tkinter as tk 
from tkinter import ttk
from PIL import Image, ImageTk
from tinydb import TinyDB
from unidecode import unidecode as ud
import pygame
from PIL import ImageOps 

class ReproductorXav:
    def mostrar_letras(self, cancion):
        ventana_letra = tk.Toplevel(self.root)
        ventana_letra.geometry("300x500")
        ventana_letra.title(f"{cancion.get('nombre')} letra.")
        ventana_letra.configure(bg="black")

        marco_texto = tk.Frame(ventana_letra, bg="black")
        marco_texto.pack(fill="both", expand=True)

        scroll = tk.Scrollbar(marco_texto)
        scroll.pack(side='right', fill='y')

        # Widget de texto
        texto = tk.Text(marco_texto, wrap="word", yscrollcommand=scroll.set, font=("Arial", 12),bg="black", fg="white", insertbackground="white")
        texto.pack(side="top", fill="both", expand=True, padx=15, pady=10)
        scroll.config(command=texto.yview)

        # Insertar letra
        letra = cancion.get('letra', 'Letra no disponible.')
        texto.insert("1.0", letra)
        texto.config(state="disabled")

    def play(self, index=None):
        if index is not None:
            self.cancion_actual = index 
    
        if not self.canciones:
            return
        cancion = self.canciones[self.cancion_actual]
        ruta_audio = cancion.get("ubicacion", "")
        try:
            if self.esta_pausado:
            # Si está pausado, reanudar sin reiniciar
                pygame.mixer.music.unpause()
                self.esta_pausado = False
            else:
            # Si no está pausado, cargar y reproducir desde el inicio
                pygame.mixer.music.stop()
                pygame.mixer.music.load(ruta_audio)
                pygame.mixer.music.play()
                try:
                    from mutagen.mp3 import MP3
                    audio = MP3(ruta_audio)
                    self.duracion_total = audio.info.length
                    self.barra_progreso.config(to=self.duracion_total)
                except:
                    self.duracion_total = 300  # Valor por defecto (5 mins)
                self.esta_reproduciendo = True
                self.actualizar_interfaz()
                self.actualizar_barra()
        except Exception as e:
            print("Error al reproducir:", e)

    def pause(self):
        if self.esta_reproduciendo:
            pygame.mixer.music.pause()
            self.esta_reproduciendo = False
        else:
            pygame.mixer.music.unpause()
            self.esta_reproduciendo = True

    def stop(self):
        pygame.mixer.music.stop()
        self.esta_reproduciendo = False
        self.esta_pausado = False

    def next_song(self):
        if not self.canciones:
            return
        self.cancion_actual = (self.cancion_actual + 1) % len(self.canciones)
        self.stop()
        self.play()
        self.actualizar_interfaz()

    def prev_song(self):
        if not self.canciones:
            return
        self.cancion_actual = (self.cancion_actual - 1) % len(self.canciones)
        self.stop()
        self.play()
        self.actualizar_interfaz()
        
    def actualizar_interfaz(self):
        if not self.canciones:
            return
    
        cancion = self.canciones[self.cancion_actual]
        self.etiqueta_cancion.config(text=cancion.get("nombre", ""))
        self.etiqueta_autor.config(text=cancion.get("autor", ""))
        self.etiqueta_album.config(text=cancion.get("album", ""))
        self.etiqueta_anio.config(text=cancion.get("fecha_de_lanzamiento", ""))
    
        try:
            imagen = Image.open(cancion["portada"]).resize((200, 200))
            self.imagen_portada = ImageTk.PhotoImage(imagen)
            self.etiqueta_portada.config(image=self.imagen_portada)
        except Exception as e:
            print("Error cargando portada:", e)

    #ACTUALIZAR LA BARRA DE PROGRESO
    def actualizar_barra(self):
        if self.esta_reproduciendo and not self.esta_pausado:
            self.tiempo_actual = pygame.mixer.music.get_pos() / 1000 
            self.barra_progreso.set(self.tiempo_actual)
            tiempo_formateado = self.formatear_tiempo(self.tiempo_actual)
            duracion_formateada = self.formatear_tiempo(self.duracion_total)
            self.etiqueta_tiempo.config(text=f"{tiempo_formateado}/{duracion_formateada}")  
        self.root.after(1000, self.actualizar_barra)

    def formatear_tiempo(self, segundos):
        minutos = int(segundos//60)
        segundos = int(segundos%60)
        return f"{minutos:02d}:{segundos:02d}"
    
    def seguir_reproduciendo(self):
        if self.esta_reproduciendo and not pygame.mixer.music.get_busy():
            self.next_song()
        self.root.after(1000, self.seguir_reproduciendo)

    def on_seek(self, valor):
        if self.esta_reproduciendo:
            if abs(float(valor) - self.tiempo_actual) > 2:
                pygame.mixer.music.set_pos(float(valor))
                self.tiempo_actual = float(valor)

    def clickEnCancion(self, event):
        item_id = self.tree.focus()
        if not item_id:
            return
        item_values = self.tree.item(item_id, "values")
        for i, cancion in enumerate(self.canciones):
            if (cancion.get("nombre"), cancion.get("autor"), cancion.get("album")) == item_values:
                self.cancion_actual = i
                self.play()
                break

    def mostrar_canciones(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview",
                background="black",
                foreground="white",
                fieldbackground="black",
                font=("Arial", 11))
        style.map("Treeview", background=[('selected', '#333333')])  # Color al seleccionar
        ventana_lista = tk.Toplevel(self.root)
        ventana_lista.title("Mi Música")
        ventana_lista.geometry("450x500")
        ventana_lista.resizable(False, False)
        ventana_lista.configure(bg="black")

        columnas = ("nombre", "autor", "album")
        tree = ttk.Treeview(ventana_lista, columns=columnas, show="headings", selectmode="browse")
        tree.pack(fill="both", expand=True)
        tree.tag_configure("odd", background="black", foreground="white")
        tree.tag_configure("even", background="black", foreground="white")
        self.tree = tree
        self.tree.bind("<Double-1>", self.clickEnCancion)

        panel_busqueda = tk.Frame(ventana_lista, bg="black")
        panel_busqueda.pack(fill="x")
        caja_busqueda = tk.Entry(panel_busqueda, width=30, bg="black", fg="white", font=("Arial", 12), insertbackground="white")
        caja_busqueda.pack(side='left', padx=50, pady=10)
        boton_busqueda = tk.Button(panel_busqueda, text='🔍')
        boton_busqueda.pack(side="left")

        estado_orden = {"nombre": "asc", "autor": "asc", "album": "asc"}
    
    # Función para cargar canciones
        def cargar_canciones(lista):
            for item in tree.get_children():
                tree.delete(item)  # Limpiar el Treeview antes de insertar nuevos elementos
            for cancion in lista:
                tree.insert("", "end", values=(cancion.get("nombre", ""), cancion.get("autor", ""), cancion.get("album", "")))

    # Llamar a cargar_canciones al inicio sin ordenar
        cargar_canciones(self.canciones)
    
    # Función para el ordenamiento
        def ordenamientoSeleccion(campo, ord='asc'):
            n = len(self.canciones)
            for pi in range(n-1):
                min = pi
                for pj in range(pi+1, n):
                    if ord == 'desc':
                        if self.canciones[pj][campo] > self.canciones[min][campo]:
                            min = pj
                    else:
                        if self.canciones[pj][campo] < self.canciones[min][campo]:
                            min = pj
            # Mover el intercambio fuera del ciclo interno
                self.canciones[pi], self.canciones[min] = self.canciones[min], self.canciones[pi]
            cargar_canciones(self.canciones)  # Recargar la lista de canciones ordenadas

    # Función de búsqueda
        def buscar():
            termino = caja_busqueda.get().strip().lower()  # Corregir uso de 'ud'
            resultados = []
            for cancion in self.canciones:
                for campo in cancion.values():
                    if termino in str(campo).strip().lower():
                        resultados.append(cancion)
                        break
            cargar_canciones(resultados)

    # Funciones para ordenar por columna
        def ordenarPorNombre():
            campo = "nombre"
            orden = estado_orden[campo]
            ordenamientoSeleccion(campo, orden)
            tree.heading(campo, text=f"Nombre {'↓' if orden == 'asc' else '↑'}")
            estado_orden[campo] = "desc" if orden == "asc" else "asc"

        def ordenarPorAutor():
            campo = "autor"
            orden = estado_orden[campo]
            ordenamientoSeleccion(campo, orden)
            tree.heading(campo, text=f"Autor {'↓' if orden == 'asc' else '↑'}")
            estado_orden[campo] = "desc" if orden == "asc" else "asc"

        def ordenarPorAlbum():
            campo = "album"
            orden = estado_orden[campo]
            ordenamientoSeleccion(campo, orden)
            tree.heading(campo, text=f"Album {'↓' if orden == 'asc' else '↑'}")
            estado_orden[campo] = "desc" if orden == "asc" else "asc"

        boton_busqueda.config(command=buscar)
        tree.heading("nombre", text="Nombre", command=ordenarPorNombre)
        tree.heading("autor", text="Autor", command=ordenarPorAutor)
        tree.heading("album", text="Album", command=ordenarPorAlbum)
        tree.column("nombre", width=150)
        tree.column("autor", width=125)
        tree.column("album", width=125)

    # Función para mostrar información de la canción seleccionada
        def mostrarCancion(cancion):
            self.etiqueta_cancion.config(text=cancion.get("nombre", ""))
            self.etiqueta_autor.config(text=cancion.get("autor", ""))
            self.etiqueta_album.config(text=cancion.get("album", ""))
            self.etiqueta_anio.config(text=cancion.get("fecha_de_lanzamiento", ""))
            try:
                imagen = Image.open(cancion["portada"])
                imagen = imagen.resize((200, 200))
                self.imagen_portada = ImageTk.PhotoImage(imagen)
                self.etiqueta_portada.config(image=self.imagen_portada)
            except Exception as e:
                print("Error cargando imagen:", e)


    def __init__(self):
        self.db = TinyDB("G:/Mi unidad/UACM/5to Semestre/Analisis de Algoritmos/Reproductor de Musica con Tkinter/Musica2.json")
        self.tb_canciones = self.db.table("Musica")
        self.canciones = self.tb_canciones.all()
        self.root = tk.Tk()
        self.root.title("Spoty Xavat") 
        self.root.resizable(width=False, height=False)
        
        self.icono_previous = ImageTk.PhotoImage(Image.open("G:/Mi unidad/UACM/5to Semestre/Analisis de Algoritmos/Reproductor de Musica con Tkinter/Imagenes/icono_previous.png").resize((30, 30)))
        self.icono_play = ImageTk.PhotoImage(Image.open("G:/Mi unidad/UACM/5to Semestre/Analisis de Algoritmos/Reproductor de Musica con Tkinter/Imagenes/icono_play.png").resize((30, 30)))
        self.icono_pause = ImageTk.PhotoImage(Image.open("G:/Mi unidad/UACM/5to Semestre/Analisis de Algoritmos/Reproductor de Musica con Tkinter/Imagenes/icono_pause.png").resize((30, 30)))
        self.icono_stop = ImageTk.PhotoImage(Image.open("G:/Mi unidad/UACM/5to Semestre/Analisis de Algoritmos/Reproductor de Musica con Tkinter/Imagenes/icono_stop.png").resize((30, 30)))
        self.icono_next = ImageTk.PhotoImage(Image.open("G:/Mi unidad/UACM/5to Semestre/Analisis de Algoritmos/Reproductor de Musica con Tkinter/Imagenes/icono_next.png").resize((30, 30)))
        self.menu = ImageTk.PhotoImage(Image.open("G:/Mi unidad/UACM/5to Semestre/Analisis de Algoritmos/Reproductor de Musica con Tkinter/Imagenes/menu.png").resize((20, 20)))
    
        self.panel_portada = tk.Frame(self.root, bg="black", height=200, width=300)
        self.panel_portada.pack_propagate(False)
        self.panel_informacion_cancion = tk.Frame(self.root, bg="black", height=150, width=300)
        self.panel_informacion_cancion.pack_propagate(False)
        self.panel_botones = tk.Frame(self.root, bg="black", height=150, width=300)
        self.panel_botones.pack_propagate(False)

        self.portada = Image.open("C:/Users/gonzz/Downloads/JIM.jpg").resize((200, 200))
        self.portada = ImageTk.PhotoImage(self.portada)
        self.etiqueta_portada = tk.Label(self.panel_portada, image=self.portada)

        self.etiqueta_portada.pack(side='top', pady=20)
        self.etiqueta_cancion = tk.Label(self.panel_informacion_cancion,text="Nombre de la canción", bg="black", fg="white", font=("Arial", 12))
        self.etiqueta_cancion.pack(side='top',pady=5)
        self.etiqueta_autor = tk.Label(self.panel_informacion_cancion,text="Autor", bg="black", fg="#FFFFFF", font=("Arial", 12))
        self.etiqueta_autor.pack(side='top',pady=1)
        self.etiqueta_album = tk.Label(self.panel_informacion_cancion,text="Album", bg="black", fg="white", font=("Arial", 12))
        self.etiqueta_album.pack(side='top',pady=1)
        self.etiqueta_anio = tk.Label(self.panel_informacion_cancion,text="Año", bg="black", fg="white", font=("Arial", 12))
        self.etiqueta_anio.pack(side='top',pady=1)
        self.boton_letras = tk.Button(self.panel_informacion_cancion, text="Letras", bg="black", fg="white", font=("Arial", 12), command=lambda: self.mostrar_letras(self.canciones[self.cancion_actual]))
        self.boton_letras.pack(side="bottom")

        self.lista_canciones = tk.Frame(self.panel_botones, bg="black")
        self.lista_canciones.pack(fill="x", pady=(0, 5))
        marco_barra = tk.Frame(self.lista_canciones, bg="white", padx=1, pady=1)
        marco_barra.pack(pady=5, side="left", padx=15)
        self.boton_canciones = tk.Button(self.lista_canciones, image=self.menu, command=self.mostrar_canciones)
        self.boton_canciones.pack(side='left', padx=15)

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Custom.Horizontal.TScale",troughcolor="black",background="white",thickness=0.5)
        self.barra_progreso = ttk.Scale(marco_barra, from_=0, to=100, orient='horizontal', length=200, style="Custom.Horizontal.TScale")
        self.barra_progreso.pack()
        self.barra_progreso.config(command=self.on_seek)
        self.etiqueta_tiempo = tk.Label(self.panel_botones, text="00:00/00:00", bg="black", fg="white")
        self.etiqueta_tiempo.pack()

        self.panel_de_botones = tk.Frame(self.panel_botones, bg="black")
        self.boton_anterior = tk.Button(self.panel_de_botones, image=self.icono_previous, borderwidth=0, bg="white", command=self.prev_song)
        self.boton_anterior.pack(side='left')
        self.boton_reproducir = tk.Button(self.panel_de_botones, image=self.icono_play, borderwidth=0, bg="white", command=self.play)
        self.boton_reproducir.pack(side='left', padx=15)
        self.boton_pausa = tk.Button(self.panel_de_botones, image=self.icono_pause, borderwidth=0, bg="white", command=self.pause)
        self.boton_pausa.pack(side='left', padx=15)
        self.boton_stop = tk.Button(self.panel_de_botones, image=self.icono_stop, borderwidth=0, bg="white", command=self.stop)
        self.boton_stop.pack(side='left', padx=15)
        self.boton_siguiente = tk.Button(self.panel_de_botones, image=self.icono_next, borderwidth=0, bg="white", command=self.next_song)
        self.boton_siguiente.pack(side='left')

        self.panel_portada.pack(side='top')
        self.panel_informacion_cancion.pack()
        self.panel_botones.pack()
        self.panel_de_botones.pack(side="top", pady=15)

        if self.canciones:
            self.etiqueta_cancion.config(text=self.canciones[0].get("nombre", ""))
            self.etiqueta_autor.config(text=self.canciones[0].get("autor", ""))
            self.etiqueta_album.config(text=self.canciones[0].get("album", ""))
            self.etiqueta_anio.config(text=self.canciones[0].get("fecha_de_lanzamiento", ""))
            try:
                imagen = Image.open(self.canciones[0]["portada"]).resize((200, 200))
                self.imagen_portada = ImageTk.PhotoImage(imagen)
                self.etiqueta_portada.config(image=self.imagen_portada)
            except Exception as e:
                print("Error cargando imagen por default:", e)
            pygame.mixer.init() 
            self.root.after(1000, self.seguir_reproduciendo)
            self.esta_reproduciendo = False  
            self.esta_pausado = False       
            self.tiempo_actual = 0          
            self.duracion_total = 0         
            self.cancion_actual = 0
            #self.checar_si_termino()
        self.root.mainloop()

ReproductorXav = ReproductorXav()
