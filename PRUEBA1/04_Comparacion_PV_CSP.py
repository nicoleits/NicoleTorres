import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
import matplotlib.ticker as mticker

# # Comparación de Resultados PV y CSP

# ## 1. Configuración de Rutas
# Directorio donde se encuentran los resultados CSV
# results_dir = "/home/nicole/proyecto/NicoleTorres/PRUEBA1/Resultados"
# Directorio donde guardar los gráficos de comparación (puedes crear uno nuevo o usar existente)
# graphs_comp_dir = "/home/nicole/proyecto/NicoleTorres/PRUEBA1/graficos/comparacion_pv_csp"

# Obtener la ruta del directorio donde se encuentra este script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Construir rutas relativas al directorio del script
results_dir = os.path.join(script_dir, "Resultados")
graphs_comp_dir = os.path.join(script_dir, "graficos", "comparacion_pv_csp")

os.makedirs(graphs_comp_dir, exist_ok=True)

# Nombres de los archivos CSV relevantes (verifica si existen)
csv_csp_main = os.path.join(results_dir, "resultados_simulacion_csp_multi.csv")
csv_pv_energia_cap = os.path.join(results_dir, "resultados_pv_energia_vs_capacidad.csv")
# Añade aquí los nombres de otros archivos CSV de PV si los encuentras/generas
# csv_pv_lcoe_fcr = os.path.join(results_dir, "resultados_pv_lcoe_vs_fcr_1000kW.csv") # Ejemplo
# csv_pv_sens_tilt = os.path.join(results_dir, "resultados_pv_sensibilidad_tilt_1000kW.csv") # Ejemplo

print(f"Directorio de resultados: {results_dir}")
print(f"Directorio de gráficos de comparación: {graphs_comp_dir}")


# ## 2. Carga de Datos

# --- Carga de datos CSP desde archivos individuales --- MODIFICADO
print("\nCargando datos CSP desde archivos individuales (resultados_<pais>.csv)...")
df_csp_list = []
paises_info = [
    {"nombre": "Australia", "sufijo": "australia"},
    {"nombre": "Chile", "sufijo": "chile"},
    {"nombre": "Espana", "sufijo": "espana"}
]

for pais_data in paises_info:
    pais_nombre = pais_data["nombre"]
    pais_sufijo = pais_data["sufijo"]
    csv_csp_individual = os.path.join(results_dir, f"resultados_{pais_sufijo}.csv")
    try:
        df_temp = pd.read_csv(csv_csp_individual)
        # Asegurarse de que la columna 'Pais' exista o añadirla
        if 'Pais' not in df_temp.columns:
            df_temp['Pais'] = pais_nombre
        print(f"  Cargado: {csv_csp_individual} ({len(df_temp)} filas)")
        df_csp_list.append(df_temp)
    except FileNotFoundError:
        print(f"  ERROR: Archivo no encontrado - {csv_csp_individual}. Saltando este país para CSP.")
    except Exception as e:
        print(f"  ERROR al cargar {csv_csp_individual}: {e}. Saltando este país para CSP.")

# Combinar los dataframes individuales en uno solo
if df_csp_list:
    df_csp_main = pd.concat(df_csp_list, ignore_index=True)
    print("Datos CSP combinados desde archivos individuales.")
    # Verificar columnas cargadas
    print(f"  Columnas en df_csp_main: {df_csp_main.columns.tolist()}")
else:
    print("ERROR: No se pudieron cargar datos CSP desde ningún archivo individual.")
    df_csp_main = pd.DataFrame() # Asegurar que sea un DF vacío si falla la carga

# --- FIN Carga CSP Modificada ---

# # Cargar datos principales de CSP (CÓDIGO ORIGINAL - COMENTADO)
# df_csp_main = pd.DataFrame() # Inicializar vacío
# csv_csp_main = os.path.join(results_dir, "resultados_simulacion_csp_multi.csv") # Archivo combinado original
# try:
#     df_csp_main = pd.read_csv(csv_csp_main)
#     print(f"\nCargado: {csv_csp_main}")
#     # print(df_csp_main.head()) # Descomenta para ver las primeras filas
# except FileNotFoundError:
#     print(f"\nERROR: Archivo no encontrado - {csv_csp_main}")

# Calcular CF para CSP (vs Storage)
CSP_NOMINAL_CAPACITY_KW = 100000 # Asunción: Capacidad nominal del bloque de potencia CSP en kW (e.g., 100 MW)
if not df_csp_main.empty and 'Generacion_energia_kWh' in df_csp_main.columns:
    df_csp_main['CF_CSP'] = df_csp_main['Generacion_energia_kWh'] / (CSP_NOMINAL_CAPACITY_KW * 8760)
    print("  Columna 'CF_CSP' calculada y añadida a df_csp_main (asumiendo %.0f kW nominal)." % CSP_NOMINAL_CAPACITY_KW)
else:
    print("  Advertencia: No se pudo calcular CF_CSP (faltan datos o columnas en df_csp_main).")

# Cargar datos de Energía vs Capacidad de PV
df_pv_energia_cap = pd.DataFrame() # Inicializar vacío
try:
    df_pv_energia_cap = pd.read_csv(csv_pv_energia_cap)
    print(f"Cargado: {csv_pv_energia_cap}")
    # print(df_pv_energia_cap.head()) # Descomenta para ver las primeras filas
except FileNotFoundError:
    print(f"ERROR: Archivo no encontrado - {csv_pv_energia_cap}")

