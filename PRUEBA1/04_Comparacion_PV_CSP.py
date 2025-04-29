import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np

# # Comparación de Resultados PV y CSP

# ## 1. Configuración de Rutas

# Directorio donde se encuentran los resultados CSV
results_dir = "/home/nicole/proyecto/NicoleTorres/PRUEBA1/Resultados"
# Directorio donde guardar los gráficos de comparación (puedes crear uno nuevo o usar existente)
graphs_comp_dir = "/home/nicole/proyecto/NicoleTorres/PRUEBA1/graficos/comparacion_pv_csp"
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

# Cargar datos principales de CSP
df_csp_main = pd.DataFrame() # Inicializar vacío
try:
    df_csp_main = pd.read_csv(csv_csp_main)
    print(f"\nCargado: {csv_csp_main}")
    # print(df_csp_main.head()) # Descomenta para ver las primeras filas
except FileNotFoundError:
    print(f"\nERROR: Archivo no encontrado - {csv_csp_main}")

# Cargar datos de Energía vs Capacidad de PV
df_pv_energia_cap = pd.DataFrame() # Inicializar vacío
try:
    df_pv_energia_cap = pd.read_csv(csv_pv_energia_cap)
    print(f"Cargado: {csv_pv_energia_cap}")
    # print(df_pv_energia_cap.head()) # Descomenta para ver las primeras filas
except FileNotFoundError:
    print(f"ERROR: Archivo no encontrado - {csv_pv_energia_cap}")

# Cargar otros DataFrames de PV o CSP según sea necesario para la comparación deseada
# Ejemplo:
# df_pv_lcoe_fcr = pd.DataFrame() # Inicializar vacío
# try:
#     df_pv_lcoe_fcr = pd.read_csv(csv_pv_lcoe_fcr)
#     print(f"Cargado: {csv_pv_lcoe_fcr}")
# except FileNotFoundError:
#     print(f"ERROR: Archivo no encontrado - {csv_pv_lcoe_fcr}")


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
        plt.savefig(graph_filepath)
        print(f"\nGráfico de comparación de generación guardado en: {graph_filepath}")
        # plt.show() # Descomentar si quieres que se muestre el gráfico al ejecutar el script
        plt.close()

    else:
        if energia_pv_series.empty:
             print(f"\nNo se encontraron datos de PV para {pais_comparar} con capacidad {capacidad_pv_comparar} kW.")
        if df_csp_pais.empty:
             print(f"\nNo se encontraron datos de CSP para {pais_comparar}.")

else:
    print("\nNo se pudieron cargar los DataFrames necesarios o están vacíos para la comparación de generación.")


# ## 4. Comparación de LCOE (Pendiente - Necesita datos LCOE de PV)

# Aquí iría el código para comparar LCOE una vez que tengamos los datos CSV de PV LCOE.
# Podríamos comparar el LCOE mínimo encontrado para cada tecnología por país,
# o comparar LCOE para configuraciones específicas.

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
# else:
#      print("\nFaltan datos (df_csp_main o df_pv_lcoe_fcr) para la comparación de LCOE.")

print("\nScript de comparación finalizado.") 