# CODIGO CLIENTE V 1.2 - CON PERSISTENCIA
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
import ctypes
from ctypes import wintypes

# 🛡️ Evitar múltiples instancias del Cliente
ERROR_ALREADY_EXISTS = 183
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
CreateMutex = kernel32.CreateMutexW
CreateMutex.argtypes = [wintypes.LPCVOID, wintypes.BOOL, wintypes.LPCWSTR]
CreateMutex.restype = wintypes.HANDLE

# Este nombre DEBE coincidir con el de AppMutex de Inno Setup
MUTEX_CLIENTE = "ControlClienteMutexSecret"

mutex_handle_cliente = CreateMutex(None, False, MUTEX_CLIENTE)
if kernel32.GetLastError() == ERROR_ALREADY_EXISTS:
    # Si el cliente ya está abierto, esta copia se destruye inmediatamente
    sys.exit(0)

# CONFIGURACIÓN DEL CLIENTE
#BASE_DIR = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))
#ARCH_CONFIG = os.path.join(BASE_DIR, "config_cliente.json")

def resource_path(relative_path):
    """
    Devuelve la ruta correcta tanto al ejecutar el .py
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

ARCH_CONFIG = os.path.join(
    os.path.dirname(sys.executable)
    if getattr(sys, "frozen", False)
    else os.path.dirname(os.path.abspath(__file__)),
    "config_cliente.json",
)

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
            with open(ARCH_CONFIG, "r") as f:
                # Combina los valores existentes del JSON con los default
                return {**config_defecto, **json.load(f)}
        except:
            return config_defecto
    return config_defecto

# Cargar los datos config del JSON antes de que levante la interfaz gráfica
CONFIG_SISTEMA = cargar_configuracion_completa()

# CONFIGURACIÓN DINÁMICA AHORA CARGADA DEL JSON
ID_CLIENTE = CONFIG_SISTEMA["id_cliente"]
SERVER_IP = CONFIG_SISTEMA["server_ip"]
PORT = 65432

# PALETA DE COLORES (PANTALLA DE BLOQUEO)
COLOR_LOCK_BG = "#0c0c0d"
COLOR_TEXT = "#ffffff"
COLOR_ACCENT = "#007acc"
COLOR_DANGER = "#dc2626"

class ClienteTerminal:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Terminal Cliente N° {ID_CLIENTE}")

        # Variables de estado
        self.bloqueado = True
        self.sesion_offline = False
        self.usuario_actual = "-"
        self.nombre_actual = "-"
        self.tiempo_segundos = 0
        self.red_disponible = False

        # Cargar configuración
        self.config = CONFIG_SISTEMA

        # Inicializar base de datos local (Caché) y recuperar estado previo
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
        self.conn_local = sqlite3.connect("cache_cliente.db", check_same_thread=False)
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

    # FUNCION DE PERSISTENCIA DE ESTADO

    def guardar_estado_local(self):
        """Escribe el estado crítico de la app en la base de datos local."""
        try:
            cursor = self.conn_local.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO estado_sesion (clave, usuario, nombre, tiempo_segundos, sesion_offline, bloqueado)
                VALUES ('actual', ?, ?, ?, ?, ?)
            """, (self.usuario_actual, self.nombre_actual, self.tiempo_segundos, int(self.sesion_offline), int(self.bloqueado)))
            self.conn_local.commit()
        except Exception as e:
            print(f"Error al escribir en la caja negra SQLite: {e}")

    # Función para recuperar el estado de la sesión desde la base de datos local
    def recuperar_estado_local(self):
        """Busca si el programa viene de un cierre forzado para restaurar el tiempo maestro."""
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
            print(f"Error al leer de la caja negra SQLite: {e}")

    def reemplazar_usuarios_locales(self, diccionario_usuarios):
        """Sincroniza la caché local con los usuarios válidos del servidor."""
        cursor = self.conn_local.cursor()
        cursor.execute("DELETE FROM usuarios_locales")
        for u_id, nombre in diccionario_usuarios.items():
            cursor.execute("INSERT OR REPLACE INTO usuarios_locales (id, nombre) VALUES (?, ?)", (u_id, nombre))
        self.conn_local.commit()

    def crear_componentes_ui(self):
        # Contenedor principal de la Pantalla de Bloqueo
        self.frame_bloqueo = tk.Frame(self.root, bg=COLOR_LOCK_BG)

        # LOGO

        ruta_logo = resource_path("logo.png")
        if os.path.exists(ruta_logo):
            try:
              # Abrir imagen
              img_original = Image.open(ruta_logo)
              # Redimensionar imagen para la pantalla del cliente
              ancho_orig, alto_orig = img_original.size
              nuevo_ancho = self.frame_bloqueo.winfo_screenwidth() // 3
              nuevo_alto = int((nuevo_ancho / ancho_orig) * alto_orig)
              img_redimensionada = img_original.resize((nuevo_ancho, nuevo_alto), Image.Resampling.LANCZOS)
              # Convertir al formato compatible con Tkinter
              self.logo_tk = ImageTk.PhotoImage(img_redimensionada)
              # Insertar la imagen dentro de un Label sin bordes ni fondo
              lbl_logo = tk.Label(self.frame_bloqueo, image=self.logo_tk, bg=COLOR_LOCK_BG)
              lbl_logo.pack(side="top", pady=(40, 10)) # Margen de 40px arriba y 10px abajo
            except Exception as e:
              print(f"No se pudo desplegar el logo: {e}")
        else:
            print("Archivo logo.png no encontrado en la ruta.")

        # TITULO

        self.lbl_titulo = tk.Label(self.frame_bloqueo, text=f"COMPUTADOR DE USO RESTRINGIDO\nTERMINAL N° {ID_CLIENTE}",
                                   font=("Segoe UI", 18, "bold"), fg=COLOR_TEXT, bg=COLOR_LOCK_BG)
        self.lbl_titulo.pack(pady=30)

        # ALERTA DE RED
        self.lbl_alerta_red = tk.Label(self.frame_bloqueo, text="Verificando conexión con el servidor...",
                                       font=("Segoe UI", 11, "bold"), fg="#eab308", bg=COLOR_LOCK_BG)
        self.lbl_alerta_red.pack(pady=5)

        self.frame_offline_login = tk.Frame(self.frame_bloqueo, bg=COLOR_LOCK_BG)
        self.frame_offline_login.pack(pady=15)

        self.label_codigo_offline = tk.Label(self.frame_offline_login, text="Ingrese su ID para ingresar en Modo Offline:",
                 font=("Segoe UI", 11), fg="#ffffff", bg=COLOR_LOCK_BG).pack(pady=15)

        self.entry_login_id = tk.Entry(self.frame_offline_login, bg="#1e1e1e", fg=COLOR_TEXT, insertbackground="white",
                                       relief="solid", bd=1, font=("Segoe UI", 14), width=22, justify="center")
        self.entry_login_id.pack(pady=5)
        self.entry_login_id.bind("<Return>", lambda e: self.intentar_autenticacion_local())

        self.btn_ingresar_local = tk.Button(self.frame_offline_login, text="Iniciar Sesión Local", command=self.intentar_autenticacion_local,
                                            bg=COLOR_ACCENT, fg=COLOR_TEXT, bd=0, font=("Segoe UI", 11, "bold"), padx=20, pady=8, cursor="hand2")
        self.btn_ingresar_local.pack(pady=15)

        # Contenedor BARRA FLOTANTE (Cuando el equipo está activo y desbloqueado)
        self.frame_barra_activa = tk.Frame(self.root, bg="#1a1a1a", height=40)
        btn_terminar = tk.Button(
            self.frame_barra_activa,
            text="❌ Terminar Sesión",
            command=self.solicitar_cierre_manual_usuario,
            bg="#dc2626", # Rojo
            fg="white",
            font=("Segoe UI", 9, "bold"),
            bd=0,
            padx=10,
            cursor="hand2"
        )
        btn_terminar.pack(side="right", padx=15, pady=5)
        self.lbl_cronometro = tk.Label(self.frame_barra_activa, text="Tiempo Restante: 00:00:00",
                                       font=("Segoe UI", 11, "bold"), fg="#16a34a", bg="#1a1a1a")
        self.lbl_cronometro.pack(side="left", padx=20, expand=True)

    def textos_bloqueo_normal(self):
      self.lbl_titulo.config(text=f"COMPUTADOR DE USO RESTRINGIDO\nTERMINAL N° {ID_CLIENTE}",
                  fg=COLOR_TEXT)
      self.lbl_alerta_red.config(text="● CONECTADO AL SERVIDOR CENTRAL", fg="#16a34a")

    def configurar_pantalla_segun_estado(self):
        """Aplica el blindaje de pantalla completa o minimiza a barra flotante."""
        if self.bloqueado:
          self.frame_barra_activa.pack_forget()
          self.frame_bloqueo.pack(expand=True, fill="both")

          # Forzar Pantalla Completa absoluta sobre todas las barras del sistema
          self.root.attributes("-fullscreen", True)
          self.root.attributes("-topmost", True)

          es_pausa = self.tiempo_segundos > 0
          offline_prohibido = not self.config.get("permitir_offline", True)

          if es_pausa or offline_prohibido:
            try:
              self.frame_offline_login.pack_forget() # Oculta el login offline
            except:
              pass
          else:
            try:
                # Si no es pausa y está permitido, lo volvemos a mostrar abajo
                self.frame_offline_login.pack(pady=15)
            except:
                pass

          # Restauración de textos si es bloqueo total
          if self.tiempo_segundos == 0:
              try:
                self.textos_bloqueo_normal()
              except:
                pass

          self.forzar_foco_bloqueo()
        else:
          self.frame_bloqueo.pack_forget()
          self.frame_barra_activa.pack(fill="x", side="top")

          if self.tiempo_segundos == 0:
            try:
              self.textos_bloqueo_normal()
            except Exception as e:
                print(f"Error al restaurar textos: {e}")
            self.root.update()
            self.root.grab_set() # Secuestra el mouse y teclado para que no den clics fuera de la app
          else:
            self.frame_bloqueo.pack_forget()
            self.frame_barra_activa.pack(fill="x", side="top")

            # Convertir en una barra superior pequeña y delgada
            self.root.attributes("-fullscreen", False)
            self.root.attributes("-topmost", True)
            # Dimensiones de la barra superior
            ancho = self.root.winfo_screenwidth()
            self.root.geometry(f"{ancho}x40+0+0")
            self.root.grab_release() # Libera el mouse para que puedan usar sus programas normalmente

    def intentar_autenticacion_local(self):
        """Valida las credenciales en Modo Offline utilizando la caché SQLite."""
        if not self.bloqueado: return

        u_id = self.entry_login_id.get().strip()
        if not u_id: return

        if not self.config.get("permitir_offline", True):
            messagebox.showerror("Bloqueado", "El modo offline está deshabilitado por el Bibliotecario.")
            return

        cursor = self.conn_local.cursor()
        cursor.execute("SELECT nombre FROM usuarios_locales WHERE id = ?", (u_id,))
        res = cursor.fetchone()

        if res:
            self.usuario_actual = u_id
            self.nombre_actual = res[0]
            # Le asigno el tiempo de emergencia configurado en el JSON local
            self.tiempo_segundos = self.config.get("tiempo_predeterminado_minutos", 60) * 60
            self.bloqueado = False
            self.sesion_offline = True # Bandera encendida para avisar al servidor después

            self.entry_login_id.delete(0, tk.END)
            self.configurar_pantalla_segun_estado()

            if hasattr(self, 'socket_activo') and self.red_disponible:
              try:
                paquete_offline = {
                    "accion": "sincronizar_offline",
                    "id_cliente": ID_CLIENTE,
                    "usuario": self.usuario_actual,
                    "nombre": self.nombre_actual,
                    "tiempo_restante": self.tiempo_segundos
                }
                self.socket_activo.sendall(json.dumps(paquete_offline).encode('utf-8'))
              except Exception as e:
                print(f"Error al sincronizar inicio offline por red: {e}")
        else:
            messagebox.showerror("Error de Acceso", "ID no registrado en esta terminal. Requiere activación remota del Servidor.")


    # HILO DE CONTROL DE RED Y AUTO-BLOQUEO POR CABLE

    def bucle_conexion_red(self):
      while True:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Timeout para evitar que se quede congelado si la IP no responde
        sock.settimeout(10)
        try:
          sock.connect((SERVER_IP, PORT))
          # Quita el timeout una vez conectados para que recv() pueda esperar comandos
          sock.settimeout(None)

          self.socket_activo = sock # Guardamos el socket fresco en la variable global
          self.red_disponible = True
          self.lbl_alerta_red.config(text="● CONECTADO AL SERVIDOR CENTRAL", fg="#16a34a")

          # Presentarse ante el servidor
          paquete_registro = {"accion": "registrarse", "id_cliente": ID_CLIENTE}
          sock.sendall(json.dumps(paquete_registro).encode('utf-8'))

          # SINCRONIZACIÓN RETROACTIVA OFFLINE
          # Al conectar con éxito, si viene de un desbloqueo offline aislado:
          if self.sesion_offline and self.tiempo_segundos > 0:
            #minutos_restantes = self.tiempo_segundos // 60
            paquete_reporte = {
                "accion": "sincronizar_offline",
                "id_cliente": ID_CLIENTE,
                "usuario": self.usuario_actual,
                "nombre": self.nombre_actual,
                "tiempo_restante": self.tiempo_segundos
            }

            try:
              sock.sendall(json.dumps(paquete_reporte).encode('utf-8'))
              self.sesion_offline = False # Reportado con éxito, apaga la bandera
              print("✅ Reporte de sesión offline sincronizado en el Servidor.")
            except Exception as e:
              print(f"Error al enviar reporte de reconexión: {e}")

          # Monitorea activamente la salud de la red)
          while self.red_disponible:
            try:
              data = sock.recv(4096).decode('utf-8')
            except:
              data = None # Si el recv falla por desconexión física, forza la salida

            if not data:
              # Si recv devuelve vacío o falla, significa que el servidor se cerró o el cable de red se desconectó.
              break

            cmd = json.loads(data)
            accion = cmd.get("accion")

            if accion == "actualizar_config":
              self.config["permitir_offline"] = cmd.get("permitir_offline", True)
              self.config["tiempo_predeterminado_minutos"] = cmd.get("tiempo_predeterminado_minutos", 60)
              with open(ARCH_CONFIG, "w") as f:
                json.dump(self.config, f)

              # Guardar copia en SQLite local
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
          # PÉRDIDA DE RED DETECTADA O FALLO DESDE EL INICIO
          self.red_disponible = False
          self.lbl_alerta_red.config(text="⚠️ TERMINAL SIN RED: CONEXIÓN INTERRUMPIDA", fg=COLOR_DANGER)

          # Si el equipo estaba desbloqueado de forma normal de red, procedemos al cierre seguro
          if not self.bloqueado and not self.sesion_offline:
              pass

        finally:
          # Cierra el objeto socket viejo para liberar los descriptores del sistema
          try:
            sock.close()
          except:
            pass
          # Espera 5 segundos antes de crear un socket nuevo e intentar reconectar
          time.sleep(5)

    # MOTOR INTERNO DEL CRONÓMETRO DE LA TERMINAL

    def motor_cronometro(self):
        # Banderas para asegurar que cada alerta se muestre una sola vez por sesión
        alerta_15_enviada = False
        alerta_5_enviada = False

        while True:
            time.sleep(1)

            # Si el equipo se vuelve a bloquear o se reinicia el tiempo, restauramos las alertas
            if self.bloqueado:
                alerta_15_enviada = False
                alerta_5_enviada = False
                continue

            if not self.bloqueado and self.tiempo_segundos > 0:
                self.tiempo_segundos -= 1

                # Calcular horas, minutos y segundos para la barra superior
                hrs = self.tiempo_segundos // 3600
                mins = (self.tiempo_segundos % 3600) // 60
                segs = self.tiempo_segundos % 60
                texto_tiempo = f"Tiempo Restante: {hrs:02d}:{mins:02d}:{segs:02d}"

                self.lbl_cronometro.config(text=texto_tiempo)

                # CONTROL DE ALERTAS AUTOMÁTICAS

                # CASO A: Faltan exactamente 15 minutos (900 segundos)
                if self.tiempo_segundos == 900 and not alerta_15_enviada:
                    alerta_15_enviada = True
                    msg = "⚠️ Aviso de cortesía: Te quedan 15 minutos de sesión disponibles en esta terminal."
                    self.root.after(0, lambda m=msg: self.desplegar_notificacion_admin(m))

                # CASO B: Faltan exactamente 5 minutos (300 segundos)
                elif self.tiempo_segundos == 300 and not alerta_5_enviada:
                    alerta_5_enviada = True
                    msg = "🚨 ¡Atención! Te quedan solo 5 minutos. Guarda tu trabajo para evitar pérdida de información."
                    self.root.after(0, lambda m=msg: self.desplegar_notificacion_admin(m))

            # Si el tiempo se termina por completo
            if self.tiempo_segundos <= 0:
                self.bloqueado = True
                self.usuario_actual = "-"
                self.nombre_actual = "-"
                self.root.after(0, self.configurar_pantalla_segun_estado)

                # Aviso al servidor usando el canal ya existente
                if self.red_disponible and hasattr(self, 'socket_activo'):
                    try:
                        paquete = {"accion": "tiempo_agotado_cliente", "id_cliente": ID_CLIENTE}
                        self.socket_activo.sendall(json.dumps(paquete).encode('utf-8'))
                    except Exception as e:
                        print(f"Error al enviar notificación de tiempo agotado: {e}")

    def desplegar_notificacion_admin(self, mensaje):
        """Muestra una ventana emergente en el cliente con el aviso del administrador."""
        v_alerta = tk.Toplevel(self.root)
        v_alerta.title("Mensaje del Bibliotecario")
        v_alerta.geometry("400x180")
        v_alerta.configure(bg="#1a1a1a")
        v_alerta.resizable(False, False)

        # Aseguro que aparezca por encima de todo, pero sin bloquear el teclado general del usuario
        v_alerta.attributes("-topmost", True)

        # Centrar la ventana en la pantalla del usuario de forma dinámica
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

        # Botón normal de cierre ordinario
        btn_entendido = tk.Button(v_alerta, text="Entendido", command=v_alerta.destroy, bg="#3e3e42", fg=COLOR_TEXT, bd=0, font=("Segoe UI", 10, "bold"), padx=20, pady=5, cursor="hand2")
        btn_entendido.pack(pady=15)

    def solicitar_cierre_manual_usuario(self):
      """El usuario decide terminar voluntariamente su tiempo desde la barra superior."""
      if messagebox.askyesno("Terminar Servicio", "¿Estás seguro de que deseas cerrar tu sesión ahora?\nEl tiempo restante se perderá."):

        # Aviso al servidor por red de forma inmediata si hay conexión
        if self.red_disponible and hasattr(self, 'socket_activo'):
          try:
            paquete = {"accion": "tiempo_agotado_cliente", "id_cliente": ID_CLIENTE}
            self.socket_activo.sendall(json.dumps(paquete).encode('utf-8'))
          except Exception as e:
            print(f"Error al enviar salida al servidor: {e}")
          # Forzar el estado de bloqueo en la UI de inmediato
        self.bloqueado = True
        self.usuario_actual = "-"
        self.nombre_actual = "-"
        self.tiempo_segundos = 0
        self.configurar_pantalla_segun_estado()

    def forzar_pantalla_pausa(self, mensaje_alerta):
      """Modifica temporalmente la pantalla de bloqueo para reflejar la pausa técnica."""
      # Invoco el redibujado de bloqueo estándar (fullscreen y grab_set)
      self.configurar_pantalla_segun_estado()

      # Altero los textos principales de la pantalla de bloqueo para avisar al usuario
      try:
          self.lbl_titulo.config(text="⚠️ SESIÓN SUSPENDIDA TEMPORALMENTE", fg="#eab308") # Amarillo
          self.lbl_alerta_red.config(text=mensaje_alerta + "\nConsulte con el administrador de BIBLIOTECA.")
      except:
          pass

    def forzar_foco_bloqueo(self):
      """Mantiene el teclado y mouse secuestrados en la app impidiendo Alt+Tab eficaces."""
      if self.bloqueado:
          self.root.focus_force()
          self.root.grab_set()

          # Si el usuario presiona Alt+Tab, Tkinter pierde el foco.
          # lo auto-reclamo en el microsegundo exacto.
          self.root.bind("<FocusOut>", lambda e: self.entry_login_id.focus_force() if self.bloqueado else None)

          # Recursivamente para asegurar el ciclo de enfoque
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

# CREACION DE LAUNCHER

import os
import sys
import time
import psutil
import subprocess

APP_NAME = "cliente.exe"


def get_base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


BASE_DIR = get_base_dir()

CLIENTE = os.path.join(BASE_DIR, APP_NAME)


def cliente_activo():

    for p in psutil.process_iter(["name"]):

        if p.info["name"] == APP_NAME:

            return True

    return False


while True:

    if not cliente_activo():

        subprocess.Popen(CLIENTE)

    time.sleep(2)