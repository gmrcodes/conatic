# Historial de Cambios - Cliente

Todos los cambios notables en el cliente serán documentados en este archivo.
El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/)
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [0.5.2] - 2026-07-29

### Corregido (Fix)

- Solución de sintaxis en `resource_path()` para resolución correcta de la carpeta `resources/` en entornos `.spec` , `.py` y `binarios`.
- Corrección de _Garbage Collection_ en Tkinter manteniendo referencia de `_app_icon`.

## [0.5.1] - 2026-07-28

### Corregido (Fix)

- Soporte multiplataforma para íconos (`client.ico` en Windows, `client.png` en Linux/macOS).
- Soporte multiplataforma para logo.png

### Añadido

- Soporte (UX) para fuente predeterminada según el sistema operativo.

## [0.5.0] - 2026-07-27

### Añadido (Feat)

- Compatibilidad con S.O. Windows y Linux
- Mecanismo de instancia única (Mutex) mediante puerto socket interno (`65431`).
- Abstracción de rutas dinámicas según el sistema operativo (`%LOCALAPPDATA%` en Windows, `~/.local/share` en Linux).
- Ajuste de rutas del archivo config_cliente.json y de la cache_cliente.db según el S.O.

## [0.4.1] - 2026-07-26

### Corregido (Fix)

- Se mejora la concurrencia con la DB para evitar perdidas de información.

### Mantenimiento (Chore)

- Se hace limpieza del código y se eliminan dependencias que ya no se usan (ctypes, psutil)

## [0.4.0] - 2026-07-25

### Añadido (Feat)

- Mutex a nivel de red mediante Socket Local (PUERTO_MUTEX_INTERNO = 65431) para impedir la ejecución de instancias múltiples.
- Abstracción del sistema operativo (SISTEMA_OPERATIVO = platform.system()).
- Se eliminó el Mutex implementado con ctypes que solo funionaba en Windows.

## [0.3.1] - 2026-07-23

### Corregido (Fix)

- Ajuste de rutas del archivo config_cliente.json y de la cache_cliente.db.

## [0.3.0] - 2026-07-10

### Añadido (Feat)

- Manejo de temporizadores de sesión, conteos regresivos sincronizados con el servidor y desbloqueos por pase de administración.
- Implementación de la función ruta_carpeta_appdata() respetando el estándar %LOCALAPPDATA% en Windows y XDG (~/.local/share) en Linux.
- Soporte para resource_path() compatible con ejecuciones .py y binarios empaquetados mediante PyInstaller (sys.\_MEIPASS).
- Mutex con manejo de libreria ctypes para Windows.
- Launcher para relanzar automáticamente cliente.exe cuando no está en ejecución.

## [0.2.1] - 2026-07-06

### Corregido (Fix)

- Ahora La persistencia en la base de datos local cache_cliente.db guarda correctamente los tiempos de sesión.

## [0.2.0] - 2026-07-03

### Añadido (Feat)

- Implementación del bloqueo de pantalla en modo Kiosk (overrideredirect, pantalla completa, binding de eventos de foco).
- Integración de SQLite local (cache_cliente.db) para persistencia de credenciales/sesiones.
- Bloqueo de combinaciones de teclas nativas Alt+F4.

## [0.1.0] - 2026-06-30

### Añadido (Feat)

- Creación de la interfaz básica en tkinter.
- Implementación del hilo (threading) para el socket TCP cliente.
- Envío y recepción de marcos de red en formato JSON.
