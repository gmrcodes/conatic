# CHANGELOG - Launcher

Todos los cambios notables en el launcher serán documentados en este archivo.
El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/)
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [0.2.0] - 2026-07-30

### Añadido (Added)

- **Soporte Multiplataforma**: Detección automática del sistema operativo (`Windows`, `Linux`, `Darwin`) para invocar el binario correcto (`cliente.exe` o `cliente`).
- **Gestión de Señales del Sistema**: Implementación de manejadores de señales `SIGINT` y `SIGTERM` para garantizar la finalización limpia del cliente cuando el launcher sea detenido.
- **Protección Anti-Crash Loop**: Control de frecuencia de reejecución que aplica una pausa de 3 segundos si el ejecutable hijo colapsa en menos de 3 segundos.
- **Asignación Automática de Permisos**: Inclusión de `os.chmod(..., 0o755)` en entornos UNIX/Linux para garantizar permisos de ejecución antes del lanzamiento.

### Cambiado (Changed)

- **Mecanismo de Instancia Única**: Migración del mutex exclusivo de Windows (`kernel32.CreateMutexW`) a un socket loopback en puerto dedicado (`65434`), garantizando funcionamiento idéntico en Windows y Linux.
- **Tolerancia a Entornos sin Pantalla (Headless)**: Encapsulamiento del despliegue de alertas de `Tkinter` dentro de un bloque de captura de excepciones para evitar cierres inesperados por falta de servidor gráfico.

---

## [0.1.0] - 2026-07-10

### Añadido (Feat)

- Creación del launcher (Watchdog) para relanzar cliente.exe en Windows.
- Soporte Mutex con ctypes para control de instancia única del launcher compatible con Windows.
