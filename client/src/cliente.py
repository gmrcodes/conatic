# CODIGO CLIENTE V 0.4.9 - CON PERSISTENCIA
# =================================
import socket
import threading
import json
import time
import os
import tkinter as tk
from tkinter import messagebox
import sqlite3
import sys
from PIL import Image, ImageTk
import psutil
import subprocess
import ctypes
from ctypes import wintypes

# 🛡️ Evitar múltiples instancias del Cliente (Se mantiene intacto por tu instrucción)
ERROR_ALREADY_EXISTS = 183
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
CreateMutex = kernel32.CreateMutexW
CreateMutex.argtypes = [wintypes.LPCVOID, wintypes.BOOL, wintypes.LPCWSTR]
CreateMutex.restype = wintypes.HANDLE

# Este nombre DEBE coincidir con el de AppMutex de Inno Setup
MUTEX_CLIENTE = "ControlClienteMutexSecret"

mutex_handle_cliente = CreateMutex(None, False, MUTEX_CLIENTE)
if kernel32.GetLastError() == ERROR_ALREADY_EXISTS:
    sys.exit(0)

# CONFIGURACIÓN DEL CLIENTE

def resource_path(relative_path):
    """
    Devuelve la ruta correcta de resources tanto al ejecutar el .py
    como al ejecutar el .exe creado con PyInstaller.
    """
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        if getattr(sys, "frozen", False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, relative_path)

def ruta_carpeta_appdata():
    """Devuelve la ruta de la carpeta de datos de la aplicación en %LOCALAPPDATA%."""
    app_data = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
    carpeta_app = os.path.join(app_data, 'ControlClienteApp')
    os.makedirs(carpeta_app, exist_ok=True)
    return carpeta_app

def obtener_ruta_config():
    """Devuelve la ruta completa al archivo de configuración JSON del cliente."""
    return os.path.join(ruta_carpeta_appdata(), 'config_cliente.json')

ARCH_CONFIG = obtener_ruta_config()

def cargar_configuracion_completa():
    # Valores default si el archivo JSON aún no se ha creado
    config_defecto = {
        "id_cliente": "1",
        "server_ip": "127.0.0.1",
        "permitir_offline": True,
        "tiempo_predeterminado_minutos": 60
    }    

    if os.path.exists(ARCH_CONFIG):
        try:
            with open(ARCH_CONFIG, "r", encoding="utf-8") as f:
                return {**config_defecto, **json.load(f)}
        except Exception as e:
            print(f"Error al leer la configuración: {e}")
            return config_defecto
    else:
        try:
            with open(ARCH_CONFIG, "w", encoding="utf-8") as f:
                json.dump(config_defecto, f, indent=4)
        except Exception as e:
            print(f"Error al crear el archivo de configuración: {e}")

    return config_defecto

def obtener_ruta_db():
    """Ruta completa a la base de datos de caché local."""
    return os.path.join(ruta_carpeta_appdata(), 'cache_cliente.db')

# CARGAR CONFIGURACIÓN DEL SISTEMA
CONFIG_SISTEMA = cargar_configuracion_completa()

# Lock para proteger la base de datos local en caso de accesos concurrentes desde hilos
db_lock = threading.Lock()

ID_CLIENTE = CONFIG_SISTEMA["id_cliente"]
SERVER_IP = CONFIG_SISTEMA["server_ip"]
PORT = 65432

# COLORES DE LA INTERFAZ PANTALLA DE BLOQUEO
COLOR_LOCK_BG = "#0c0c0d"
COLOR_TEXT = "#ffffff"
COLOR_ACCENT = "#007acc"
COLOR_DANGER = "#dc2626"

