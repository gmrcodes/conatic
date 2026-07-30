# LAUNCHER -WATCHDOG PARA EL CLIENTE
# Este script es un "watchdog" que se asegura de que la aplicación cliente esté siempre corriendo.
# ==============================================================================
# Versión: 0.2.0
# ==============================================================================
import os
import sys
import time
import subprocess
import socket
import platform
import signal

# ==============================================================================
# 🛡️ EVITAR MULTIPLES INSTANCIAS DEL LAUNCHER POR LOCKSOCKET
# ==============================================================================

PUERTO_MUTEX_LAUNCHER = 65434

try:
    lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    lock_socket.bind(("127.0.0.1", PUERTO_MUTEX_LAUNCHER))
    lock_socket.listen(1)
except socket.error:
    print("[!] El cliente watchdog ya se encuentra en ejecución.")
    try:
        from tkinter import messagebox
        messagebox.showerror("Error", "El cliente watchdog ya se encuentra en ejecución.")
    except Exception:
        pass
    sys.exit(0)

# DETECTAR SISTEMA OPERATIVO
# =============================================================================
SISTEMA_OPERATIVO = platform.system()

# CONFIGURACION DE RUTA DEL CLIENTE
# =============================================================================
def get_base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = get_base_dir()

APP_NAME = "cliente.exe" if SISTEMA_OPERATIVO == "Windows" else "cliente"

CLIENTE_PATH = os.path.join(BASE_DIR, APP_NAME)

# CONTROL DE CIERRE DEL PROCESO CLIENTE CON MANEJO DE SEÑALES
# =============================================================================
proceso_cliente = None

def terminar_proceso_hijo(signum, frame):
    """ Garantiza que al cerrar el launcher también se detenga el cliente """
    global proceso_cliente
    print("\n[*] Cerrando el watchdog y finalizando procesos...")
    if proceso_cliente and proceso_cliente.poll() is None:
        try:
            proceso_cliente.terminate()
            proceso_cliente.wait(timeout=2)
        except Exception:
            proceso_cliente.kill()
    sys.exit(0)

# Interceptar peticiones de cierre del sistema operativo
signal.signal(signal.SIGINT, terminar_proceso_hijo)
signal.signal(signal.SIGTERM, terminar_proceso_hijo)

# ==============================================================================
# LÓGICA DEL WATCHDOG (OPTIMIZADA A 0% DE CPU)
# ==============================================================================

while True:
    try:
        if os.path.exists(CLIENTE_PATH):
            if SISTEMA_OPERATIVO != "Windows":
                # En Linux y macOS, aseguramos que el cliente sea ejecutable
                try:
                    os.chmod(CLIENTE_PATH, 0o755)
                except Exception as e:
                    print(f"Error al cambiar permisos de {CLIENTE_PATH}: {e}")

            tiempo_inicio = time.time()

            # Lanzamos el cliente y guardamos la referencia del proceso
            proceso_cliente = subprocess.Popen([CLIENTE_PATH])
            
            # .wait() congela este script de forma pasiva sin consumir CPU.            
            proceso_cliente.wait()

            duracion = time.time() - tiempo_inicio

            if duracion < 3:
                print("[*] El cliente se cerró prematuramente. Reiniciando en 3 segundos...")
                time.sleep(3)
        else:
            print(f"Error: No se encontró el ejecutable en: {CLIENTE_PATH}")
            time.sleep(5) # Esperar antes de reintentar buscar el ejecutable

    except PermissionError:
        print(f"[!] Permiso denegado al intentar ejecutar: {CLIENTE_PATH}")
        time.sleep(5)        
    except Exception as e:
        # Evitar que el launcher colapse por algún error imprevisto
        print(f"[!] Excepción inesperada en el watchdog: {e}")
        time.sleep(2)