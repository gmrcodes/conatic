# CHANGELOG - Servidor de Control de Terminales

Todos los cambios notables en este proyecto serán documentados en este archivo.
El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/)
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [0.4.2] - Redundancia codificación, puerto mutex y frecuencia de reloj

### Corregido (Fixed)

- **Error de tipo**: Se eliminó la llamada redundante `.encode('utf-8')` sobre retornos booleanos en los métodos de envío de acciones (desbloquear, pausar, mensajes, etc.) que causaban cierres inesperados (`AttributeError`).
- **Socket mutex**: Se añadió la llamada `.listen(1)` en el socket de bloqueo interno (`PUERTO_MUTEX_INTERNO = 65433`) para evitar multiples instancias.
- **Ajuste de reloj**: Se ajustó la frecuencia del bucle `motor_reloj_servidor` con `root.after(1000)` para evitar el descuento acelerado de segundos en pantalla.

### Cambiado / Limpiado (Changed & Removed)

- **Depuración de código muerto**: Eliminación de variables no utilizadas en la paleta de colores (`COLOR_DANGER`), desempaquetado de conexiones (`addr` sobrante en `accept()`) y cálculos inútiles de tiempo en sincronización offline (`ahora_db`).

---

## [0.4.1] - Estabilización de Hilos y Recubrimiento de Recursos

### Corregido (Fixed)

- **Sincronización Hilo-GUI**: Encapsulamiento de refrescos de la interfaz Tkinter mediante `root.after` para prevenir _race conditions_ al recibir datos por TCP.
- **Tolerancia a fallos en Recursos**: Manejo defensivo en `aplicar_icono_servidor` que evita que la falta del icono `.ico` o `.png` detenga la ejecución del servidor.
- **Liberación de locks SQLite**: Refactorización del context manager `with db_lock` en métodos de persistencia para reducir latencia entre hilos.

---

## [0.4.0] - Soporte Multiplataforma Nativo (Windows & Linux)

### Añadido (Added)

- **Mecanismo de Mutex por Socket**: Implementación de prevención de múltiples instancias mediante binding de socket loopback local en puerto `65433`, eliminando dependencias de `kernel32.dll` (`CreateMutexW`).
- **Almacenamiento de DB Dinámico**: Rutas de persistencia SQLite adaptativas según el SO (`%LOCALAPPDATA%/ControlServerApp` en Windows y `~/.local/share/controlserverapp` en Linux).
- **Carga dinámicas de recursos**: Función `resource_path()` para gestionar rutas de recursos compatibles con empaquetado binario PyInstaller (`sys._MEIPASS`).
- **Soporte de Ícono de Aplicación**: Asignación nativa de íconos `.ico` para Windows e íconos `.png` para distribuciones Linux/macOS.

### Cambiado (Changed)

- **Adaptación tipográfica**: Sustitución de fuenets propietarias ("Segoe UI") por la fuente simbólica del sistema `TkDefaultFont` para acoplarse al tema del usuario.

---

## [0.3.0] - Control Remoto de Terminales y Sincronización

### Añadido (Added)

- **Motor Cronómetro de Tiempo**: Implementación del bucle temporal en background para descuento de tiempo en vivo por terminal.
- **Protocolo de Control Remoto**: Comandos para bloqueo, desbloqueo manual, pausa, reanudación y envío de mensajes en pantalla hacia las terminales cliente.
- **Persistencia de Estado de Terminales**: Tabla `estado_terminales` y método `persistir_estado_terminal_db` para guardar en todo momento los minutos restantes de cada equipo.
- **Cálculo de Desconexión (Catch-up)**: Función `cargar_estado_terminales_db` que calcula los segundos transcurridos mientras el servidor estuvo apagado y descuenta el tiempo correspondiente automáticamente.

---

## [0.2.0] - Capa de Persistencia SQLite y Concurrencia

### Añadido (Added)

- **Base de Datos Centralizada**: Creación automática de la base de datos `sistema_central.db` con tablas `usuarios`, `historial_sesiones` y `estado_terminales`.
- **Sincronización de Hilos (Thread Safety)**: Incorporación de `threading.Lock()` (`db_lock`) para proteger las operaciones SQLite contra colisiones entre hilos de red y la GUI.
- **Soporte de Claves Foráneas**: Inclusión explícita de `PRAGMA foreign_keys = ON;` en SQLite.

---

## [0.1.0] - Servidor Core & Interfaz Gráfica Base

### Añadido (Added)

- **Servidor Socket TCP Multihilo**: Creación del listener de red principal en el puerto `65432` aceptando clientes concurrentes mediante `threading.Thread`.
- **Panel de Control UI**: Construcción de la interfaz gráfica principal con `Tkinter` / `ttk.Treeview` para visualizar la sala de terminales.
- **Manejo de Mensajes JSON**: Creación de la capa de serialización/deserialización para intercambio de paquetes estructurados.
