# PRUEBA 1: Evaluación Integral de Tecnologías Solares "PV vs CSP"

Este directorio contiene los notebooks y scripts utilizados para realizar un análisis comparativo entre las tecnologías solar fotovoltaica (PV) y de concentración (CSP) en diferentes ubicaciones geográficas (Chile, España, Australia). El análisis incluye el procesamiento del recurso solar, simulaciones de rendimiento técnico-económico con PySAM y la comparación de resultados clave como LCOE y generación anual.

## Contenido del Directorio

*   **`01_Analisis_Recurso_Solar.ipynb`**: Notebook para cargar, procesar y analizar los datos del recurso solar (GHI, DNI, DHI, Temperatura, etc.) desde archivos CSV (formato TMY/NSRDB). Realiza análisis estadísticos, detecta anomalías y genera gráficos mensuales y horarios de la irradiación para cada ubicación. También aplica correcciones específicas a los datos de Chile y Australia.
*   **`02_Simulacion_PV.ipynb`**: Notebook (actualmente no encontrado) destinado a definir y ejecutar funciones para simular el rendimiento de plantas fotovoltaicas (PV) utilizando PySAM. Probablemente calcula la generación de energía y el LCOE para diferentes capacidades de planta y condiciones. *(Nota: Este archivo no fue encontrado durante la última revisión).*
*   **`03_Simulacion_csp.ipynb`**: Notebook para definir y ejecutar funciones que simulan plantas de concentración solar de potencia (CSP) de torre central con almacenamiento en sales fundidas, usando PySAM. Realiza simulaciones variando las horas de almacenamiento y el múltiplo solar, calcula la generación anual y el LCOE, y ejecuta análisis de sensibilidad respecto al FCR.
*   **`04_Comparacion_PV_CSP.py`**: Script de Python que carga los resultados (archivos CSV) generados por los notebooks de simulación PV y CSP. Realiza cálculos adicionales (como el Factor de Capacidad) y genera una serie de gráficos comparativos entre ambas tecnologías, analizando métricas como generación anual, LCOE y factor de capacidad bajo diferentes parámetros.
*   **`Datos/`**: Carpeta que **debe contener** los archivos CSV con los datos del recurso solar para cada ubicación. Se esperan los archivos:
    *   `australia.csv`
    *   `chile.csv`
    *   `espana.csv`
*   **`Resultados/`**: Carpeta donde se guardarán los resultados numéricos de los análisis y simulaciones en formato CSV.
*   **`graficos/`**: Carpeta que contiene subdirectorios donde se guardan los gráficos generados:
    *   `recurso_solar/`: Gráficos del análisis de recurso solar (de `01_...`).
    *   `simulacion_csp/`: Gráficos de la simulación CSP (de `03_...`).
    *   `simulacion_pv/`: (Esperado) Gráficos de la simulación PV (de `02_...`).
    *   `comparacion_pv_csp/`: Gráficos comparativos (de `04_...`).

## Prerrequisitos

Se requiere Python 3.8 para `02_Simulación_PV.ipynb`, 3.10 para `03_Simulacion_csp.ipynb` y las siguientes bibliotecas principales:

*   PySAM
*   pandas / polars (usado en `01_...`)
*   numpy
*   matplotlib
*   seaborn (usado en `01_...`)
*   ipython (para `display` en `01_...`)

Puedes instalarlas usando pip (polars es opcional si no usas `01_...` directamente):
```bash
pip install PySAM pandas polars numpy matplotlib seaborn ipython
```
*(Nota: La instalación de PySAM puede tener requisitos específicos. Consulta su documentación oficial).*

## Datos de Entrada

*   Los archivos CSV en `Datos/` deben contener datos horarios o sub-horarios del recurso solar (formato similar a NSRDB).
*   **Importante:** El script `01_Analisis_Recurso_Solar.ipynb` modifica el archivo `australia.csv` (cambiando 'Minute' a 30) y aplica correcciones de columnas a `chile.csv`. Ejecutar este notebook primero asegura que los datos estén en el formato esperado por las simulaciones posteriores. Los archivos originales en `Datos/` serán sobrescritos por `01_...` si se ejecuta.

## Ejecución (Flujo Sugerido)

1.  **Análisis del Recurso (`01_Analisis_Recurso_Solar.ipynb`):**
    *   Abre y ejecuta este notebook en un entorno Jupyter.
    *   Verifica que las rutas en la primera celda de código sean correctas.
    *   Su ejecución procesará los CSV en `Datos/`, generará gráficos en `graficos/recurso_solar/` y un resumen en `Resultados/analisis_estadistico_recurso_solar.txt`.
2.  **Simulación PV (`02_Simulacion_PV.ipynb`):**
    *   Abre y ejecuta este notebook (si lo encuentras o restauras).
    *   Asegúrate de que las rutas y parámetros de simulación estén correctamente configurados.
    *   Generará resultados PV en formato CSV en `Resultados/`.
3.  **Simulación CSP (`03_Simulacion_csp.ipynb`):**
    *   Abre y ejecuta este notebook en un entorno Jupyter.
    *   **Consideración Crítica:** Revisa las definiciones duplicadas de `ejecutar_simulacion_principal` y asegúrate de que la versión final (que calcula LCOE y retorna `resultados_main`) sea la que efectivamente se usa para generar los DataFrames finales (`resultados_simulacion_csp_multi.csv`, etc.) necesarios para el script de comparación. Comentar o eliminar la definición anterior es lo más seguro.
    *   Generará resultados CSP en CSV en `Resultados/` y gráficos en `graficos/simulacion_csp/`.
4.  **Comparación PV vs CSP (`04_Comparacion_PV_CSP.py`):**
    *   Abre una terminal.
    *   Navega hasta el directorio que contiene la carpeta `PRUEBA1`.
    *   Ejecuta el script:
        ```bash
        python PRUEBA1/04_Comparacion_PV_CSP.py
        ```
    *   Este script leerá los archivos CSV de `Resultados/` (generados en los pasos 2 y 3) y creará los gráficos comparativos en `graficos/comparacion_pv_csp/`. Asegúrate de que los nombres de archivo CSV que busca el script coincidan con los generados por los notebooks.

## Configuración

*   Las rutas a las carpetas `Datos/`, `Resultados/` y `graficos/` se definen generalmente al inicio de cada script/notebook. **Verifica y ajusta estas rutas** si es necesario.
*   Parámetros clave de simulación (costos, FCR, capacidades, horas de almacenamiento, etc.) se definen dentro de las funciones de configuración o celdas iniciales de los notebooks `02_...` y `03_...`.

## Salidas Principales

*   **Archivos CSV en `Resultados/`**: Contienen los datos numéricos detallados de cada simulación y análisis.
*   **Archivos PNG en `graficos/`**: Contienen las visualizaciones de los análisis de recurso, resultados de simulaciones individuales y las comparaciones entre PV y CSP.

## Consideraciones

*   **Dependencias:** Asegúrate de tener todas las bibliotecas necesarias instaladas.
*   **Orden de Ejecución:** Es recomendable seguir el orden sugerido (01 -> 02 -> 03 -> 04) para asegurar que los datos de entrada para cada paso estén disponibles y procesados correctamente.
*   **Tiempo de Ejecución:** Las simulaciones (especialmente CSP) pueden tardar un tiempo considerable.
*   **Archivo `02_Simulacion_PV.ipynb`:** La funcionalidad completa depende de la presencia y correcta ejecución de este notebook. 