# Calcular CF para PV
if not df_pv_energia_cap.empty and 'capacidad_kw' in df_pv_energia_cap.columns and 'energia_kwh' in df_pv_energia_cap.columns:
    # Evitar división por cero si alguna capacidad es 0
    df_pv_energia_cap_safe = df_pv_energia_cap[df_pv_energia_cap['capacidad_kw'] > 0].copy()
    df_pv_energia_cap_safe['CF_PV'] = df_pv_energia_cap_safe['energia_kwh'] / (df_pv_energia_cap_safe['capacidad_kw'] * 8760)
    # Fusionar de nuevo si es necesario o trabajar con df_pv_energia_cap_safe
    df_pv_energia_cap = pd.merge(df_pv_energia_cap, df_pv_energia_cap_safe[['CF_PV']], left_index=True, right_index=True, how='left')
    print("  Columna 'CF_PV' calculada y añadida a df_pv_energia_cap.")
else:
    print("  Advertencia: No se pudo calcular CF_PV (faltan datos o columnas en df_pv_energia_cap).")

# Cargar otros DataFrames de PV o CSP según sea necesario para la comparación deseada
# Ejemplo:
# df_pv_lcoe_fcr = pd.DataFrame() # Inicializar vacío
# try:
#     df_pv_lcoe_fcr = pd.read_csv(csv_pv_lcoe_fcr)
#     print(f"Cargado: {csv_pv_lcoe_fcr}")
# except FileNotFoundError:
#     print(f"ERROR: Archivo no encontrado - {csv_pv_lcoe_fcr}")

# Define path for PV LCOE data
csv_pv_lcoe_fcr = os.path.join(results_dir, "resultados_pv_lcoe_vs_fcr_1000kW.csv")

# Load PV LCOE data
df_pv_lcoe_fcr = pd.DataFrame() # Initialize empty
try:
    df_pv_lcoe_fcr = pd.read_csv(csv_pv_lcoe_fcr)
    print(f"Cargado: {csv_pv_lcoe_fcr}")
    # print(df_pv_lcoe_fcr.head()) # Uncomment to view first rows
except FileNotFoundError:
    print(f"ERROR: Archivo no encontrado - {csv_pv_lcoe_fcr}")

# Define path for CSP varying Solar Multiple data
csv_csp_variando_solarm = os.path.join(results_dir, "resultados_simulacion_csp_variando_solarm.csv")

# Load CSP varying Solar Multiple data
df_csp_variando_solarm = pd.DataFrame() # Initialize empty
try:
    df_csp_variando_solarm = pd.read_csv(csv_csp_variando_solarm)
    print(f"Cargado: {csv_csp_variando_solarm}")
    # print(df_csp_variando_solarm.head()) # Uncomment to view first rows
except FileNotFoundError:
    print(f"ERROR: Archivo no encontrado - {csv_csp_variando_solarm}")

# Calcular CF para CSP (vs Solar Multiple)
if not df_csp_variando_solarm.empty and 'Generacion_energia_kWh' in df_csp_variando_solarm.columns:
    df_csp_variando_solarm['CF_CSP'] = df_csp_variando_solarm['Generacion_energia_kWh'] / (CSP_NOMINAL_CAPACITY_KW * 8760)
    print("  Columna 'CF_CSP' calculada y añadida a df_csp_variando_solarm (asumiendo %.0f kW nominal)." % CSP_NOMINAL_CAPACITY_KW)
else:
     print("  Advertencia: No se pudo calcular CF_CSP (faltan datos o columnas en df_csp_variando_solarm).")


# ## 3. Comparación de Generación Anual (Ejemplo Inicial)

# Podemos comparar la generación para una capacidad PV específica vs. diferentes horas de almacenamiento CSP
# O mostrar rangos.

# Ejemplo: Comparar la generación de PV para 10 MW con la generación de CSP (para Chile)

capacidad_pv_comparar = 10000 # kW (Planta 10 MW)
pais_comparar = "Chile" # Asegúrate que el nombre coincida (mayúsculas/minúsculas)

if not df_pv_energia_cap.empty and not df_csp_main.empty:
    # Filtrar datos PV
    energia_pv_series = df_pv_energia_cap[
        (df_pv_energia_cap['pais'] == pais_comparar) &
        (df_pv_energia_cap['capacidad_kw'] == capacidad_pv_comparar)
    ]['energia_kwh']

    # Filtrar datos CSP para el mismo país
    df_csp_pais = df_csp_main[df_csp_main['Pais'] == pais_comparar]

    if not energia_pv_series.empty and not df_csp_pais.empty:
        energia_pv_valor = energia_pv_series.iloc[0]

        plt.figure(figsize=(10, 6))
        # Graficar CSP
        plt.plot(df_csp_pais['Horas_almacenamiento'], df_csp_pais['Generacion_energia_kWh'], marker='o', linestyle='-', label=f'CSP ({pais_comparar})')
        # Añadir línea horizontal para PV
        plt.axhline(energia_pv_valor, color='red', linestyle='--', label=f'PV {capacidad_pv_comparar/1000} MW ({pais_comparar})')

        plt.xlabel("Horas de Almacenamiento (CSP)")
        plt.ylabel("Generación Anual (kWh)")
        plt.title(f"Comparación Generación Anual: CSP vs PV ({pais_comparar})")
        plt.legend()
        plt.grid(True, linestyle='--')
        plt.ticklabel_format(style='sci', axis='y', scilimits=(0,0))
        plt.tight_layout()

        # Guardar gráfico
        graph_filename = f"comparacion_generacion_csp_vs_pv_{pais_comparar}.png"
        graph_filepath = os.path.join(graphs_comp_dir, graph_filename)
        # >>> INICIO MODIFICACIÓN: Comentar guardado de gráfico individual <<<
        # plt.savefig(graph_filepath)
        # print(f"\nGráfico de comparación de generación guardado en: {graph_filepath}")
        print(f"\nGráfico de comparación de generación para {pais_comparar} NO guardado (código comentado).")
        # <<< FIN MODIFICACIÓN >>>
        # plt.show() # Descomentar si quieres que se muestre el gráfico
        plt.close()

    else:
        if energia_pv_series.empty:
             print(f"\nNo se encontraron datos de PV para {pais_comparar} con capacidad {capacidad_pv_comparar} kW.")
        if df_csp_pais.empty:
             print(f"\nNo se encontraron datos de CSP para {pais_comparar}.")

