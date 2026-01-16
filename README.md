# Selección Natural - Simulación con Simple Random Walk (SRW)

Simulación interactiva de selección natural usando Simple Random Walk.

## Descripción

Este proyecto simula el proceso de selección natural donde partículas se muevn aleatoriamente, buscando comida en un ambiente delimitado. Solo aquellas partículas que encuentran comida y regresan a casa, sobreviven y se reproducen, permitiendo observar la evolución de características hereditarias como velocidad mejorada y prioridad para acceder a la comida.

## Requisitos Previos

- Python 3.7 o superior
- Git

## Instalación y Ejecución

### Opción 1: Clonar el Repositorio

```bash
git clone https://github.com/GabrielCevallos/SeleccionNatural.git
cd SeleccionNatural
```

### Opción 2: Descargar Directamente

Descarga los archivos directamente del repositorio.

### Crear un Entorno Virtual

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

### Instalar Dependencias

```bash
pip install pygame matplotlib
```

### Ejecutar la Simulación

```bash
python SRW_Natural_Selection.py
```

## Uso

### Pantalla de Configuración

Al ejecutar el programa, aparecerá un menú donde se puede configurar:

- **Número de días**: Duración total de la simulación (1-9999 días)
- **Duración del día (pasos)**: Número de pasos por día para que las partículas se muevan (debe ser mayor que los pasos por vida)
- **Partículas iniciales**: Número de partículas que comenzarán la simulación
- **% de comida en mapa**: Porcentaje del área que contendrá comida disponible (1-100%)
- **Pasos por vida**: Número máximo de pasos que cada partícula puede dar antes de agotarse (1-9999)

Presionar **INICIAR** para comenzar la simulación o **SALIR** para cerrar.

### Durante la Simulación

**Controles:**
- **ESPACIO** o botón **PAUSA**: Pausa/reanuda la simulación
- **T**: Muestra/oculta las trayectorias de las partículas
- **RESET**: Reinicia la simulación con los mismos parámetros
- **MENU**: Vuelve a la pantalla de configuración
- **Barra deslizante**: Ajusta la velocidad de la simulación (5-120 FPS)

**Panel de estadísticas (lado derecho):**
- Partículas vivas y en casa
- Cantidad de partículas que comieron hoy
- Desglose por tipo de mutación (Normales, Rojos, Verdes)

## Características

### Mecánicas de la Simulación

- **Simple Random Walk**: Cada partícula se mueve aleatoriamente (arriba, abajo, izquierda, derecha)
- **Sistema de Supervivencia**: Las partículas **deben** encontrar comida Y regresar a casa para sobrevivir
- **Reproducción Selectiva**: Los sobrevivientes se reproducen, transmitiendo sus características a la siguiente generación
- **Tres Tipos de Mutaciones**:
  - **Normales** (Blanco): Sin mutaciones
  - **Mutación Velocidad** (Rojo): 50% más veloces que sus padres
  - **Mutación Prioridad** (Verde): Tienen prioridad para acceder a la comida cuando compiten con otras partículas
  
### Visualización

- Simulación visual en tiempo real con Pygame
- Partículas de colores según su tipo de mutación
- Círculo verde alrededor de partículas en casa
- Cuadrícula para referencia espacial
- Animaciones de muerte (cruz roja) para partículas que no sobreviven
- Trayectorias opcionales para seguimiento de movimiento

### Análisis de Datos

- Gráficas interactivas con Matplotlib
- Evolución total de la población por día
- Desglose de población por tipo de mutación
- Estadísticas finales (población inicial, final, máxima y mínima)

## Desactivar el Entorno Virtual

Cuando se termine de usar el proyecto:

```bash
deactivate
```

## Parámetros por Defecto

Estos valores se pueden modificar en la pantalla de configuración:

- Número de días: 30
- Duración del día: 300 pasos
- Partículas iniciales: 50
- Porcentaje de comida: 20%
- Pasos por vida: 100
- Velocidad: 30 FPS