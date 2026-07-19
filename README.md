# Sistema de Control de Tiempos y Bloqueo de Terminales

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![License](https://img.shields.io/badge/License-GPLv3-blue.svg)

Una solución robusta de arquitectura Cliente-Servidor diseñada para gestionar sesiones de usuarios, realizar el seguimiento del tiempo de uso en terminales y ejecutar bloqueos remotos o automáticos de sistemas. Ideal para entornos empresariales o laboratorios de cómputo compartidos.

## 📸 Capturas de Pantalla

| Panel del Servidor (Monitoreo) | Interfaz de Cliente (Terminal Bloqueada) |
|---|---|
| <img src="media/screenshot_server.png" width="400" alt="Servidor Panel"/> | <img src="media/screenshot_client.png" width="400" alt="Cliente Bloqueado"/> |

*Nota: Reemplaza las imágenes en la carpeta `media/` con tus propias capturas reales del sistema en funcionamiento.*

---

## ✨ Características Principales

### 🖥️ Módulo Servidor
- **Monitoreo en Tiempo Real:** Visualización del estado de todos los terminales clientes conectados.
- **Gestión de Sesiones:** Control y asignación de tiempos de uso por usuario o terminal.
- **Persistencia de Datos:** Arquitectura respaldada por base de datos para auditorías e historiales de uso.

### 💻 Módulo Cliente
- **Bloqueo Seguro de Pantalla:** Interfaz de bloqueo persistente que impide el uso del sistema sin autorización.
- **Sincronización Fuera de Línea:** Capacidad de mantener el control del tiempo incluso ante desconexiones temporales de la red.
- **Ligero y Autónomo:** Diseñado para empaquetarse como ejecutable independiente.

---

## 🛠️ Arquitectura del Proyecto

El proyecto está dividido estrictamente en dos componentes independientes para facilitar su despliegue:

```text
├── client/          # Aplicación que se ejecuta en las terminales a controlar.
└── server/          # Panel central de administración y base de datos.
```

---

## 🚀 Instrucciones de Instalación y Despliegue

### Requisitos Previos
- Python 3.10 o superior instalado.
- Servidor de Base de Datos (MySQL / MariaDB).

### 1. Configuración del Servidor
Navega a la carpeta del servidor e instala las dependencias necesarias:
```bash
cd server
pip install -r requirements.txt
```
1. Configura los parámetros de conexión a la base de datos en el archivo de configuración correspondiente.
2. Ejecuta el script de inicialización de la base de datos ubicado en `database/`.
3. Inicia el panel de control:
```bash
python src/main.py
```

### 2. Configuración del Cliente
Navega a la carpeta del cliente e instala sus requerimientos:
```bash
cd ../client
pip install -r requirements.txt
```
Para probar el cliente en modo de desarrollo, ejecuta:
```bash
python src/main.py
```

---

## 📦 Compilación para Producción (Opcional)

Si deseas generar los archivos ejecutables (`.exe` o binarios nativos) para su distribución formal sin necesidad de instalar Python en los clientes, puedes utilizar **PyInstaller**:

```bash
cd client
pyinstaller --noconfirm --onedir --windowed src/main.py
```
*Los binarios finales se generarán de manera automática en la carpeta `dist/`.*

---

## 📄 Licencia

Este proyecto está bajo la licencia **GNU GPLv3**. Esto significa que el software es de código abierto y cualquiera puede modificarlo o redistribuirlo, siempre y cuando las versiones modificadas mantengan la misma licencia de código abierto. Consulta el archivo [LICENSE](LICENSE) para más detalles.