else:
    print("\nNo se pudieron cargar los DataFrames necesarios o están vacíos para la comparación de generación.")


# ## 4. Comparación de LCOE (Pendiente - Necesita datos LCOE de PV)

# Comparar el LCOE mínimo encontrado para cada tecnología por país.

if not df_csp_main.empty and not df_pv_lcoe_fcr.empty:

    # Asegurarse que las columnas de país y LCOE existen y tienen nombres consistentes
    # (Ajustar nombres si es necesario basado en los CSV reales)
    csp_country_col = 'Pais'
    csp_lcoe_col = 'LCOE_$/kWh'
    pv_country_col = 'pais'
    pv_lcoe_col = 'lcoe_$/kwh' # Asumiendo este nombre basado en scripts anteriores

    if csp_country_col not in df_csp_main.columns:
        print(f"ERROR: La columna '{csp_country_col}' no se encuentra en df_csp_main.")
    elif csp_lcoe_col not in df_csp_main.columns:
         print(f"ERROR: La columna '{csp_lcoe_col}' no se encuentra en df_csp_main.")
    elif pv_country_col not in df_pv_lcoe_fcr.columns:
         print(f"ERROR: La columna '{pv_country_col}' no se encuentra en df_pv_lcoe_fcr.")
    elif pv_lcoe_col not in df_pv_lcoe_fcr.columns:
         print(f"ERROR: La columna '{pv_lcoe_col}' no se encuentra en df_pv_lcoe_fcr.")
    else:
        # Encontrar LCOE mínimo para CSP por país
        min_lcoe_csp = df_csp_main.loc[df_csp_main.groupby(csp_country_col)[csp_lcoe_col].idxmin()]
        min_lcoe_csp = min_lcoe_csp[[csp_country_col, csp_lcoe_col]].rename(
            columns={csp_country_col: 'Pais', csp_lcoe_col: 'LCOE_CSP_min'}
        )

        # Encontrar LCOE mínimo para PV por país (asumiendo que df_pv_lcoe_fcr contiene resultados para 1000kW)
        min_lcoe_pv = df_pv_lcoe_fcr.loc[df_pv_lcoe_fcr.groupby(pv_country_col)[pv_lcoe_col].idxmin()]
        min_lcoe_pv = min_lcoe_pv[[pv_country_col, pv_lcoe_col]].rename(
            columns={pv_country_col: 'Pais', pv_lcoe_col: 'LCOE_PV_min'}
        )

        # Fusionar los dataframes de LCOE mínimo
        df_lcoe_comp = pd.merge(min_lcoe_csp, min_lcoe_pv, on='Pais', how='outer') # Use outer merge to keep all countries

        print("\nTabla comparativa de LCOE mínimo ($/kWh) por país:")
        print(df_lcoe_comp)

        # Crear gráfico de barras comparando LCOE mínimo
        if not df_lcoe_comp.empty:
            n_countries = len(df_lcoe_comp)
            index = np.arange(n_countries)
            bar_width = 0.35

            fig, ax = plt.subplots(figsize=(12, 7))
            bar1 = ax.bar(index - bar_width/2, df_lcoe_comp['LCOE_CSP_min'].fillna(0), bar_width, label='CSP Min LCOE') # Fill NaN for plotting
            bar2 = ax.bar(index + bar_width/2, df_lcoe_comp['LCOE_PV_min'].fillna(0), bar_width, label='PV Min LCOE (1MW)') # Fill NaN for plotting

            ax.set_xlabel('País')
            ax.set_ylabel('LCOE Mínimo ($/kWh)')
            ax.set_title('Comparación LCOE Mínimo por País: CSP vs PV (1MW)')
            ax.set_xticks(index)
            ax.set_xticklabels(df_lcoe_comp['Pais'], rotation=45, ha="right")
            ax.legend()
            ax.grid(True, axis='y', linestyle='--')
            plt.tight_layout()

            # Guardar gráfico
            graph_filename = "comparacion_lcoe_minimo_csp_vs_pv.png"
            graph_filepath = os.path.join(graphs_comp_dir, graph_filename)
            plt.savefig(graph_filepath)
            print(f"\nGráfico de comparación de LCOE guardado en: {graph_filepath}")
            # plt.show() # Descomentar si quieres que se muestre
            plt.close()
        else:
            print("\nNo se pudieron combinar los datos de LCOE para graficar.")

# Aquí iría el código para comparar LCOE una vez que tengamos los datos CSV de PV LCOE.
# Podríamos comparar el LCOE mínimo encontrado para cada tecnología por país,
# o comparar LCOE para configuraciones específicas.
#
# Ejemplo (requiere df_pv_lcoe_fcr o similar):
# if not df_csp_main.empty and 'df_pv_lcoe_fcr' in locals() and not df_pv_lcoe_fcr.empty:
#     # Encontrar LCOE mínimo para CSP por país
#     min_lcoe_csp = df_csp_main.loc[df_csp_main.groupby('Pais')['LCOE_$/kWh'].idxmin()]
#
#     # Encontrar LCOE mínimo para PV por país (o para una config base)
#     # (Esto depende de cómo se calculó y guardó el LCOE PV)
#     # Suponiendo que df_pv_lcoe_fcr tiene LCOE para 1MW y varios FCR
#     min_lcoe_pv = df_pv_lcoe_fcr.loc[df_pv_lcoe_fcr.groupby('pais')['lcoe_$/kwh'].idxmin()] # OJO: nombres columnas
#
#     # Crear gráfico de barras comparando LCOE mínimo
#     # ... (código matplotlib para graficar min_lcoe_csp vs min_lcoe_pv) ...
#     print("\nSe podría generar comparación LCOE.")
else:
     print("\nFaltan datos (df_csp_main o df_pv_lcoe_fcr) para la comparación de LCOE.")


