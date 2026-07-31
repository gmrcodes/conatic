# LAUNCHER -WATCHDOG PARA EL CLIENTE
# Este script es un "watchdog" que se asegura de que la aplicación cliente esté siempre corriendo.
# ==============================================================================
# Versión: 0.3.0
# ==============================================================================
import os
import sys
import time
import subprocess
import socket
import platform
import signal

PUERTO_MUTEX_CLIENTE = 65431
PUERTO_MUTEX_LAUNCHER = 65434

# ==============================================================================
# 🛡️ EVITAR MULTIPLES INSTANCIAS DEL LAUNCHER POR LOCKSOCKET
# ==============================================================================

try:
    lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    lock_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
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

# OBTENER RUTA DEL CLIENTE
# =============================================================================
def get_base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = get_base_dir()

APP_NAME = "cliente.exe" if SISTEMA_OPERATIVO == "Windows" else "cliente"

CLIENTE_PATH = os.path.join(BASE_DIR, APP_NAME)

# FUNCIONES AUXILIARES
# =============================================================================

def cliente_esta_activo():
    """Intenta conectarse al puerto mutex del cliente.
    Si la conexión se realiza con éxito, significa que el cliente está activo."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.5)

    try:
        s.connect(("127.0.0.1", PUERTO_MUTEX_CLIENTE))
        return True # Cliente activo
    except OSError:
        return False # Cliente inactivo
    finally:
        s.close()

def iniciar_cliente():

    if not os.path.exists(CLIENTE_PATH):
        print(f"[!] No se encontró el cliente en: {CLIENTE_PATH}")
        return

    if SISTEMA_OPERATIVO != "Windows":                    
        # En Linux y macOS, aseguramos que el cliente sea ejecutable
        try:
            os.chmod(CLIENTE_PATH, 0o755)
        except Exception as e:
            print(f"Error al cambiar permisos de {CLIENTE_PATH}: {e}")

    try:
        # Intentar iniciar el cliente
        subprocess.Popen([CLIENTE_PATH], cwd=BASE_DIR, close_fds=True)

    except Exception as e:
        print(f"[!] Error al intentar iniciar el cliente: {e}")

    time.sleep(1)  # Esperar un segundo para que el cliente inicie correctamente

# CIERRE DE LAUNCHER CON MANEJO DE SEÑALES
# =============================================================================

def salir_launcher(_signum, _frame):
    sys.exit(0)

signal.signal(signal.SIGINT, salir_launcher)
signal.signal(signal.SIGTERM, salir_launcher)

if SISTEMA_OPERATIVO == "Windows":
    signal.signal(signal.SIGBREAK, salir_launcher)

# ==============================================================================
# LÓGICA DEL WATCHDOG (OPTIMIZADA)
# ==============================================================================

while True:
    try:
        if not cliente_esta_activo():
            iniciar_cliente()

        time.sleep(2)

    except PermissionError:
        print(f"[!] Permiso denegado al intentar ejecutar: {CLIENTE_PATH}")
        time.sleep(5)        
    except Exception as e:
        # Evitar que el launcher colapse por algún error imprevisto
        print(f"[!] Excepción inesperada en el watchdog: {e}")
        time.sleep(5)