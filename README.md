# 🧬 Selección Natural - Simulación con Simple Random Walk (SRW)

Simulación interactiva de selección natural usando Simple Random Walk con depredadores y mutaciones evolutivas.

## 📋 Descripción

Este proyecto simula el proceso de **selección natural** donde partículas se mueven aleatoriamente (Random Walk), buscando comida en un ambiente delimitado. Solo aquellas partículas que encuentran comida y regresan a casa sobreviven y se reproducen, transmitiendo sus mutaciones a la siguiente generación.

### 🎯 Características Principales

- 🎮 **Interfaz interactiva** con Pygame
- 📊 **Visualización de datos** con gráficas y tablas (Matplotlib)
- 🧪 **Sistema de mutaciones** (velocidad y prioridad alimenticia)
- 🦅 **Depredadores** que eliminan partículas periódicamente
- ⚡ **Sistema de stamina** y consumo de energía
- 📈 **Análisis estadístico completo** día a día

## 💻 Requisitos Previos

- 🐍 Python 3.7 o superior
- 📦 Git

## 🚀 Instalación y Ejecución

### Opción 1: Clonar el Repositorio

```bash
git clone https://github.com/GabrielCevallos/SeleccionNatural.git
cd SeleccionNatural
```

### Opción 2: Descargar Directamente

Descarga los archivos directamente del repositorio.

### 🔧 Crear un Entorno Virtual

**En Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**En macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 📦 Instalar Dependencias

```bash
pip install pygame matplotlib
```

### ▶️ Ejecutar la Simulación

```bash
python SRW_Natural_Selection.py
```

## 🎮 Uso

### 🛠️ Pantalla de Configuración

Al ejecutar el programa, aparecerá un menú donde se puede configurar:

- **📅 Número de días**: Duración total de la simulación (1-9999 días)
- **⏱️ Duración del día (pasos)**: Número de pasos por día (debe ser mayor que los pasos por vida)
- **👥 Partículas iniciales**: Número de partículas al inicio (1-500)
- **🍎 % de comida en mapa**: Porcentaje del área con comida disponible (1-100%)
- **💪 Pasos por vida**: Energía máxima de cada partícula (1-9999)
- **🦅 Depredadores por purga**: Número de depredadores por día de purga (0-50)
- **🔄 Frecuencia de purga**: Cada cuántos días aparecen depredadores (0 = nunca)

Presionar **INICIAR** para comenzar la simulación o **SALIR** para cerrar.

### 🎯 Durante la Simulación

**⌨️ Controles:**
- **ESPACIO** o botón **PAUSA**: Pausa/reanuda la simulación
- **T**: Muestra/oculta las trayectorias de las partículas
- **RESET**: Reinicia la simulación con los mismos parámetros
- **MENU**: Vuelve a la pantalla de configuración
- **🎚️ Barra deslizante**: Ajusta la velocidad de la simulación (5-120 FPS)

**📊 Panel de estadísticas (lado derecho):**
- Partículas vivas y en casa
- Cantidad de partículas que comieron hoy
- Pueden reproducirse
- Desglose por tipo de mutación (Normales, Verdes, Rojos)
- Número de depredadores activos

## ✨ Características de la Simulación

### 🎲 Mecánicas de Juego

- **🚶 Simple Random Walk**: Cada partícula se mueve aleatoriamente (arriba, abajo, izquierda, derecha)
- **⚡ Sistema de Stamina**: Las partículas consumen energía al moverse
- **🍎 Búsqueda de Comida**: Deben encontrar comida para recuperar energía
- **🏠 Retorno a Casa**: DEBEN regresar a casa para sobrevivir y reproducirse
- **🧬 Reproducción Selectiva**: Los sobrevivientes se reproducen, heredando mutaciones
- **🦅 Depredadores**: Eliminan partículas periódicamente según configuración

### 🧬 Tres Tipos de Mutaciones

1. **⚪ Normales** (Blanco/Dorado): Sin mutaciones especiales
2. **🟢 Mutación Velocidad** (Verde): 2x velocidad de movimiento
3. **🔴 Mutación Prioridad** (Rojo): 2x vida máxima + **prioridad ALTA** para comida

**🍽️ Sistema de Prioridad Alimenticia:**
Cuando múltiples partículas compiten por la misma comida:
1. 🔴 **Rojos** tienen prioridad ALTA (comen primero)
2. 🟢 **Verdes** tienen prioridad MEDIA
3. ⚪ **Normales** tienen prioridad BAJA

### 🎨 Visualización

- 🖼️ Simulación visual en tiempo real con Pygame
- 🎨 Partículas de colores según su tipo de mutación
- 🟢 Círculo verde alrededor de partículas en casa
- 📐 Cuadrícula para referencia espacial
- ❌ Animaciones de muerte (cruz roja) para partículas eliminadas
- 📏 Barras de stamina sobre cada partícula
- 🔴 Área de visión de depredadores
- 🌈 Trayectorias opcionales para seguimiento de movimiento

### 📊 Análisis de Datos

Al finalizar la simulación, se pueden visualizar:

**📈 Gráficas Interactivas:**
- 📉 Evolución total de la población por día
- 🧬 Desglose de población por tipo de mutación
- 🦅 Impacto de depredadores (partículas eliminadas)
- 📊 Comparación de tipos eliminados por depredadores

**📋 Tablas Detalladas (ventanas separadas):**

1. **Histórico**: Datos día a día
   - Población total
   - Partículas en casa y que comieron
   - Pueden reproducirse
   - Desglose por mutación (Normales, Verdes, Rojos)
   - Depredadores activos

2. **Impacto de Depredadores**: 
   - Día de purga
   - Total eliminadas
   - Desglose por tipo de mutación

3. **Resumen de Simulación**:
   - Población inicial, final, máxima y mínima
   - Días de purga totales
   - Parámetros de configuración usados

## 🔧 Parámetros por Defecto

Estos valores se cargan inicialmente (modificables en configuración):

- 📅 Número de días: **30**
- ⏱️ Duración del día: **300 pasos**
- 👥 Partículas iniciales: **50**
- 🍎 Porcentaje de comida: **20%**
- 💪 Pasos por vida: **100**
- 🦅 Depredadores por purga: **5**
- 🔄 Frecuencia de purga: **10 días**
- ⚡ Velocidad: **30 FPS**

## 🛑 Desactivar el Entorno Virtual

Cuando se termine de usar el proyecto:

```bash
deactivate
```

## 👨‍💻 Autores

- **Gabriel Cevallos** - [@GabrielCevallos](https://github.com/GabrielCevallos)
- **Francisco Jaramillo** - [@FrancisJaramilloC](https://github.com/FrancisJaramilloC)
- **Iván Fernández** - [@IvanFernandez02](https://github.com/IvanFernandez02)
- **José Riofrío** - [@JOSERiofrio2002](https://github.com/JOSERiofrio2002)

## 📝 Licencia

Este proyecto es de código abierto y está disponible para uso educativo.

---

🧬 **¡Explora la selección natural en acción!** 🎮