# ## 5. Comparación LCOE Específico: CSP (vs Horas Almac.) vs PV Mínimo (1MW)

if not df_csp_main.empty and 'min_lcoe_pv' in locals() and not min_lcoe_pv.empty:
    print("\n--- Iniciando Comparación LCOE Específico: CSP vs PV Mínimo (1MW) ---")

    paises_comunes = sorted(list(set(df_csp_main['Pais']) & set(min_lcoe_pv['Pais'])))

    if not paises_comunes:
        print("No hay países comunes entre los datos de CSP y los datos de LCOE mínimo de PV.")
    else:
        for pais in paises_comunes:
            # Filtrar datos CSP para el país actual
            df_csp_pais = df_csp_main[df_csp_main['Pais'] == pais].sort_values('Horas_almacenamiento')

            # Obtener LCOE mínimo PV para el país actual
            lcoe_pv_min_pais = min_lcoe_pv[min_lcoe_pv['Pais'] == pais]['LCOE_PV_min'].iloc[0]

            if df_csp_pais.empty or pd.isna(lcoe_pv_min_pais):
                print(f"  Datos incompletos para {pais}, saltando gráfico de LCOE específico.")
                continue

            plt.figure(figsize=(10, 6))
            # Graficar LCOE CSP vs Horas de Almacenamiento
            plt.plot(df_csp_pais['Horas_almacenamiento'], df_csp_pais['LCOE_$/kWh'], marker='o', linestyle='-', label=f'LCOE CSP ({pais})')

            # Añadir línea horizontal para LCOE mínimo PV
            plt.axhline(lcoe_pv_min_pais, color='red', linestyle='--', label=f'LCOE Mínimo PV 1MW ({pais})')

            plt.xlabel("Horas de Almacenamiento (CSP)")
            plt.ylabel("LCOE ($/kWh)")
            plt.title(f"Comparación LCOE: CSP (vs Almac.) vs PV Mínimo (1MW) - {pais}")
            plt.legend()
            plt.grid(True, linestyle='--')
            # plt.ylim(bottom=0) # Descomentar si quieres que el eje Y empiece en 0
            plt.tight_layout()

            # Guardar gráfico
            graph_filename = f"comparacion_lcoe_especifico_csp_vs_pv_{pais}.png"
            graph_filepath = os.path.join(graphs_comp_dir, graph_filename)
            # >>> INICIO MODIFICACIÓN: Comentar guardado de gráfico individual <<<
            # plt.savefig(graph_filepath)
            # print(f"  Gráfico de comparación de LCOE específico para {pais} guardado en: {graph_filepath}")
            print(f"  Gráfico de comparación de LCOE específico para {pais} NO guardado (código comentado).")
            # <<< FIN MODIFICACIÓN >>>
            # plt.show() # Descomentar si quieres que se muestre el gráfico
            plt.close()

else:
    print("\nNo se pudieron cargar los DataFrames necesarios (CSP y LCOE PV min) para la comparación de LCOE específico.")


# ## 6. Análisis CSP: Generación y LCOE vs Horas de Almacenamiento (Combinado en un solo gráfico)

if not df_csp_main.empty:
    print("\n--- Iniciando Análisis CSP: Generación y LCOE vs Horas (Gráfico Combinado por País) ---")

    # Verificar existencia de columnas necesarias
    required_cols = ['Pais', 'Horas_almacenamiento', 'Generacion_energia_kWh', 'LCOE_$/kWh']
    if not all(col in df_csp_main.columns for col in required_cols):
        print("ERROR: Faltan columnas necesarias en df_csp_main para el análisis combinado.")
    else:
        # Definir orden y obtener países presentes
        country_order = ['Chile', 'Espana', 'Australia']
        paises_csp_presentes = df_csp_main['Pais'].unique()
        paises_csp_sorted = sorted([p for p in paises_csp_presentes if p in country_order],
                                     key=lambda x: country_order.index(x))

        if not paises_csp_sorted:
            print("No se encontraron datos de países válidos (Chile, Espana, Australia) en df_csp_main.")
        else:
            # Crear figura ÚNICA y ejes duales
            fig_comb_single, ax1 = plt.subplots(1, 1, figsize=(12, 7))
            ax2 = ax1.twinx()

            # Paleta de colores (puedes ajustar si quieres)
            palette = {
                'Chile': 'red',
                'Espana': 'green',
                'Australia': 'blue'
            }

            print("  Generando curvas combinadas por país...")
            for pais in paises_csp_sorted:
                df_csp_pais = df_csp_main[df_csp_main['Pais'] == pais].sort_values('Horas_almacenamiento')
                color = palette.get(pais, 'gray') # Color por defecto si el país no está en la paleta

                if df_csp_pais.empty:
                    print(f"    Advertencia: No hay datos para {pais}, no se graficará.")
                    continue

                # Graficar Generación en eje izquierdo (ax1)
                ax1.plot(df_csp_pais['Horas_almacenamiento'], df_csp_pais['Generacion_energia_kWh'],
                         color=color, marker='o', linestyle='-', label=pais) # Etiqueta con nombre de país

                # Graficar LCOE en eje derecho (ax2)
                ax2.plot(df_csp_pais['Horas_almacenamiento'], df_csp_pais['LCOE_$/kWh'],
                         color=color, marker='s', linestyle='--') # Sin etiqueta aquí

            # Configurar ejes
            ax1.set_xlabel('Horas de Almacenamiento (CSP)')
            ax1.set_ylabel('Generación Anual (kWh)', color='black') # Etiqueta genérica
            ax1.tick_params(axis='y', labelcolor='tab:blue')
            ax1.ticklabel_format(style='sci', axis='y', scilimits=(0,0))
            ax1.grid(True, linestyle='--', alpha=0.7)

            ax2.set_ylabel('LCOE ($/kWh)', color='black') # Etiqueta genérica
            ax2.tick_params(axis='y', labelcolor='tab:red')
            ax2.yaxis.set_major_formatter(mticker.FormatStrFormatter('%.3f'))

            # Título
            fig_comb_single.suptitle("CSP: Generación (Eje Izq, líneas sólidas) y LCOE (Eje Der, líneas punteadas) vs Horas", fontsize=14)

            # Leyenda basada en las líneas de generación (ax1)
            ax1.legend(title='País', loc='best')

            # Ajustar layout y guardar
            fig_comb_single.tight_layout(rect=[0, 0.03, 1, 0.95])
            graph_filename_single = "analisis_csp_gen_lcoe_vs_alm_paises_combinado.png"
            graph_filepath_single = os.path.join(graphs_comp_dir, graph_filename_single)
            plt.savefig(graph_filepath_single)
            print(f"  Gráfico combinado de análisis CSP por país guardado en: {graph_filepath_single}")
            # plt.show()
            plt.close(fig_comb_single)
