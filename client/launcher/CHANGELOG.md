# CHANGELOG - Launcher

Todos los cambios notables en el launcher serán documentados en este archivo.
El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/)
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [0.3.1] - 2026-07-31

### Cambiado (Changed)

- Se eliminó el uso de `SO_REUSEADDR` en el mutex TCP del launcher para garantizar la exclusividad del puerto durante toda la ejecución.

### Corregido (Fixed)

- Corregida la prevención de múltiples instancias del launcher.
- Restaurado el comportamiento exclusivo del mutex TCP en Windows.
- Mejorada la fiabilidad del mecanismo de bloqueo del launcher sin afectar la supervisión del cliente.

---

## [0.3.0] - 2026-07-31

### Añadido (Added)

- **Supervisión basada en Mutex**: El launcher ahora determina el estado del cliente mediante la comprobación del mutex TCP, eliminando la dependencia del proceso hijo.
- **Inicialización Robusta del Cliente**: Se añadió una pausa de estabilización tras el lanzamiento del cliente para evitar condiciones de carrera durante la creación del mutex.
- **Directorio de Trabajo Consistente**: El cliente ahora se inicia utilizando el directorio base del launcher (`cwd=BASE_DIR`), garantizando el acceso correcto a recursos y archivos de configuración.

### Cambiado (Changed)

- **Arquitectura del Watchdog**: Simplificación completa del ciclo principal, reemplazando la supervisión mediante `subprocess.wait()` por un monitoreo periódico del mutex del cliente.
- **Gestión de Señales**: Simplificación del manejo de señales del launcher para realizar únicamente una finalización limpia del proceso, sin intervenir sobre el cliente.
- **Lógica de Supervisión**: El launcher ahora supervisa exclusivamente el estado real del cliente, independientemente de quién haya iniciado el proceso.

### Corregido (Fixed)

- Eliminado el riesgo de crear múltiples instancias del cliente al reiniciar manualmente el launcher.
- Corregido el bucle de relanzamiento provocado por la supervisión del proceso hijo mediante `wait()`.
- Mejorada la estabilidad del watchdog cuando el launcher es reiniciado mientras el cliente continúa en ejecución.
- Optimizado el consumo de CPU manteniendo un ciclo de supervisión basado en espera (`sleep`) y comprobaciones periódicas del mutex.

---

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
