
# CONTROL SERVIDOR DE TERMINALES - VERSIÓN 1.1 (CON PERSISTENCIA DE ESTADO)
# =====================================================================
import socket
import threading
import json
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
#import os

# --- CONFIGURACIÓN DE RED ---
PORT = 65432
sockets_clientes = {}  # Guarda los objetos socket indexados por id_cliente

# --- PALETA DE COLORES ---
COLOR_BG = "#1e1e1e"
COLOR_PANEL = "#252526"
COLOR_TEXT_MAIN = "#ffffff"
COLOR_TEXT_MUTED = "#858585"
COLOR_ACCENT = "#007acc"
COLOR_SUCCESS = "#16a34a"
COLOR_DANGER = "#dc2626"

class ServidorGridTerminales:
    def __init__(self, root):
        self.root = root
        self.root.title("Panel de Control de Terminales - Servidor Central Pro")
        self.root.geometry("1100x630")
        self.root.configure(bg=COLOR_BG)

        self.inicializar_db_central()

        self.sala_pcs = {}
        # Cargar el estado persistente antes de iniciar operaciones
        self.cargar_estado_terminales_db()

        self.configurar_estilos()
        self.crear_interfaz_grid()
        self.actualizar_tabla_ui()

        self.tabla_pcs.bind("<<TreeviewSelect>>", self.evento_pc_seleccionada)
        threading.Thread(target=self.arrancar_socket_server, daemon=True).start()
        self.root.after(5000, self.motor_reloj_servidor)

    def inicializar_db_central(self):
        self.conn = sqlite3.connect("sistema_central.db", check_same_thread=False)
        self.conn.execute("PRAGMA foreign_keys = ON;")
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id TEXT PRIMARY KEY,
                nombre TEXT NOT NULL,
                saldo_segundos INTEGER DEFAULT 0
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historial_sesiones (
                id_sesion INTEGER PRIMARY KEY AUTOINCREMENT,
                id_cliente TEXT NOT NULL,
                id_usuario TEXT NOT NULL,
                fecha_hora_ingreso TEXT NOT NULL,
                fecha_hora_salida TEXT,
                segundos_usados INTEGER DEFAULT 0,
                FOREIGN KEY (id_usuario) REFERENCES usuarios(id) ON DELETE CASCADE
            )
        """)
        # NUEVA TABLA: Caché de estado en tiempo real de las terminales
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS estado_terminales (
                id_cliente TEXT PRIMARY KEY,
                estado TEXT NOT NULL,
                usuario TEXT,
                nombre TEXT,
                hora_ingreso TEXT,
                segundos_restantes INTEGER DEFAULT 0,
                ultima_actualizacion TEXT
            )
        """)
        self.conn.commit()

    def persistir_estado_terminal_db(self, id_pc):
        """Guarda de forma segura el estado actual de una terminal en la base de datos."""
        info = self.sala_pcs.get(id_pc)
        if not info: return

        cursor = self.conn.cursor()
        ahora_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO estado_terminales (id_cliente, estado, usuario, nombre, hora_ingreso, segundos_restantes, ultima_actualizacion)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id_cliente) DO UPDATE SET
                estado=excluded.estado,
                usuario=excluded.usuario,
                nombre=excluded.nombre,
                hora_ingreso=excluded.hora_ingreso,
                segundos_restantes=excluded.segundos_restantes,
                ultima_actualizacion=excluded.ultima_actualizacion
        """, (id_pc, info.get("estado"), info.get("usuario"), info.get("nombre"),
              info.get("hora_ingreso"), info.get("segundos_restantes", 0), ahora_str))
        self.conn.commit()

    def cargar_estado_terminales_db(self):
        """Reconstruye el estado de la sala basándose en la caché física al iniciar."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id_cliente, estado, usuario, nombre, hora_ingreso, segundos_restantes, ultima_actualizacion FROM estado_terminales")
        filas = cursor.fetchall()

        ahora = datetime.now()
        for fila in filas:
            id_pc, estado, usuario, nombre, hora_ingreso, segundos_restantes, ultima_actualizacion = fila

            # Sincronizar pérdidas de tiempo por apagado del servidor
            if "Activo" in estado and segundos_restantes > 0 and ultima_actualizacion:
                try:
                    dt_ultima = datetime.strptime(ultima_actualizacion, "%Y-%m-%d %H:%M:%S")
                    segundos_transcurridos = int((ahora - dt_ultima).total_seconds())
                    segundos_restantes = max(0, segundos_restantes - segundos_transcurridos)
                    if segundos_restantes == 0:
                        estado = "Bloqueado 🔒"
                except ValueError:
                    pass

            mins_vivos = segundos_restantes // 60

            # 1. Evaluamos y asignamos la condición de forma limpia
            state_active = estado in ["Activo ✅", "Pausado ⏸️"]

            # 2. Usamos la variable para definir el string de tiempo
            tiempo_str = f"{mins_vivos} Minutos" if state_active else "-"

            # 3. Construimos el diccionario sin ninguna advertencia
            self.sala_pcs[id_pc] = {
                "estado": estado,
                "usuario": usuario if state_active else "-",
                "nombre": nombre if state_active else "-",
                "hora_ingreso": hora_ingreso if state_active else "-",
                "segundos_restantes": segundos_restantes,
                "tiempo": tiempo_str
            }

    def configure_sorting(self, val):
        try: return int(val)
        except ValueError: return val

    def configurar_estilos(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background=COLOR_PANEL, foreground=COLOR_TEXT_MAIN,
                        fieldbackground=COLOR_PANEL, rowheight=30, borderwidth=0, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", background="#2d2d2d", foreground=COLOR_TEXT_MAIN,
                        relief="flat", font=("Segoe UI", 10, "bold"))
        style.map("Treeview", background=[("selected", COLOR_ACCENT)])

    def crear_interfaz_grid(self):
        panel_control = tk.Frame(self.root, bg=COLOR_PANEL, width=320, bd=0)
        panel_control.pack(side="left", fill="y", padx=5, pady=5)
        panel_control.pack_propagate(False)

        tk.Label(panel_control, text="DESBLOQUEO REMOTO", font=("Segoe UI", 12, "bold"), fg=COLOR_ACCENT, bg=COLOR_PANEL).pack(pady=15, padx=15, anchor="w")

        self.permitir_offline_var = tk.BooleanVar(value=True)
        chk_offline = tk.Checkbutton(
            panel_control, text="Permitir Inicio de Sesión Offline", variable=self.permitir_offline_var,
            onvalue=True, offvalue=False, command=self.notificar_cambio_reglas_a_clientes,
            bg=COLOR_PANEL, fg=COLOR_TEXT_MAIN, selectcolor=COLOR_BG, activebackground=COLOR_PANEL,
            activeforeground=COLOR_TEXT_MAIN, font=("Segoe UI", 10, "bold"), cursor="hand2"
        )
        chk_offline.pack(padx=15, pady=5, anchor="w")

        lbl_sep = tk.Label(panel_control, text="─" * 32, fg="#3e3e42", bg=COLOR_PANEL)
        lbl_sep.pack(padx=15, pady=5, anchor="w")

        tk.Label(panel_control, text="Terminal Seleccionada:", fg=COLOR_TEXT_MUTED, bg=COLOR_PANEL).pack(padx=15, anchor="w")
        self.lbl_pc_seleccionada = tk.Label(panel_control, text="Ninguna (Seleccione en la tabla)", font=("Segoe UI", 11, "bold"), fg=COLOR_TEXT_MAIN, bg=COLOR_PANEL)
        self.lbl_pc_seleccionada.pack(padx=15, pady=2, anchor="w")

        tk.Label(panel_control, text="ID de Usuario:", fg=COLOR_TEXT_MUTED, bg=COLOR_PANEL).pack(padx=15, pady=5, anchor="w")
        frame_busqueda = tk.Frame(panel_control, bg=COLOR_PANEL)
        frame_busqueda.pack(fill="x", padx=15)

        self.entry_id = tk.Entry(frame_busqueda, bg=COLOR_BG, fg=COLOR_TEXT_MAIN, insertbackground='white', relief="solid", bd=1, font=("Segoe UI", 11))
        self.entry_id.pack(side="left", expand=True, fill="x", pady=2)
        self.entry_id.bind("<Return>", lambda e: self.buscar_usuario_por_id())

        btn_buscar = tk.Button(frame_busqueda, text="🔍", command=self.buscar_usuario_por_id, bg="#3e3e42", fg=COLOR_TEXT_MAIN, bd=0, font=("Segoe UI", 9, "bold"), width=4, cursor="hand2")
        btn_buscar.pack(side="right", padx=5, pady=2)

        tk.Label(panel_control, text="Nombre del Afiliado:", fg=COLOR_TEXT_MUTED, bg=COLOR_PANEL).pack(padx=15, pady=5, anchor="w")
        self.entry_nombre = tk.Entry(panel_control, bg=COLOR_BG, fg=COLOR_TEXT_MAIN, insertbackground='white', relief="solid", bd=1, font=("Segoe UI", 11))
        self.entry_nombre.pack(fill="x", padx=15, pady=2)

        tk.Label(panel_control, text="Tiempo a Asignar (Minutos):", fg=COLOR_TEXT_MUTED, bg=COLOR_PANEL).pack(padx=15, pady=5, anchor="w")
        self.entry_tiempo = tk.Entry(panel_control, bg=COLOR_BG, fg=COLOR_TEXT_MAIN, insertbackground='white', relief="solid", bd=1, font=("Segoe UI", 11))
        self.entry_tiempo.insert(0, "60")
        self.entry_tiempo.pack(fill="x", padx=15, pady=2)

        self.btn_activar = tk.Button(panel_control, text="🚀 Desbloquear Terminal", command=self.enviar_desbloqueo_a_cliente,
                                bg=COLOR_SUCCESS, fg=COLOR_TEXT_MAIN, bd=0, relief="flat", font=("Segoe UI", 11, "bold"), cursor="hand2")
        self.btn_activar.pack(fill="x", padx=15, pady=20)

        area_grid = tk.Frame(self.root, bg=COLOR_BG)
        area_grid.pack(side="right", expand=True, fill="both", padx=5, pady=5)

        tk.Label(area_grid, text="MONITOREO DE SALA EN TIEMPO REAL", font=("Segoe UI", 12, "bold"), fg=COLOR_TEXT_MAIN, bg=COLOR_BG).pack(pady=10, anchor="w")

        self.tabla_pcs = ttk.Treeview(area_grid, columns=("PC", "Estado", "ID", "Usuario", "HoraIngreso", "Tiempo"), show="headings")
        self.tabla_pcs.heading("PC", text="Terminal")
        self.tabla_pcs.heading("Estado", text="Estado de Pantalla")
        self.tabla_pcs.heading("ID", text="ID Usuario")
        self.tabla_pcs.heading("Usuario", text="Nombre del Usuario")
        self.tabla_pcs.heading("HoraIngreso", text="Hora de Ingreso")
        self.tabla_pcs.heading("Tiempo", text="Tiempo Restante")

        self.tabla_pcs.column("PC", width=80, anchor="center")
        self.tabla_pcs.column("Estado", width=120, anchor="center")
        self.tabla_pcs.column("ID", width=100, anchor="center")
        self.tabla_pcs.column("Usuario", width=200, anchor="w")
        self.tabla_pcs.column("HoraIngreso", width=110, anchor="center")
        self.tabla_pcs.column("Tiempo", width=120, anchor="center")

        self.tabla_pcs.pack(expand=True, fill="both")
        self.tabla_pcs.bind("<Button-3>", self.mostrar_menu_contextual)

    def mostrar_menu_contextual(self, event):
        item = self.tabla_pcs.identify_row(event.y)
        if item:
            self.tabla_pcs.selection_set(item)
            valores = self.tabla_pcs.item(item, "values")
            id_pc = valores[0]
            estado_pc = valores[1]

            menu = tk.Menu(self.root, tearoff=0, bg=COLOR_PANEL, fg=COLOR_TEXT_MAIN, activebackground=COLOR_ACCENT)

            if "Activo" in estado_pc:
                menu.add_command(label="⏸️ Pausar Terminal (Llamado Atención)", command=lambda: self.enviar_control_accion(id_pc, "pausar_terminal"))
                menu.add_command(label="🛑 Terminar Sesión (Liberar PC)", command=lambda: self.enviar_control_accion(id_pc, "bloquear_terminal"))
                menu.add_command(label="🔄 Trasladar Usuario a otra Terminal", command=lambda: self.ventana_trasladar_usuario(id_pc))
                menu.add_separator()
            elif "Pausado" in estado_pc:
                menu.add_command(label="▶️ Reanudar Sesión de Usuario", command=lambda: self.enviar_control_accion(id_pc, "reanudar_terminal"))
                menu.add_command(label="🛑 Terminar Sesión (Liberar PC)", command=lambda: self.enviar_control_accion(id_pc, "bloquear_terminal"))
                menu.add_separator()

            menu.add_command(label="💬 Enviar Mensaje de Texto", command=lambda: self.ventana_escribir_mensaje(id_pc))
            menu.post(event.x_root, event.y_root)

    def enviar_control_accion(self, id_pc, accion):
        if id_pc not in sockets_clientes:
            messagebox.showerror("Error", "La terminal no está conectada actualmente.")
            return

        paquete = {"accion": accion}
        try:
            sockets_clientes[id_pc].sendall(json.dumps(paquete).encode('utf-8'))

            if accion == "pausar_terminal":
                self.sala_pcs[id_pc]["estado"] = "Pausado ⏸️"
            elif accion == "reanudar_terminal":
                self.sala_pcs[id_pc]["estado"] = "Activo ✅"
            elif accion == "bloquear_terminal":
                self.sala_pcs[id_pc] = {"estado": "Bloqueado 🔒", "usuario": "-", "nombre": "-", "hora_ingreso": "-", "tiempo": "-", "segundos_restantes": 0}

            # Persistir cambio inmediato en DB
            self.persistir_estado_terminal_db(id_pc)
            self.actualizar_tabla_ui()
        except Exception as e:
            messagebox.showerror("Error de red", f"No se pudo enviar el comando: {e}")

    def ventana_escribir_mensaje(self, id_pc):
        v_msg = tk.Toplevel(self.root)
        v_msg.title(f"Mensaje para Terminal {id_pc}")
        v_msg.geometry("350x180")
        v_msg.configure(bg=COLOR_PANEL)
        v_msg.resizable(False, False)

        tk.Label(v_msg, text=f"Escribe el mensaje para la PC {id_pc}:", fg=COLOR_TEXT_MAIN, bg=COLOR_PANEL, font=("Segoe UI", 10, "bold")).pack(pady=10)
        txt_mensaje = tk.Entry(v_msg, bg=COLOR_BG, fg=COLOR_TEXT_MAIN, insertbackground="white", relief="solid", bd=1, font=("Segoe UI", 11), width=35)
        txt_mensaje.pack(pady=5, padx=15)
        txt_mensaje.focus()

        def despachar():
            msg_texto = txt_mensaje.get().strip()
            if not msg_texto: return
            paquete = {"accion": "mostrar_mensaje", "contenido": msg_texto}
            try:
                sockets_clientes[id_pc].sendall(json.dumps(paquete).encode('utf-8'))
                v_msg.destroy()
            except:
                messagebox.showerror("Error de Red", "No se pudo enviar el mensaje. Conexión inestable.")

        txt_mensaje.bind("<Return>", lambda e: despachar())
        tk.Button(v_msg, text="✉️ Enviar Mensaje", command=despachar, bg=COLOR_ACCENT, fg=COLOR_TEXT_MAIN, bd=0, font=("Segoe UI", 10, "bold"), cursor="hand2", padx=10, pady=5).pack(pady=15)

    def buscar_usuario_por_id(self):
        id_buscar = self.entry_id.get().strip()
        if not id_buscar: return

        cursor = self.conn.cursor()
        cursor.execute("SELECT nombre FROM usuarios WHERE id = ?", (id_buscar,))
        resultado = cursor.fetchone()

        if resultado:
            self.entry_nombre.delete(0, tk.END)
            self.entry_nombre.insert(0, resultado[0])
            self.entry_nombre.config(bg="#1a2e1a")
        else:
            self.entry_nombre.delete(0, tk.END)
            self.entry_nombre.config(bg=COLOR_BG)
            messagebox.showwarning("No Encontrado", "El ID no existe en la DB Central. Escriba el nombre para registrarlo automáticamente al activar.")

    def motor_reloj_servidor(self):
        debe_refrescar = False
        for id_pc, info in self.sala_pcs.items():
            if info["estado"] == "Activo ✅" and "segundos_restantes" in info:
                if info["segundos_restantes"] > 0:
                    info["segundos_restantes"] -= 5
                    mins_vivos = info["segundos_restantes"] // 60
                    info["tiempo"] = f"{mins_vivos} Minutos"
                    debe_refrescar = True
                else:
                    info["estado"] = "Bloqueado 🔒"
                    info["tiempo"] = "-"
                    info["segundos_restantes"] = 0
                    debe_refrescar = True

                # Volcar a DB en cada iteración del reloj para mantener la sincronía al segundo
                self.persistir_estado_terminal_db(id_pc)

        if debe_refrescar:
            self.actualizar_tabla_ui()
        self.root.after(5000, self.motor_reloj_servidor)

    def evento_pc_seleccionada(self, event):
        seleccion = self.tabla_pcs.selection()
        if seleccion:
            valores = self.tabla_pcs.item(seleccion[0], "values")
            self.lbl_pc_seleccionada.config(text=f"TERMINAL CLIENTE N° {valores[0]}", fg=COLOR_ACCENT)

    def actualizar_tabla_ui(self):
        seleccionada = self.tabla_pcs.selection()
        pc_previa = self.tabla_pcs.item(seleccionada[0], "values")[0] if seleccionada else None

        for fila in self.tabla_pcs.get_children():
            self.tabla_pcs.delete(fila)

        for id_pc in sorted(self.sala_pcs.keys(), key=self.configure_sorting):
            info = self.sala_pcs[id_pc]
            item_id = self.tabla_pcs.insert("", "end", values=(
                id_pc,
                info.get("estado", "Bloqueado 🔒"),
                info.get("usuario", "-"),
                info.get("nombre", "-"),
                info.get("hora_ingreso", "-"),
                info.get("tiempo", "-")
            ))
            if pc_previa == id_pc:
                self.tabla_pcs.selection_set(item_id)

    def notificar_cambio_reglas_a_clientes(self):
        estado_toggle = self.permitir_offline_var.get()
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, nombre FROM usuarios")
        db_map = {f[0]: f[1] for f in cursor.fetchall()}

        paquete_sync = {
            "accion": "actualizar_config",
            "permitir_offline": estado_toggle,
            "tiempo_predeterminado_minutos": 60,
            "usuarios": db_map
        }
        for id_pc, sock_conn in list(sockets_clientes.items()):
            try: sock_conn.sendall(json.dumps(paquete_sync).encode('utf-8'))
            except: pass

    def enviar_desbloqueo_a_cliente(self):
        seleccion = self.tabla_pcs.selection()
        if not seleccion:
            messagebox.showerror("Error", "Seleccione primero qué PC desea asignar en el Grid derecho.")
            return

        id_pc = self.tabla_pcs.item(seleccion[0], "values")[0]
        id_u = self.entry_id.get().strip()
        nom_u = self.entry_nombre.get().strip()
        min_u = self.entry_tiempo.get().strip()

        if not id_u or not nom_u or not min_u:
            messagebox.showerror("Campos Vacíos", "Complete el ID, Nombre y Tiempo para proceder.")
            return

        if id_pc not in sockets_clientes:
            messagebox.showerror("Equipo Offline", f"La Terminal {id_pc} no está conectada al socket del servidor.")
            return

        try:
            minutos = int(min_u)
            segundos = minutos * 60
            ahora_db = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            hora_pantalla = datetime.now().strftime("%I:%M:%S %p")

            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO usuarios (id, nombre, saldo_segundos) VALUES (?, ?, 0)
                ON CONFLICT(id) DO UPDATE SET nombre=excluded.nombre
            """, (id_u, nom_u))

            cursor.execute("""
                INSERT INTO historial_sesiones (id_cliente, id_usuario, fecha_hora_ingreso)
                VALUES (?, ?, ?)
            """, (id_pc, id_u, ahora_db))
            self.conn.commit()

            self.sala_pcs[id_pc] = {
                "estado": "Activo ✅", "usuario": id_u, "nombre": nom_u,
                "hora_ingreso": hora_pantalla, "segundos_restantes": segundos,
                "tiempo": f"{minutos} Minutos"
            }

            # Guardar el estado inicial en la caché DB
            self.persistir_estado_terminal_db(id_pc)

            paquete = {
                "accion": "desbloqueo_remoto",
                "tiempo_segundos": segundos,
                "usuario_id": id_u,
                "nombre": nom_u
            }
            sockets_clientes[id_pc].sendall(json.dumps(paquete).encode('utf-8'))

            self.entry_id.delete(0, tk.END)
            self.entry_nombre.delete(0, tk.END)
            self.entry_nombre.config(bg=COLOR_BG)
            self.actualizar_tabla_ui()

        except ValueError:
            messagebox.showerror("Error", "La caja de tiempo debe ser un valor entero.")

    def ventana_trasladar_usuario(self, id_pc_origen):
      v_traslado = tk.Toplevel(self.root)
      v_traslado.title("Trasladar Sesión")
      v_traslado.geometry("300x150")
      v_traslado.configure(bg=COLOR_PANEL)

      tk.Label(v_traslado, text=f"Cambiar usuario de PC N° {id_pc_origen} a:", fg=COLOR_TEXT_MAIN, bg=COLOR_PANEL, font=("Segoe UI", 10, "bold")).pack(pady=10)
      entry_destino = tk.Entry(v_traslado, bg=COLOR_BG, fg=COLOR_TEXT_MAIN, insertbackground="white", relief="solid", bd=1, font=("Segoe UI", 11), width=15, justify="center")
      entry_destino.pack(pady=5)

      def ejecutar_traslado():
          id_pc_destino = entry_destino.get().strip()
          if not id_pc_destino or id_pc_destino == id_pc_origen: return

          if id_pc_destino not in sockets_clientes:
              messagebox.showerror("Error", f"La Terminal Destino {id_pc_destino} no está en red.")
              return

          if self.sala_pcs.get(id_pc_destino, {}).get("estado") != "Bloqueado 🔒":
              messagebox.showerror("Error", "La terminal de destino no está libre.")
              return

          info_origen = self.sala_pcs[id_pc_origen]
          segundos_restantes = info_origen.get("segundos_restantes", 3600)

          self.enviar_control_accion(id_pc_origen, "bloquear_terminal")

          paquete_destino = {
              "accion": "desbloqueo_remoto",
              "tiempo_segundos": segundos_restantes,
              "usuario_id": info_origen["usuario"],
              "nombre": info_origen["nombre"]
          }

          try:
              sockets_clientes[id_pc_destino].sendall(json.dumps(paquete_destino).encode('utf-8'))

              self.sala_pcs[id_pc_destino] = {
                  "estado": "Activo ✅", "usuario": info_origen["usuario"],
                  "nombre": info_origen["nombre"], "hora_ingreso": info_origen["hora_ingreso"],
                  "segundos_restantes": segundos_restantes, "tiempo": f"{segundos_restantes // 60} Minutos"
              }
              # Forzar persistencia del destino
              self.persistir_estado_terminal_db(id_pc_destino)
              self.actualizar_tabla_ui()
              v_traslado.destroy()
          except Exception as e:
              messagebox.showerror("Error", f"Fallo al transferir datos por socket: {e}")

      tk.Button(v_traslado, text="Confirmar Cambio", command=ejecutar_traslado, bg=COLOR_ACCENT, fg=COLOR_TEXT_MAIN, bd=0, font=("Segoe UI", 10, "bold"), cursor="hand2").pack(pady=10)

    # =========================================================================
    # ESCUCHA DE RED (SOCKETS)
    # =========================================================================
    def arrancar_socket_server(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(('0.0.0.0', PORT))
        server.listen()

        while True:
            conn, addr = server.accept()
            threading.Thread(target=self.bucle_comunicacion_cliente, args=(conn,), daemon=True).start()

    def bucle_comunicacion_cliente(self, conn):
        id_pc = None
        try:
            while True:
                data = conn.recv(4096).decode('utf-8')
                if not data: break
                msg = json.loads(data)
                accion = msg.get("accion")

                if accion == "registrarse":
                    id_pc = str(msg.get("id_cliente"))
                    sockets_clientes[id_pc] = conn

                    # 1. Enviar siempre la configuración básica obligatoria primero
                    cursor = self.conn.cursor()
                    cursor.execute("SELECT id, nombre FROM usuarios")
                    db_map = {f[0]: f[1] for f in cursor.fetchall()}
                    paquete_sync = {
                        "accion": "actualizar_config",
                        "permitir_offline": self.permitir_offline_var.get(),
                        "tiempo_predeterminado_minutos": 60,
                        "usuarios": db_map
                    }
                    conn.sendall(json.dumps(paquete_sync).encode('utf-8'))

                    # 2. EVALUAR CACHÉ: ¿La PC tenía una sesión viva antes del reinicio/caída?
                    cursor.execute("SELECT estado, usuario, nombre, hora_ingreso, segundos_restantes, ultima_actualizacion FROM estado_terminales WHERE id_cliente = ?", (id_pc,))
                    fila = cursor.fetchone()

                    sesion_recuperada = False
                    if fila:
                        estado, usuario, nombre, hora_ingreso, segundos_restantes, ultima_actualizacion = fila
                        if estado in ["Activo ✅", "Pausado ⏸️"]:

                            # Descontar el tiempo exacto que duró la desconexión del socket
                            if estado == "Activo ✅" and ultima_actualizacion:
                                try:
                                    dt_ultima = datetime.strptime(ultima_actualizacion, "%Y-%m-%d %H:%M:%S")
                                    delta_desconexion = int((datetime.now() - dt_ultima).total_seconds())
                                    segundos_restantes = max(0, segundos_restantes - delta_desconexion)
                                    if segundos_restantes == 0:
                                        estado = "Bloqueado 🔒"
                                except ValueError: pass

                            if segundos_restantes > 0:
                                self.sala_pcs[id_pc] = {
                                    "estado": estado, "usuario": usuario, "nombre": nombre,
                                    "hora_ingreso": hora_ingreso, "segundos_restantes": segundos_restantes,
                                    "tiempo": f"{segundos_restantes // 60} Minutos"
                                }
                                sesion_recuperada = True

                                # ENVIAR SINCRONIZACIÓN FORZADA AL CLIENTE RECONECTADO
                                paquete_recuperacion = {
                                    "accion": "desbloqueo_remoto",
                                    "tiempo_segundos": segundos_restantes,
                                    "usuario_id": usuario,
                                    "nombre": nombre
                                }
                                try: conn.sendall(json.dumps(paquete_recuperacion).encode('utf-8'))
                                except: pass

                                self.persistir_estado_terminal_db(id_pc)

                    if not sesion_recuperada:
                        # Si no hay nada que recuperar, se comporta como antes (inicializa bloqueado)
                        self.sala_pcs[id_pc] = {"estado": "Bloqueado 🔒", "usuario": "-", "nombre": "-", "hora_ingreso": "-", "tiempo": "-", "segundos_restantes": 0}
                        self.persistir_estado_terminal_db(id_pc)

                    self.root.after(0, self.actualizar_tabla_ui)

                elif accion == "sincronizar_offline":
                    u_id = msg.get("usuario")
                    segundos_restantes = msg.get("tiempo_restante", 3600)
                    minutos_restantes = segundos_restantes // 60

                    cursor = self.conn.cursor()
                    cursor.execute("SELECT nombre FROM usuarios WHERE id = ?", (u_id,))
                    res_usuario = cursor.fetchone()
                    nombre_usuario = res_usuario[0] if res_usuario else msg.get("nombre", "Usuario Offline Temporal")

                    cursor.execute("""
                        INSERT INTO usuarios (id, nombre, saldo_segundos) VALUES (?, ?, 0)
                        ON CONFLICT(id) DO UPDATE SET nombre=excluded.nombre
                    """, (u_id, nombre_usuario))

                    ahora_db = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    hora_pantalla = datetime.now().strftime("%I:%M:%S %p")
                    cursor.execute("""
                        INSERT INTO historial_sesiones (id_cliente, id_usuario, fecha_hora_ingreso)
                        VALUES (?, ?, ?)
                    """, (id_pc, u_id, f"Offline ({hora_pantalla})"))
                    self.conn.commit()

                    self.sala_pcs[id_pc] = {
                        "estado": "Activo ✅", "usuario": u_id, "nombre": nombre_usuario,
                        "hora_ingreso": f"Offline ({hora_pantalla})",
                        "segundos_restantes": segundos_restantes, "tiempo": f"{minutos_restantes} Minutos"
                    }
                    self.persistir_estado_terminal_db(id_pc)
                    self.root.after(0, self.actualizar_tabla_ui)

                elif accion == "tiempo_agotado_cliente":
                    self.sala_pcs[id_pc] = {"estado": "Bloqueado 🔒", "usuario": "-", "nombre": "-", "hora_ingreso": "-", "tiempo": "-", "segundos_restantes": 0}
                    self.persistir_estado_terminal_db(id_pc)
                    self.root.after(0, self.actualizar_tabla_ui)

        except: pass
        finally:
            if id_pc in sockets_clientes: del sockets_clientes[id_pc]
            if id_pc in self.sala_pcs:
                # OJO: Cambiamos el estado visual a Desconectado en RAM, pero NO borramos el estado
                # de la Base de datos. Así, cuando regrese la red, se recupera el tiempo remanente.
                self.sala_pcs[id_pc] = {"estado": "Desconectado", "usuario": "-", "nombre": "-", "hora_ingreso": "-", "tiempo": "-"}
            self.root.after(0, self.actualizar_tabla_ui)
            conn.close()

if __name__ == "__main__":
    root = tk.Tk()
    app = ServidorGridTerminales(root)
    root.mainloop()