else:
    print("\nDataFrame df_csp_main vacío o no cargado. No se puede realizar el análisis CSP combinado.")


# ## 7. Comparación PV (vs Capacidad) y CSP (vs Múltiplo Solar)

if not df_pv_energia_cap.empty and not df_csp_variando_solarm.empty:
    print("\n--- Iniciando Comparación PV (vs Capacidad) y CSP (vs Múltiplo Solar) ---")

    # Asegurarse nombres columnas PV Energía
    pv_gen_country_col = 'pais'
    pv_gen_cap_col = 'capacidad_kw'
    pv_gen_energy_col = 'energia_kwh'

    # Asegurarse nombres columnas CSP variando SM
    csp_sm_country_col = 'Pais'
    csp_sm_col = 'Multiplo_Solar'
    csp_sm_gen_col = 'Generacion_energia_kWh'
    csp_sm_lcoe_col = 'LCOE_$/kWh'

    # Verificar columnas PV
    if not all(col in df_pv_energia_cap.columns for col in [pv_gen_country_col, pv_gen_cap_col, pv_gen_energy_col]):
        print("ERROR: Faltan columnas requeridas en df_pv_energia_cap.")
    # Verificar columnas CSP
    elif not all(col in df_csp_variando_solarm.columns for col in [csp_sm_country_col, csp_sm_col, csp_sm_gen_col, csp_sm_lcoe_col]):
        print("ERROR: Faltan columnas requeridas en df_csp_variando_solarm.")
    else:
        # Encontrar países comunes
        # Definir el orden deseado de los países para los subplots
        country_order = ['Chile', 'Espana', 'Australia']
        paises_comunes_gen = sorted(
            list(set(df_pv_energia_cap[pv_gen_country_col]) & set(df_csp_variando_solarm[csp_sm_country_col])),
            key=lambda x: country_order.index(x) if x in country_order else float('inf')
        )


        if not paises_comunes_gen:
            print("No hay países comunes entre df_pv_energia_cap y df_csp_variando_solarm para comparar generación.")
        else:
            # Crear figura para los gráficos combinados de generación (2 filas, N columnas)
            n_cols = len(paises_comunes_gen)
            fig_gen_combined, axes_gen_combined = plt.subplots(2, n_cols, figsize=(5 * n_cols, 8), sharey='row')
            # Asegurar que axes_gen_combined sea siempre un array 2D, incluso si n_cols=1
            if n_cols == 1:
                axes_gen_combined = axes_gen_combined.reshape(2, 1)

            fig_gen_combined.suptitle('Comparación Generación Anual: PV (vs Capacidad) y CSP (vs Múltiplo Solar)', fontsize=14)


            for col_idx, pais in enumerate(paises_comunes_gen):
                print(f"  Generando subplots comparativos para {pais}...")
                df_pv_pais = df_pv_energia_cap[df_pv_energia_cap[pv_gen_country_col] == pais].sort_values(pv_gen_cap_col)
                df_csp_sm_pais = df_csp_variando_solarm[df_csp_variando_solarm[csp_sm_country_col] == pais].sort_values(csp_sm_col)

                if df_pv_pais.empty or df_csp_sm_pais.empty:
                    print(f"    Datos incompletos para {pais}, saltando subplots.")
                    # Opcional: podrías querer ocultar los ejes para este país si no hay datos
                    axes_gen_combined[0, col_idx].set_visible(False)
                    axes_gen_combined[1, col_idx].set_visible(False)
                    continue

                # --- Gráfico 1 (Modificado): Comparación de LCOE (CSP vs SM vs PV Min LCOE 1MW) ---

                # >>> INICIO MODIFICACIÓN: Crear figura única para LCOE vs SM <<<
                if 'fig_lcoe_sm_single' not in locals(): # Crear solo una vez
                    fig_lcoe_sm_single, ax_lcoe_sm_single = plt.subplots(1, 1, figsize=(10, 6))
                    ax_lcoe_sm_single.set_xlabel("Múltiplo Solar (CSP)")
                    ax_lcoe_sm_single.set_ylabel("LCOE ($/kWh)")
                    ax_lcoe_sm_single.set_title('Comparación LCOE: CSP (vs Múltiplo Solar) vs PV Mínimo (1MW)')
                    ax_lcoe_sm_single.grid(True, linestyle='--')
                    ax_lcoe_sm_single.yaxis.set_major_formatter(mticker.FormatStrFormatter('%.3f'))
                    # Paleta de colores
                    lcoe_sm_palette = {
                        'Chile': 'red',
                        'Espana': 'green',
                        'Australia': 'blue'
                    }
                # <<< FIN MODIFICACIÓN >>>

                if 'min_lcoe_pv' in locals() and not min_lcoe_pv.empty:
                    if pais in min_lcoe_pv['Pais'].values:
                        lcoe_pv_min_pais = min_lcoe_pv[min_lcoe_pv['Pais'] == pais]['LCOE_PV_min'].iloc[0]

                        if not pd.isna(lcoe_pv_min_pais):
                            # >>> INICIO MODIFICACIÓN: Dibujar en ejes únicos <<<
                            color = lcoe_sm_palette.get(pais, 'gray') # Obtener color del país

                            # Graficar LCOE CSP vs Múltiplo Solar
                            ax_lcoe_sm_single.plot(df_csp_sm_pais[csp_sm_col], df_csp_sm_pais[csp_sm_lcoe_col], 
                                                   color=color, marker='o', linestyle='-', label=f'LCOE CSP {pais}')
                            # Añadir línea horizontal para LCOE mínimo PV (1MW)
                            ax_lcoe_sm_single.axhline(lcoe_pv_min_pais, color=color, linestyle='--', label=f'PV Mín {pais}')
                            # <<< FIN MODIFICACIÓN >>>
                        else:
                             print(f"    No se encontró LCOE mínimo de PV válido para {pais} para el gráfico LCOE vs SM.")
                    else:
                        print(f"    No se encontró LCOE mínimo de PV para {pais} en la tabla min_lcoe_pv para el gráfico LCOE vs SM.")
                else:
                    print("    No se encontró la tabla min_lcoe_pv para la comparación de LCOE vs SM.")

                # --- Gráfico 2 (Modificado): Comparación de Generación en subplots combinados ---
                # (Este código se mantiene igual, generando el gráfico combinado de 2xN para generación)
                # Subplot PV (Fila 0, Columna col_idx)
                ax_pv = axes_gen_combined[0, col_idx]
                ax_pv.plot(df_pv_pais[pv_gen_cap_col], df_pv_pais[pv_gen_energy_col], marker='o', linestyle='-', color='orange', label='PV')
                ax_pv.set_xlabel('Capacidad PV (kW)')
                if col_idx == 0: # Poner etiqueta Y solo en la primera columna
                    ax_pv.set_ylabel('Generación Anual (kWh)')
                ax_pv.set_title(f'PV ({pais})')
                ax_pv.grid(True, linestyle='--')
                ax_pv.ticklabel_format(style='sci', axis='y', scilimits=(0,0))
                ax_pv.ticklabel_format(style='sci', axis='x', scilimits=(0,0))
                # ax_pv.legend() # La leyenda puede saturar, quizás quitarla

                # Subplot CSP (Fila 1, Columna col_idx)
                ax_csp = axes_gen_combined[1, col_idx]
                ax_csp.plot(df_csp_sm_pais[csp_sm_col], df_csp_sm_pais[csp_sm_gen_col], marker='s', linestyle='-', color='darkblue', label='CSP')
                ax_csp.set_xlabel('Múltiplo Solar (CSP)')
                if col_idx == 0: # Poner etiqueta Y solo en la primera columna
                    ax_csp.set_ylabel('Generación Anual (kWh)')
                # Título más informativo para CSP
                alm_fijo_csp = df_csp_sm_pais['Horas_Almacenamiento_Fijas'].iloc[0] if 'Horas_Almacenamiento_Fijas' in df_csp_sm_pais else '?'
                fcr_fijo_csp = df_csp_sm_pais['FCR_Fijo'].iloc[0] if 'FCR_Fijo' in df_csp_sm_pais else '?'
                ax_csp.set_title(f'CSP ({pais}) (Alm={alm_fijo_csp}h, FCR={fcr_fijo_csp:.2f})')

                ax_csp.grid(True, linestyle='--')
                ax_csp.ticklabel_format(style='sci', axis='y', scilimits=(0,0))
                # ax_csp.legend() # La leyenda puede saturar, quizás quitarla

            # >>> INICIO MODIFICACIÓN: Ajustar y guardar figura LCOE vs SM única <<<
            if 'fig_lcoe_sm_single' in locals(): # Asegurarse que la figura se creó
                # Ajustar leyenda y layout
                ax_lcoe_sm_single.legend(title="Tecnología y País", bbox_to_anchor=(1.05, 1), loc='upper left') # Leyenda fuera del gráfico
                fig_lcoe_sm_single.tight_layout(rect=[0, 0.03, 0.85, 0.95]) # Ajustar para leyenda y título
                graph_filename_lcoe_single = "comparacion_lcoe_csp_vs_sm_vs_pv_min_paises_combinado.png"
                graph_filepath_lcoe_single = os.path.join(graphs_comp_dir, graph_filename_lcoe_single)
                fig_lcoe_sm_single.savefig(graph_filepath_lcoe_single)
                print(f"\nGráfico LCOE vs SM Países Combinado guardado en: {graph_filepath_lcoe_single}")
                plt.close(fig_lcoe_sm_single) # Cerrar la figura única LCOE
            # <<< FIN MODIFICACIÓN >>>

            # Ajustar layout y guardar la figura combinada de generación DESPUÉS del bucle
            fig_gen_combined.tight_layout(rect=[0, 0.03, 1, 0.95]) # Ajustar para título principal

            # Guardar gráfico de Generación Combinado
            graph_filename_gen_combined = "comparacion_generacion_combinada_pv_csp.png"
            graph_filepath_gen_combined = os.path.join(graphs_comp_dir, graph_filename_gen_combined)
            fig_gen_combined.savefig(graph_filepath_gen_combined)
            print(f"\nGráfico de Generación Combinado guardado en: {graph_filepath_gen_combined}")
            plt.close(fig_gen_combined) # Cerrar la figura combinada