class ClienteTerminal:
    def __init__(self, root):
        self.root.bind("<Control-Shift-Q>", lambda e: self.root.destroy()) # Atajo de emergencia para cerrar la app
        self.root = root
        self.root.title(f"Terminal Cliente N° {ID_CLIENTE}")

        # Variables de estado
        self.bloqueado = True
        self.sesion_offline = False
        self.usuario_actual = "-"
        self.nombre_actual = "-"
        self.tiempo_segundos = 0
        self.red_disponible = False
        self.socket_activo = None

        self.config = CONFIG_SISTEMA

        self.inicializar_db_local()
        self.recuperar_estado_local()

        # Blindaje de interfaz inicial deshabilita Alt + F4
        self.root.protocol("WM_DELETE_WINDOW", lambda: None)
        self.root.configure(bg=COLOR_LOCK_BG)

        self.crear_componentes_ui()
        self.configurar_pantalla_segun_estado()

        # Hilos de soporte en segundo plano
        threading.Thread(target=self.bucle_conexion_red, daemon=True).start()
        threading.Thread(target=self.motor_cronometro, daemon=True).start()

    def inicializar_db_local(self):
        ruta_db = obtener_ruta_db()
        self.conn_local = sqlite3.connect(ruta_db, check_same_thread=False)
        self.conn_local.execute("""
            CREATE TABLE IF NOT EXISTS usuarios_locales (
                id TEXT PRIMARY KEY,
                nombre TEXT DEFAULT 'Usuario Local'
            )
        """)

        # TABLA Guarda la sesión activa y el tiempo restante segundo a segundo
        self.conn_local.execute("""
            CREATE TABLE IF NOT EXISTS estado_sesion (
                clave TEXT PRIMARY KEY,
                usuario TEXT,
                nombre TEXT,
                tiempo_segundos INTEGER,
                sesion_offline INTEGER,
                bloqueado INTEGER
            )
        """)
        self.conn_local.commit()

    def guardar_estado_local(self):
        """Escribe el estado crítico de la app en la base de datos local."""
        try:
            with db_lock:
                cursor = self.conn_local.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO estado_sesion (clave, usuario, nombre, tiempo_segundos, sesion_offline, bloqueado)
                    VALUES ('actual', ?, ?, ?, ?, ?)
                """, (self.usuario_actual, self.nombre_actual, self.tiempo_segundos, int(self.sesion_offline), int(self.bloqueado)))
                self.conn_local.commit()
        except Exception as e:
            print(f"Error al escribir en la base local: {e}")

    def recuperar_estado_local(self):
        """Busca si el programa viene de un cierre forzado para restaurar el tiempo."""
        try:
            cursor = self.conn_local.cursor()
            cursor.execute("SELECT usuario, nombre, tiempo_segundos, sesion_offline, bloqueado FROM estado_sesion WHERE clave = 'actual'")
            res = cursor.fetchone()
            if res:
                usuario, nombre, tiempo_segundos, sesion_offline, bloqueado = res
                # Si la terminal estaba desbloqueada y le quedaba tiempo, la revive intacta
                if bloqueado == 0 and tiempo_segundos > 0:
                    self.usuario_actual = usuario
                    self.nombre_actual = nombre
                    self.tiempo_segundos = tiempo_segundos
                    self.sesion_offline = bool(sesion_offline)
                    self.bloqueado = False
                    print(f"Antisabotaje: Sesión restaurada con éxito. Restan {self.tiempo_segundos} segundos.")
            else:
                self.guardar_estado_local()
        except Exception as e:
            print(f"Error al leer de la base local: {e}")

    def reemplazar_usuarios_locales(self, diccionario_usuarios):
        """Sincroniza la caché local con los usuarios válidos del servidor."""
        try:
            with db_lock:
                cursor = self.conn_local.cursor()
                cursor.execute("DELETE FROM usuarios_locales")
                for u_id, nombre in diccionario_usuarios.items():
                    cursor.execute("INSERT OR REPLACE INTO usuarios_locales (id, nombre) VALUES (?, ?)", (u_id, nombre))
                self.conn_local.commit()
        except Exception as e:
            print(f"Error al sincronizar usuarios locales: {e}")

    # AUXILIAR DE ENVÍO JSON COMPATIBLE CON EL SERVIDOR
    def enviar_json(self, paquete):
        if not self.socket_activo or not self.red_disponible:
            return False
        try:
            payload = (json.dumps(paquete) + "\n").encode('utf-8')
            self.socket_activo.sendall(payload)
            return True
        except Exception as e:
            print(f"[!] Error al enviar JSON desde el cliente: {e}")
            return False

    def crear_componentes_ui(self):
        # Contenedor principal de la Pantalla de Bloqueo
        self.frame_bloqueo = tk.Frame(self.root, bg=COLOR_LOCK_BG)

        # LOGO
        ruta_logo = resource_path("logo.png")
        if os.path.exists(ruta_logo):
            try:
                img_original = Image.open(ruta_logo)
                ancho_orig, alto_orig = img_original.size
                nuevo_ancho = self.root.winfo_screenwidth() // 3
                nuevo_alto = int((nuevo_ancho / ancho_orig) * alto_orig)
                img_redimensionada = img_original.resize((nuevo_ancho, nuevo_alto), Image.Resampling.LANCZOS)
                self.logo_tk = ImageTk.PhotoImage(img_redimensionada)
                lbl_logo = tk.Label(self.frame_bloqueo, image=self.logo_tk, bg=COLOR_LOCK_BG)
                lbl_logo.pack(side="top", pady=(40, 10))
            except Exception as e:
                print(f"No se pudo desplegar el logo: {e}")

        # TÍTULO
        self.lbl_titulo = tk.Label(self.frame_bloqueo, text=f"COMPUTADOR DE USO RESTRINGIDO\nTERMINAL N° {ID_CLIENTE}",
                                   font=("Segoe UI", 18, "bold"), fg=COLOR_TEXT, bg=COLOR_LOCK_BG)
        self.lbl_titulo.pack(pady=30)

        # ALERTA DE RED
        self.lbl_alerta_red = tk.Label(self.frame_bloqueo, text="Verificando conexión con el servidor...",
                                       font=("Segoe UI", 11, "bold"), fg="#eab308", bg=COLOR_LOCK_BG)
        self.lbl_alerta_red.pack(pady=5)

        self.frame_offline_login = tk.Frame(self.frame_bloqueo, bg=COLOR_LOCK_BG)
        self.frame_offline_login.pack(pady=15)

        tk.Label(self.frame_offline_login, text="Ingrese su ID para ingresar en Modo Offline:",
                 font=("Segoe UI", 11), fg="#ffffff", bg=COLOR_LOCK_BG).pack(pady=15)

        self.entry_login_id = tk.Entry(self.frame_offline_login, bg="#1e1e1e", fg=COLOR_TEXT, insertbackground="white",
                                       relief="solid", bd=1, font=("Segoe UI", 14), width=22, justify="center")
        self.entry_login_id.pack(pady=5)
        self.entry_login_id.bind("<Return>", lambda e: self.intentar_autenticacion_local())

        self.btn_ingresar_local = tk.Button(self.frame_offline_login, text="Iniciar Sesión Local", command=self.intentar_autenticacion_local,
                                            bg=COLOR_ACCENT, fg=COLOR_TEXT, bd=0, font=("Segoe UI", 11, "bold"), padx=20, pady=8, cursor="hand2")
        self.btn_ingresar_local.pack(pady=15)

        self.frame_barra_activa = tk.Frame(self.root, bg="#1a1a1a", height=40)
        btn_terminar = tk.Button(
            self.frame_barra_activa, text="❌ Terminar Sesión", command=self.solicitar_cierre_manual_usuario,
            bg="#dc2626", fg="white", font=("Segoe UI", 9, "bold"), bd=0, padx=10, cursor="hand2"
        )
        btn_terminar.pack(side="right", padx=15, pady=5)
        self.lbl_cronometro = tk.Label(self.frame_barra_activa, text="Tiempo Restante: 00:00:00",
                                       font=("Segoe UI", 11, "bold"), fg="#16a34a", bg="#1a1a1a")
        self.lbl_cronometro.pack(side="left", padx=20, expand=True)

    def textos_bloqueo_normal(self):
        self.lbl_titulo.config(text=f"COMPUTADOR DE USO RESTRINGIDO\nTERMINAL N° {ID_CLIENTE}", fg=COLOR_TEXT)
        self.lbl_alerta_red.config(text="● CONECTADO AL SERVIDOR CENTRAL", fg="#16a34a")

    def configurar_pantalla_segun_estado(self):
        self.guardar_estado_local()

        if self.bloqueado:
            self.frame_barra_activa.pack_forget()
            self.frame_bloqueo.pack(expand=True, fill="both")

            self.root.attributes("-fullscreen", True)
            self.root.attributes("-topmost", True)

            es_pausa = self.tiempo_segundos > 0
            offline_prohibido = not self.config.get("permitir_offline", True)

            if es_pausa or offline_prohibido:
                self.frame_offline_login.pack_forget()
            else:
                self.frame_offline_login.pack(pady=15)

            if self.tiempo_segundos == 0:
                self.textos_bloqueo_normal()

            self.forzar_foco_bloqueo()
        else:
            self.frame_bloqueo.pack_forget()
            self.frame_barra_activa.pack(fill="x", side="top")

            self.root.attributes("-fullscreen", False)
            self.root.attributes("-topmost", True)
            ancho = self.root.winfo_screenwidth()
            self.root.geometry(f"{ancho}x40+0+0")
            self.root.grab_release()

    def intentar_autenticacion_local(self):
        """Valida las credenciales en Modo Offline utilizando la caché SQLite."""
        if not self.bloqueado: return

        u_id = self.entry_login_id.get().strip()
        if not u_id: return

        if not self.config.get("permitir_offline", True):
            self.root.grab_release()
            messagebox.showerror("Bloqueado", "El modo offline está deshabilitado por el Servidor.")
            self.root.grab_set()
            return

        cursor = self.conn_local.cursor()
        cursor.execute("SELECT nombre FROM usuarios_locales WHERE id = ?", (u_id,))
        res = cursor.fetchone()

        if res:
            self.usuario_actual = u_id
            self.nombre_actual = res[0]
            self.tiempo_segundos = self.config.get("tiempo_predeterminado_minutos", 60) * 60
            self.bloqueado = False
            self.sesion_offline = True

            self.entry_login_id.delete(0, tk.END)
            self.configurar_pantalla_segun_estado()

            paquete_offline = {
                "accion": "sincronizar_offline",
                "id_cliente": ID_CLIENTE,
                "usuario": self.usuario_actual,
                "nombre": self.nombre_actual,
                "tiempo_restante": self.tiempo_segundos
            }
            self.enviar_json(paquete_offline)
        else:
            self.root.grab_release()
            messagebox.showerror("Error de Acceso", "ID no registrado en esta terminal. Requiere activación del Servidor.")
            self.root.grab_set()


    # HILO DE CONTROL DE RED Y AUTO-BLOQUEO POR CABLE

    def bucle_conexion_red(self):
        while True:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            try:
                sock.connect((SERVER_IP, PORT))
                sock.settimeout(None)

                self.socket_activo = sock
                self.red_disponible = True
                self.lbl_alerta_red.config(text="● CONECTADO AL SERVIDOR CENTRAL", fg="#16a34a")

                # Registro con protocolo delimitado por \n
                paquete_registro = {"accion": "registrarse", "id_cliente": ID_CLIENTE}
                self.enviar_json(paquete_registro)

                if self.sesion_offline and self.tiempo_segundos > 0:
                    paquete_reporte = {
                        "accion": "sincronizar_offline",
                        "id_cliente": ID_CLIENTE,
                        "usuario": self.usuario_actual,
                        "nombre": self.nombre_actual,
                        "tiempo_restante": self.tiempo_segundos
                    }
                    if self.enviar_json(paquete_reporte):
                        self.sesion_offline = False

                # LECTURA POR BUFFER (Resuelve el JSONDecodeError al recibir múltiples paquetes)
                buffer = ""
                while self.red_disponible:
                    chunk = sock.recv(4096).decode('utf-8')
                    if not chunk: break
                    buffer += chunk

                    while '\n' in buffer:
                        data, buffer = buffer.split('\n', 1)
                        if not data.strip(): continue

                        cmd = json.loads(data)
                        accion = cmd.get("accion")

                        if accion == "actualizar_config":
                            self.config["permitir_offline"] = cmd.get("permitir_offline", True)
                            self.config["tiempo_predeterminado_minutos"] = cmd.get("tiempo_predeterminado_minutos", 60)
                            try:
                                with open(ARCH_CONFIG, "w", encoding="utf-8") as f:
                                    json.dump(self.config, f, indent=4)
                            except Exception as e:
                                print(f"Error al guardar configuración: {e}")

                            usuarios_server = cmd.get("usuarios", {})
                            self.reemplazar_usuarios_locales(usuarios_server)

                        elif accion == "desbloqueo_remoto":
                            self.usuario_actual = cmd.get("usuario_id")
                            self.nombre_actual = cmd.get("nombre")
                            self.tiempo_segundos = cmd.get("tiempo_segundos")
                            self.bloqueado = False
                            self.sesion_offline = False
                            self.root.after(0, self.configurar_pantalla_segun_estado)

                        elif accion == "mostrar_mensaje":
                            texto_recibido = cmd.get("contenido", "")
                            self.root.after(0, lambda: self.desplegar_notificacion_admin(texto_recibido))

                        elif accion == "pausar_terminal":
                            self.bloqueado = True
                            self.root.after(0, lambda: self.forzar_pantalla_pausa("Terminal PAUSADA temporalmente."))

                        elif accion == "reanudar_terminal":
                            self.bloqueado = False
                            self.root.after(0, self.configurar_pantalla_segun_estado)

                        elif accion == "bloquear_terminal":
                            self.bloqueado = True
                            self.usuario_actual = "-"
                            self.nombre_actual = "-"
                            self.tiempo_segundos = 0
                            self.root.after(0, self.configurar_pantalla_segun_estado)

            except (socket.error, socket.timeout, json.JSONDecodeError) as e:
                self.red_disponible = False
                self.lbl_alerta_red.config(text="⚠️ TERMINAL SIN RED: CONEXIÓN INTERRUMPIDA", fg=COLOR_DANGER)

            finally:
                try: sock.close()
                except: pass
                self.socket_activo = None
                time.sleep(5)

    # MOTOR INTERNO DEL CRONÓMETRO DE LA TERMINAL

    def motor_cronometro(self):
        alerta_15_enviada = False
        alerta_5_enviada = False
        contador_guardado_db = 0

        while True:
            time.sleep(1)

            if self.bloqueado:
                alerta_15_enviada = False
                alerta_5_enviada = False
                continue

            if not self.bloqueado and self.tiempo_segundos > 0:
                self.tiempo_segundos -= 1

                # Guardado persistente local cada 5 segundos para proteger el saldo ante apagones
                contador_guardado_db += 1
                if contador_guardado_db >= 5:
                    self.guardar_estado_local()
                    contador_guardado_db = 0

                hrs = self.tiempo_segundos // 3600
                mins = (self.tiempo_segundos % 3600) // 60
                segs = self.tiempo_segundos % 60
                self.lbl_cronometro.config(text=f"Tiempo Restante: {hrs:02d}:{mins:02d}:{segs:02d}")

                if self.tiempo_segundos == 900 and not alerta_15_enviada:
                    alerta_15_enviada = True
                    msg = "⚠️ Aviso de cortesía: Te quedan 15 minutos de sesión disponibles en esta terminal."
                    self.root.after(0, lambda m=msg: self.desplegar_notificacion_admin(m))

                elif self.tiempo_segundos == 300 and not alerta_5_enviada:
                    alerta_5_enviada = True
                    msg = "🚨 ¡Atención! Te quedan solo 5 minutos. Guarda tu trabajo para evitar pérdida de información."
                    self.root.after(0, lambda m=msg: self.desplegar_notificacion_admin(m))

            if self.tiempo_segundos <= 0 and not self.bloqueado:
                self.bloqueado = True
                self.usuario_actual = "-"
                self.nombre_actual = "-"
                self.root.after(0, self.configurar_pantalla_segun_estado)

                paquete = {"accion": "tiempo_agotado_cliente", "id_cliente": ID_CLIENTE}
                self.enviar_json(paquete)

    def desplegar_notificacion_admin(self, mensaje):
        """Muestra una ventana emergente en el cliente con el aviso del administrador."""
        v_alerta = tk.Toplevel(self.root)
        v_alerta.title("Mensaje del Bibliotecario")
        v_alerta.geometry("400x180")
        v_alerta.configure(bg="#1a1a1a")
        v_alerta.resizable(False, False)
        v_alerta.attributes("-topmost", True)

        v_alerta.update_idletasks()
        ancho = v_alerta.winfo_width()
        alto = v_alerta.winfo_height()
        x = (v_alerta.winfo_screenwidth() // 2) - (ancho // 2)
        y = (v_alerta.winfo_screenheight() // 2) - (alto // 2)
        v_alerta.geometry(f"+{x}+{y}")

        # Contenido visual
        tk.Label(v_alerta, text="📢 ATENCIÓN - MENSAJE DEL BIBLIOTECARIO", font=("Segoe UI", 11, "bold"), fg=COLOR_ACCENT, bg="#1a1a1a").pack(pady=12)
        lbl_msg = tk.Label(v_alerta, text=mensaje, font=("Segoe UI", 11), fg=COLOR_TEXT, bg="#1a1a1a", wraplength=360, justify="center")
        lbl_msg.pack(expand=True, fill="both", padx=20)

        btn_entendido = tk.Button(v_alerta, text="Entendido", command=v_alerta.destroy, bg="#3e3e42", fg=COLOR_TEXT, bd=0, font=("Segoe UI", 10, "bold"), padx=20, pady=5, cursor="hand2")
        btn_entendido.pack(pady=15)

    def solicitar_cierre_manual_usuario(self):
        if messagebox.askyesno("Terminar Servicio", "¿Estás seguro de que deseas cerrar tu sesión ahora?\nEl tiempo restante se perderá."):
            paquete = {"accion": "tiempo_agotado_cliente", "id_cliente": ID_CLIENTE}
            self.enviar_json(paquete)

            self.bloqueado = True
            self.usuario_actual = "-"
            self.nombre_actual = "-"
            self.tiempo_segundos = 0
            self.configurar_pantalla_segun_estado()

    def forzar_pantalla_pausa(self, mensaje_alerta):
        self.configurar_pantalla_segun_estado()
        try:
            self.lbl_titulo.config(text="⚠️ SESIÓN SUSPENDIDA TEMPORALMENTE", fg="#eab308")
            self.lbl_alerta_red.config(text=mensaje_alerta + "\nConsulte con el administrador de BIBLIOTECA.")
        except:
            pass

    def forzar_foco_bloqueo(self):
        if self.bloqueado:
            self.root.grab_set()

            # Si el campo de texto existe y está visible en pantalla, el foco debe ir hacia él
            if hasattr(self, 'entry_login_id') and self.entry_login_id.winfo_viewable():
                self.entry_login_id.focus_force()
                self.root.bind("<FocusOut>", lambda e: self.entry_login_id.focus_force() if self.bloqueado else None)
            else:
                self.root.focus_force()
                self.root.bind("<FocusOut>", lambda e: self.root.focus_force() if self.bloqueado else None)

            self.root.after(1000, self.forzar_foco_bloqueo)

if __name__ == "__main__":
    root = tk.Tk()
    ruta_icono = resource_path("icono.ico")
    if os.path.exists(ruta_icono):
        try:
            root.iconbitmap(ruta_icono)
        except Exception as e:
            print(f"No se pudo cargar el ícono: {e}")
    app = ClienteTerminal(root)
    root.mainloop()