# PRUEBA 1: Evaluación Integral de Tecnologías Solares "PV vs CSP"

Este directorio contiene los notebooks y scripts utilizados para realizar un análisis comparativo entre las tecnologías solar fotovoltaica (PV) y de concentración (CSP) en diferentes ubicaciones geográficas (Chile, España, Australia). El análisis incluye el procesamiento del recurso solar, simulaciones de rendimiento técnico-económico con PySAM y la comparación de resultados clave como LCOE y generación anual.

## Contenido del Directorio

*   **`01_Analisis_Recurso_Solar.ipynb`**: Notebook para cargar, procesar y analizar los datos del recurso solar (GHI, DNI, DHI, Temperatura, etc.) desde archivos CSV (formato TMY/NSRDB). Realiza análisis estadísticos, detecta anomalías y genera gráficos mensuales y horarios de la irradiación para cada ubicación. También aplica correcciones específicas a los datos de Chile y Australia.
*   **`02_Simulacion_PV.ipynb`**: Notebook (actualmente no encontrado) destinado a definir y ejecutar funciones para simular el rendimiento de plantas fotovoltaicas (PV) utilizando PySAM. Probablemente calcula la generación de energía y el LCOE para diferentes capacidades de planta y condiciones. *(Nota: Este archivo no fue encontrado durante la última revisión).*
*   **`03_Simulacion_csp.ipynb`**: Notebook para definir y ejecutar funciones que simulan plantas de concentración solar de potencia (CSP) de torre central con almacenamiento en sales fundidas, usando PySAM. Realiza simulaciones variando las horas de almacenamiento y el múltiplo solar, calcula la generación anual y el LCOE, y ejecuta análisis de sensibilidad respecto al FCR.
*   **`04_Comparacion_PV_CSP.py`**: Script de Python que carga los resultados (archivos CSV) generados por los notebooks de simulación PV y CSP. Realiza cálculos adicionales (como el Factor de Capacidad) y genera una serie de gráficos comparativos estáticos entre ambas tecnologías.
*   **`dashboard/`**: Carpeta que contiene una aplicación Dash (`app.py`) para la visualización interactiva de simulaciones PV y CSP, comparaciones y análisis de recurso solar. Incluye:
    *   `app.py`: Script principal de la aplicación Dash.
    *   `simulation_logic.py`: Módulo con la lógica de simulación PV (probablemente extraída de `02_...`).
    *   `csp_simulation_logic.py`: Módulo con la lógica de simulación CSP (probablemente extraída de `03_...`).
    *   `requirements.txt`: Dependencias específicas para el dashboard.
*   **`Datos/`**: Carpeta que **debe contener** los archivos CSV con los datos del recurso solar para cada ubicación. Se esperan los archivos:
    *   `australia.csv`
    *   `chile.csv`
    *   `espana.csv`
*   **`Resultados/`**: Carpeta donde se guardarán los resultados numéricos de los análisis y simulaciones en formato CSV (generados por los notebooks/scripts, no por el dashboard).
*   **`graficos/`**: Carpeta que contiene subdirectorios donde se guardan los gráficos estáticos generados por los notebooks/scripts:
    *   `recurso_solar/`: Gráficos del análisis de recurso solar (de `01_...`).
    *   `simulacion_csp/`: Gráficos de la simulación CSP (de `03_...`).
    *   `simulacion_pv/`: (Esperado) Gráficos de la simulación PV (de `02_...`).
    *   `comparacion_pv_csp/`: Gráficos comparativos estáticos (de `04_...`).

## Prerrequisitos

Se requiere Python 3.8 para `02_Simulación_PV.ipynb`, 3.10 para `03_Simulacion_csp.ipynb` y las siguientes bibliotecas principales:

*   PySAM
*   pandas / polars (usado en `01_...`)
*   numpy
*   matplotlib
*   seaborn (usado en `01_...`)
*   ipython (para `display` en `01_...`)
*   **Para el Dashboard (`dashboard/`)**:
    *   dash
    *   plotly (generalmente instalado con dash)
    *   pvlib (para análisis de recurso)