else:
    print("\nNo se pudieron cargar los DataFrames necesarios (df_pv_energia_cap o df_csp_variando_solarm) para la Sección 7.")


# ## 8. Análisis del Factor de Capacidad (CF)

print("\n--- Iniciando Análisis del Factor de Capacidad (CF) --- ")

# Grafico 1: CF PV vs Capacidad PV
if 'df_pv_energia_cap' in locals() and not df_pv_energia_cap.empty and 'CF_PV' in df_pv_energia_cap.columns:
    try:
        plt.figure(figsize=(10, 6))
        paises_pv_cf = df_pv_energia_cap[pv_gen_country_col].unique()
        for pais in sorted(paises_pv_cf):
            df_plot = df_pv_energia_cap[df_pv_energia_cap[pv_gen_country_col] == pais].sort_values(pv_gen_cap_col)
            if not df_plot.empty:
                plt.plot(df_plot[pv_gen_cap_col], df_plot['CF_PV'], marker='.', linestyle='-', label=pais)

        plt.xlabel("Capacidad PV (kW)")
        plt.ylabel("Factor de Capacidad (CF)")
        plt.title("Factor de Capacidad PV vs Capacidad de Planta")
        plt.legend(title='País')
        plt.grid(True, linestyle='--')
        plt.gca().yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1.0))
        plt.ylim(bottom=0) # Asegurar que CF empieza en 0
        plt.tight_layout()
        graph_path = os.path.join(graphs_comp_dir, "analisis_cf_pv_vs_capacidad.png")
        plt.savefig(graph_path)
        plt.close()
        print(f"  Gráfico CF PV vs Capacidad guardado en: {graph_path}")
    except Exception as e:
        print(f"  Error generando gráfico CF PV vs Capacidad: {e}")
