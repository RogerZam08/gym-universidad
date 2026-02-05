# gym-universidad
# 🏋️ Sistema de Control de Acceso - Gimnasio Universitario

**Autor:** Roger Zambrano  
**Versión:** 1.0.0

## 📄 Descripción
Este proyecto es una solución digital desarrollada para optimizar el proceso de registro de asistencia en el gimnasio de la universidad. Reemplaza el antiguo registro en papel por una interfaz web rápida e intuitiva.

El sistema utiliza una arquitectura híbrida para garantizar que el servicio esté disponible 24/7 sin depender de servidores locales propensos a fallos eléctricos.

## 🚀 Características Principales
* **Check-in Rápido:** Los usuarios registrados ingresan solo con su cédula.
* **Base de Datos Unificada:** Si el usuario ya existe, el sistema autocompleta sus datos.
* **Validación Institucional:** Verifica que los correos pertenezcan al dominio de la universidad.
* **Registro en la Nube:** Todos los datos se sincronizan en tiempo real con Google Sheets, permitiendo a los profesores acceder a reportes instantáneos.
* **Alta Disponibilidad:** Alojado en la nube (Streamlit Cloud), accesible desde cualquier dispositivo móvil o PC.

## 🛠️ Tecnologías Usadas
* **Python:** Lógica del backend.
* **Streamlit:** Interfaz gráfica frontend.
* **Google Sheets API:** Base de datos y almacenamiento de registros.
* **Pandas:** Procesamiento de datos.

## 🔒 Privacidad
Este sistema no almacena datos localmente. Toda la información reside en los servidores seguros de Google (Google Drive) y el acceso a la base de datos es restringido exclusivamente al personal docente autorizado.

---
© 2026 Roger Zambrano. Todos los derechos reservados.
Desarrollado como iniciativa estudiantil para la modernización de servicios universitarios.