Puedes instalarlas usando pip (polars es opcional si no usas `01_...` directamente):
```bash
pip install PySAM pandas polars numpy matplotlib seaborn ipython
```
Para el dashboard, navega a la carpeta `PRUEBA1/dashboard` e instala sus requisitos:
```bash
cd PRUEBA1/dashboard
pip install -r requirements.txt
pip install pvlib # Necesario para el análisis de recurso

*(Nota: La instalación de PySAM puede tener requisitos específicos. Consulta su documentación oficial).*

## Datos de Entrada

*   Los archivos CSV en `Datos/` deben contener datos horarios o sub-horarios del recurso solar (formato similar a NSRDB).
*   **Importante:** El script `01_Analisis_Recurso_Solar.ipynb` modifica el archivo `australia.csv` (cambiando 'Minute' a 30) y aplica correcciones de columnas a `chile.csv`. Ejecutar este notebook primero asegura que los datos estén en el formato esperado por las simulaciones posteriores. Los archivos originales en `Datos/` serán sobrescritos por `01_...` si se ejecuta.

## Ejecución

Tienes dos formas principales de interactuar con este proyecto:

**A. Flujo basado en Notebooks/Scripts (Análisis Detallado y Generación de Gráficos Estáticos):**

1.  **Análisis del Recurso (`01_Analisis_Recurso_Solar.ipynb`):** Ejecuta este notebook para procesar los datos y generar los primeros gráficos.
2.  **Simulación PV (`02_Simulacion_PV.ipynb`):** Ejecuta este notebook (si existe) para generar los resultados CSV de PV.
3.  **Simulación CSP (`03_Simulacion_csp.ipynb`):** Ejecuta este notebook, asegurándote de usar la lógica correcta para generar los resultados CSV de CSP.
4.  **Comparación Estática (`04_Comparacion_PV_CSP.py`):** Ejecuta este script (`python PRUEBA1/04_Comparacion_PV_CSP.py`) para generar los gráficos comparativos estáticos basados en los CSVs de los pasos anteriores.

**B. Dashboard Interactivo (Visualización y Simulación Rápida):**

1.  **Asegura los Datos:** Verifica que los archivos de datos en `Datos/` existan y estén correctamente formateados (se recomienda ejecutar `01_...` al menos una vez).
2.  **Navega al Directorio:** Abre una terminal y ve a `PRUEBA1/dashboard/`.
    ```bash
    cd PRUEBA1/dashboard
    ```
3.  **Instala Dependencias (si no lo has hecho):**
    ```bash
    pip install -r requirements.txt
    pip install pvlib
    ```
4.  **Ejecuta la Aplicación:**
    ```bash
    python app.py
    ```
5.  **Abre tu Navegador:** Accede a la URL proporcionada (ej. `http://127.0.0.1:8050/`).
6.  **Interactúa:** Selecciona países, ajusta parámetros y haz clic en "Ejecutar Simulación y Comparación" para ver los resultados interactivos. Usa la sección "Análisis del Recurso Solar" para explorar los datos TMY visualmente.

## Configuración

*   Las rutas a las carpetas `Datos/`, `Resultados/` y `graficos/` se definen generalmente al inicio de cada script/notebook. **Verifica y ajusta estas rutas** si es necesario.
*   Parámetros clave de simulación (costos, FCR, capacidades, horas de almacenamiento, etc.) se definen dentro de las funciones de configuración o celdas iniciales de los notebooks `02_...` y `03_...`.

## Salidas Principales

*   **Archivos CSV en `Resultados/`**: Contienen los datos numéricos detallados de cada simulación y análisis.
*   **Archivos PNG en `graficos/`**: Contienen las visualizaciones de los análisis de recurso, resultados de simulaciones individuales y las comparaciones entre PV y CSP.
*   **Dashboard Interactivo**: Proporciona visualizaciones dinámicas y comparaciones directamente en el navegador web.

## Consideraciones

*   **Dependencias:** Asegúrate de tener todas las bibliotecas necesarias instaladas.
*   **Tiempo de Ejecución:** Las simulaciones (especialmente CSP) pueden tardar un tiempo considerable.
*   **Archivo `02_Simulacion_PV.ipynb`:** La funcionalidad completa depende de la presencia y correcta ejecución de este notebook. 