else:
    print("  Saltando gráfico CF PV vs Capacidad (datos o columna CF_PV no encontrados).")

# Grafico 2: CF CSP vs Horas Almacenamiento
if 'df_csp_main' in locals() and not df_csp_main.empty and 'CF_CSP' in df_csp_main.columns:
    try:
        plt.figure(figsize=(10, 6))
        paises_csp_main_cf = df_csp_main['Pais'].unique()
        for pais in sorted(paises_csp_main_cf):
             df_plot = df_csp_main[df_csp_main['Pais'] == pais].sort_values('Horas_almacenamiento')
             if not df_plot.empty:
                 plt.plot(df_plot['Horas_almacenamiento'], df_plot['CF_CSP'], marker='o', linestyle='-', label=pais)

        plt.xlabel("Horas de Almacenamiento (CSP)")
        plt.ylabel("Factor de Capacidad (CF)")
        plt.title(f"Factor de Capacidad CSP vs Horas de Almacenamiento (Capacidad Nominal Asumida: {CSP_NOMINAL_CAPACITY_KW/1000:.0f} MW)")
        plt.legend(title='País')
        plt.grid(True, linestyle='--')
        plt.gca().yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1.0))
        plt.ylim(bottom=0)
        plt.tight_layout()
        graph_path = os.path.join(graphs_comp_dir, "analisis_cf_csp_vs_horas_alm.png")
        plt.savefig(graph_path)
        plt.close()
        print(f"  Gráfico CF CSP vs Horas Almacenamiento guardado en: {graph_path}")
    except Exception as e:
        print(f"  Error generando gráfico CF CSP vs Horas Almacenamiento: {e}")
else:
    print("  Saltando gráfico CF CSP vs Horas Almacenamiento (datos o columna CF_CSP en df_csp_main no encontrados).")

# Grafico 3: CF CSP vs Múltiplo Solar
if 'df_csp_variando_solarm' in locals() and not df_csp_variando_solarm.empty and 'CF_CSP' in df_csp_variando_solarm.columns:
    try:
        plt.figure(figsize=(10, 6))
        paises_csp_sm_cf = df_csp_variando_solarm['Pais'].unique()
        for pais in sorted(paises_csp_sm_cf):
             df_plot = df_csp_variando_solarm[df_csp_variando_solarm['Pais'] == pais].sort_values('Multiplo_Solar')
             if not df_plot.empty:
                  plt.plot(df_plot['Multiplo_Solar'], df_plot['CF_CSP'], marker='s', linestyle='-', label=pais)

        # Extraer Horas Fijas y FCR Fijo del primer dato (asumiendo que son constantes)
        h_fijo = df_csp_variando_solarm['Horas_Almacenamiento_Fijas'].iloc[0] if 'Horas_Almacenamiento_Fijas' in df_csp_variando_solarm else '?'
        fcr_fijo = df_csp_variando_solarm['FCR_Fijo'].iloc[0] if 'FCR_Fijo' in df_csp_variando_solarm else '?'

        plt.xlabel("Múltiplo Solar (CSP)")
        plt.ylabel("Factor de Capacidad (CF)")
        plt.title(f"Factor de Capacidad CSP vs Múltiplo Solar (Alm={h_fijo}h, FCR={fcr_fijo:.2f}, Capacidad Nominal Asumida: {CSP_NOMINAL_CAPACITY_KW/1000:.0f} MW)")
        plt.legend(title='País')
        plt.grid(True, linestyle='--')
        plt.gca().yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1.0))
        plt.ylim(bottom=0)
        plt.tight_layout()
        graph_path = os.path.join(graphs_comp_dir, "analisis_cf_csp_vs_multiplo_solar.png")
        plt.savefig(graph_path)
        plt.close()
        print(f"  Gráfico CF CSP vs Múltiplo Solar guardado en: {graph_path}")
    except Exception as e:
        print(f"  Error generando gráfico CF CSP vs Múltiplo Solar: {e}")
else:
     print("  Saltando gráfico CF CSP vs Múltiplo Solar (datos o columna CF_CSP en df_csp_variando_solarm no encontrados).")


# ## 9. Gráfico de Dispersión: LCOE vs Generación Anual

print("\n--- Iniciando Gráfico de Dispersión LCOE vs Generación Anual --- ")

# Necesitamos df_csp_main, df_csp_variando_solarm y min_lcoe_pv (de Sección 4)
required_data_scatter = {
    'df_csp_main': locals().get('df_csp_main'),
    'df_csp_variando_solarm': locals().get('df_csp_variando_solarm'),
    'min_lcoe_pv': locals().get('min_lcoe_pv')
}

if not all(df is not None and not df.empty for df in required_data_scatter.values()):
    print("  Saltando gráficos de dispersión LCOE vs Generación (faltan DataFrames necesarios).")
else:
    # Asegurar columnas necesarias
    cols_ok = True
    if not all(c in df_csp_main.columns for c in ['Pais', 'Generacion_energia_kWh', 'LCOE_$/kWh', 'Horas_almacenamiento']):
        print("  ERROR: Faltan columnas en df_csp_main para gráfico de dispersión.")
        cols_ok = False
    if not all(c in df_csp_variando_solarm.columns for c in ['Pais', 'Generacion_energia_kWh', 'LCOE_$/kWh', 'Multiplo_Solar']):
        print("  ERROR: Faltan columnas en df_csp_variando_solarm para gráfico de dispersión.")
        cols_ok = False
    if not all(c in min_lcoe_pv.columns for c in ['Pais', 'LCOE_PV_min']):
        print("  ERROR: Faltan columnas en min_lcoe_pv para gráfico de dispersión.")
        cols_ok = False

    if cols_ok:
        # Obtener PV min LCOE data requiere también la generación asociada.
        # Esta no está directamente en min_lcoe_pv. Necesitamos buscarla en df_pv_energia_cap para 1MW.
        df_pv_1mw = pd.DataFrame()
        if 'df_pv_energia_cap' in locals() and not df_pv_energia_cap.empty:
            df_pv_1mw = df_pv_energia_cap[df_pv_energia_cap['capacidad_kw'] == 1000].copy()
            df_pv_1mw = df_pv_1mw.rename(columns={'pais':'Pais', 'energia_kwh':'Generacion_PV_1MW'}) # Renombrar para merge
            df_pv_min_lcoe_ref = pd.merge(min_lcoe_pv, df_pv_1mw[['Pais', 'Generacion_PV_1MW']], on='Pais', how='left')
            df_pv_min_lcoe_ref = df_pv_min_lcoe_ref.dropna(subset=['LCOE_PV_min', 'Generacion_PV_1MW']) # Quitar si falta LCOE o Generacion
        else:
            print("  Advertencia: No se encontró df_pv_energia_cap para obtener generación de PV 1MW.")
            df_pv_min_lcoe_ref = pd.DataFrame() # Vacío para que no falle la comprobación abajo

        paises_scatter = sorted(list(set(df_csp_main['Pais']) | set(df_csp_variando_solarm['Pais']) | set(df_pv_min_lcoe_ref['Pais'])))

        for pais in paises_scatter:
            try:
                plt.figure(figsize=(11, 7))

                # Datos CSP variando almacenamiento
                df_csp1 = df_csp_main[df_csp_main['Pais'] == pais]
                if not df_csp1.empty:
                    scatter1 = plt.scatter(df_csp1['Generacion_energia_kWh'], df_csp1['LCOE_$/kWh'], 
                                           c=df_csp1['Horas_almacenamiento'], cmap='viridis', 
                                           marker='o', s=60, label='CSP (vs Horas Alm.)', alpha=0.8)
                    cbar1 = plt.colorbar(scatter1)
                    cbar1.set_label('Horas Almacenamiento (CSP)')

                # Datos CSP variando Múltiplo Solar
                df_csp2 = df_csp_variando_solarm[df_csp_variando_solarm['Pais'] == pais]
                if not df_csp2.empty:
                    scatter2 = plt.scatter(df_csp2['Generacion_energia_kWh'], df_csp2['LCOE_$/kWh'], 
                                           c=df_csp2['Multiplo_Solar'], cmap='plasma', 
                                           marker='s', s=60, label='CSP (vs Múltiplo Solar)', alpha=0.8)
                    cbar2 = plt.colorbar(scatter2)
                    cbar2.set_label('Múltiplo Solar (CSP)')

                # Punto de referencia PV Mín LCOE (1MW)
                df_pv_ref = df_pv_min_lcoe_ref[df_pv_min_lcoe_ref['Pais'] == pais]
                if not df_pv_ref.empty:
                    plt.scatter(df_pv_ref['Generacion_PV_1MW'].iloc[0], df_pv_ref['LCOE_PV_min'].iloc[0],
                                color='red', marker='*', s=150, label='PV Mín LCOE (1MW)', zorder=5)

                plt.xlabel("Generación Anual (kWh)")
                plt.ylabel("LCOE ($/kWh)")
                plt.title(f"Dispersión LCOE vs Generación Anual - {pais}")
                plt.legend(loc='best')
                plt.grid(True, linestyle='--', alpha=0.6)
                plt.gca().xaxis.set_major_formatter(mticker.FormatStrFormatter('%.2e')) # Formato científico eje X
                plt.tight_layout()

                graph_path = os.path.join(graphs_comp_dir, f"dispersion_lcoe_vs_gen_{pais}.png")
                plt.savefig(graph_path)
                plt.close()
                print(f"  Gráfico de dispersión para {pais} guardado en: {graph_path}")

            except Exception as e:
                print(f"  Error generando gráfico de dispersión para {pais}: {e}")
                if 'fig' in locals() and plt.fignum_exists(fig.number):
                    plt.close(fig) # Intentar cerrar figura si hubo error

print("\nScript de comparación finalizado.") 