import PySAM.TcsmoltenSalt as TCSMS
import PySAM.Lcoefcr as Lcoefcr
import pandas as pd
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# --- Configuración General --- 
# Rutas base
datos_base_dir = "/home/nicole/proyecto/NicoleTorres/PRUEBA1/Datos"
output_dir_results = "/home/nicole/proyecto/NicoleTorres/PRUEBA1/Resultados"
output_dir_graphs = "/home/nicole/proyecto/NicoleTorres/PRUEBA1/graficos"

# Países a simular (Asegúrate que los archivos CSV existen)
paises = [
    {"nombre": "Chile", "archivo_sufijo": "chile", "color": "red"},
    {"nombre": "Australia", "archivo_sufijo": "australia", "color": "blue"},
    {"nombre": "Espana", "archivo_sufijo": "espana", "color": "green"}
]

# Crear directorios de salida si no existen
os.makedirs(output_dir_results, exist_ok=True)
os.makedirs(output_dir_graphs, exist_ok=True)

# --- Simulación Principal (Variando Horas de Almacenamiento por País) ---
print("-" * 50)
print("--- Iniciando Simulación Principal (Variando Horas Almacenamiento por País) ---")
print("-" * 50)

storage_hours_range = list(range(4, 19))  # De 4 a 18 horas
fixed_charge_rate_main = 0.08
fixed_operating_cost = 1000000
variable_operating_cost = 0.02
output_csv_filename_main = "resultados_simulacion_csp_multi.csv" # Nuevo nombre

results_main_all = [] # Lista para guardar todos los resultados

for pais_info in paises:
    pais_nombre = pais_info["nombre"]
    archivo_solar = os.path.join(datos_base_dir, f"{pais_info['archivo_sufijo']}.csv")
    print(f"\nProcesando Simulación Principal para: {pais_nombre}...")
    print(f"  Usando archivo solar: {archivo_solar}")

    if not os.path.exists(archivo_solar):
        print(f"  ERROR: Archivo solar no encontrado para {pais_nombre}. Saltando...")
        continue

    # Determinar cómo cargar los datos solares
    resource_input = {}
    if pais_nombre == "Australia":
        print("  Leyendo archivo de Australia manualmente con pandas...")
        try:
            # Leer metadatos de la segunda línea
            meta_df = pd.read_csv(archivo_solar, nrows=1, header=None, skiprows=1)
            lat = meta_df.iloc[0, 5]
            lon = meta_df.iloc[0, 6]
            tz = meta_df.iloc[0, 7] # Time Zone from file
            elev = meta_df.iloc[0, 8]

            # Leer datos saltando las primeras dos filas de metadatos
            data_df = pd.read_csv(archivo_solar, skiprows=2)

            # Verificar columnas necesarias y renombrar si es necesario
            required_cols = {
                'Year': 'year', 'Month': 'month', 'Day': 'day',
                'Hour': 'hour', 'Minute': 'minute', 'DNI': 'dn',
                'DHI': 'df', 'GHI': 'gh', 'Temperature': 'tdry',
                'Wind Speed': 'wspd'
            }
            # Añadir columnas opcionales si existen
            optional_cols = {'Dew Point': 'tdew', 'Pressure': 'pres'}

            resource_data = {
                'lat': lat, 'lon': lon, 'tz': tz, 'elev': elev,
                'location': pais_nombre # Añadir un identificador
            }

            cols_to_extract = {}
            for orig_col, sam_col in required_cols.items():
                if orig_col not in data_df.columns:
                    raise ValueError(f"Columna requerida '{orig_col}' no encontrada en {archivo_solar}")
                cols_to_extract[sam_col] = data_df[orig_col].tolist()
            
            for orig_col, sam_col in optional_cols.items():
                if orig_col in data_df.columns:
                    cols_to_extract[sam_col] = data_df[orig_col].tolist()
                else:
                    print(f"  Advertencia: Columna opcional '{orig_col}' no encontrada, no se incluirá.")

            resource_data.update(cols_to_extract)
            resource_input = {"solar_resource_data": resource_data}
            print(f"  Datos de Australia cargados manualmente. Lat:{lat}, Lon:{lon}, TZ:{tz}, Elev:{elev}")

        except Exception as e:
            print(f"  ERROR al leer manualmente {archivo_solar}: {e}. Saltando este país.")
            continue # Saltar al siguiente país si falla la lectura manual
    else:
        # Para otros países, usar el método original
        resource_input = {"solar_resource_file": archivo_solar}

    for tshours in storage_hours_range:
        print(f"    Simulando con {tshours} horas de almacenamiento...")
        try:
            csp_model = TCSMS.default("MSPTSingleOwner")
            csp_model.SolarResource.assign(resource_input)
            csp_model.SystemDesign.assign({"tshours": tshours})
            csp_model.execute()

            annual_energy = csp_model.Outputs.annual_energy
            total_installed_cost = csp_model.Outputs.total_installed_cost

            lcoe_model = Lcoefcr.default("GenericCSPSystemLCOECalculator")
            lcoe_model.SimpleLCOE.assign({
                "annual_energy": annual_energy,
                "capital_cost": total_installed_cost,
                "fixed_charge_rate": fixed_charge_rate_main,
                "fixed_operating_cost": fixed_operating_cost,
                "variable_operating_cost": variable_operating_cost
            })
            lcoe_model.execute()
            lcoe = lcoe_model.Outputs.lcoe_fcr
            print(f"      Energía: {annual_energy:.0f} kWh, Costo: ${total_installed_cost:,.0f}, LCOE: {lcoe:.4f} $/kWh")

            results_main_all.append({
                'Pais': pais_nombre,
                'Horas_almacenamiento': tshours,
                'Generacion_energia_kWh': annual_energy,
                'Costo_total_planta_$': total_installed_cost,
                'LCOE_$/kWh': lcoe
            })

        except Exception as e:
            print(f"      ERROR al ejecutar la simulación ({tshours}h): {e}")
            results_main_all.append({
                'Pais': pais_nombre, 'Horas_almacenamiento': tshours, 
                'Generacion_energia_kWh': None, 'Costo_total_planta_$': None, 'LCOE_$/kWh': None
            })

# Guardar resultados principales combinados
df_results_main = pd.DataFrame(results_main_all)
df_results_main.dropna(inplace=True) # Eliminar filas con errores
if not df_results_main.empty:
    output_path_main = os.path.join(output_dir_results, output_csv_filename_main)
    try:
        df_results_main.to_csv(output_path_main, index=False, float_format='%.4f')
        print(f"\nResultados principales combinados guardados en {output_path_main}")
    except Exception as e:
        print(f"ERROR al guardar resultados principales combinados: {e}")
else:
    print("\nNo se generaron resultados válidos en la simulación principal.")


# --- Análisis de Sensibilidad FCR (por País) --- 
print("-" * 50)
print("--- Iniciando Análisis de Sensibilidad FCR (por País) ---")
print("-" * 50)

tshours_sensitivity = 12
fcr_sensitivity_range = np.arange(0.05, 0.101, 0.01) # Usar numpy para precisión
output_csv_filename_sensitivity = "resultados_sensibilidad_fcr_multi.csv"

results_fcr_sens_all = []

for pais_info in paises:
    pais_nombre = pais_info["nombre"]
    archivo_solar = os.path.join(datos_base_dir, f"{pais_info['archivo_sufijo']}.csv")
    print(f"\nProcesando Sensibilidad FCR para: {pais_nombre} ({tshours_sensitivity}h almacenamiento)... ")

    if not os.path.exists(archivo_solar):
        print(f"  ERROR: Archivo solar no encontrado. Saltando...")
        continue

    # Simular una vez para obtener energía y costo base con tshours_sensitivity
    try:
        csp_model_base_sens = TCSMS.default("MSPTSingleOwner")
        csp_model_base_sens.SolarResource.assign({"solar_resource_file": archivo_solar})
        csp_model_base_sens.SystemDesign.assign({"tshours": tshours_sensitivity})
        csp_model_base_sens.execute()
        base_annual_energy = csp_model_base_sens.Outputs.annual_energy
        base_total_cost = csp_model_base_sens.Outputs.total_installed_cost
        print(f"    Energía base ({tshours_sensitivity}h): {base_annual_energy:.0f} kWh, Costo base: ${base_total_cost:,.0f}")
    except Exception as e:
        print(f"    ERROR al obtener energía/costo base para sensibilidad FCR: {e}. Saltando FCR para este país.")
        continue # Saltar al siguiente país si falla la simulación base

    for fcr in fcr_sensitivity_range:
        print(f"    Calculando LCOE con FCR = {fcr:.3f}...")
        try:
            lcoe_model_sens = Lcoefcr.default("GenericCSPSystemLCOECalculator")
            lcoe_model_sens.SimpleLCOE.assign({
                "annual_energy": base_annual_energy,
                "capital_cost": base_total_cost,
                "fixed_charge_rate": fcr, # Usar el FCR del loop
                "fixed_operating_cost": fixed_operating_cost,
                "variable_operating_cost": variable_operating_cost
            })
            lcoe_model_sens.execute()
            lcoe_sens = lcoe_model_sens.Outputs.lcoe_fcr
            print(f"      LCOE: {lcoe_sens:.4f} $/kWh")

            results_fcr_sens_all.append({
                'Pais': pais_nombre,
                'Tasa_carga_fija': fcr,
                'Generacion_energia_kWh': base_annual_energy,
                'Costo_total_planta_$': base_total_cost,
                'LCOE_$/kWh': lcoe_sens
            })
        except Exception as e:
            print(f"      ERROR al calcular LCOE para FCR={fcr}: {e}")
            results_fcr_sens_all.append({
                'Pais': pais_nombre, 'Tasa_carga_fija': fcr, 
                'Generacion_energia_kWh': base_annual_energy, 'Costo_total_planta_$': base_total_cost, 'LCOE_$/kWh': None
            })

# Guardar resultados sensibilidad FCR combinados
df_results_fcr_sens = pd.DataFrame(results_fcr_sens_all)
df_results_fcr_sens.dropna(inplace=True)
if not df_results_fcr_sens.empty:
    output_path_fcr_sens = os.path.join(output_dir_results, output_csv_filename_sensitivity)
    try:
        df_results_fcr_sens.to_csv(output_path_fcr_sens, index=False, float_format='%.4f')
        print(f"\nResultados sensibilidad FCR combinados guardados en {output_path_fcr_sens}")
    except Exception as e:
        print(f"ERROR al guardar resultados sensibilidad FCR: {e}")
else:
    print("\nNo se generaron resultados válidos en el análisis de sensibilidad FCR.")


# --- Análisis de Sensibilidad Múltiplo Solar (por País) --- 
print("-" * 50)
print("--- Iniciando Análisis de Sensibilidad Múltiplo Solar (por País) ---")
print("-" * 50)

tshours_solarm_sens = 12 
fcr_solarm_sens = fixed_charge_rate_main
solarm_sensitivity_range = np.arange(1.5, 3.01, 0.25) # 1.5 a 3.0, paso 0.25
output_csv_filename_solarm = "resultados_sensibilidad_solarm_multi.csv"

results_solarm_sens_all = []

for pais_info in paises:
    pais_nombre = pais_info["nombre"]
    archivo_solar = os.path.join(datos_base_dir, f"{pais_info['archivo_sufijo']}.csv")
    print(f"\nProcesando Sensibilidad Múltiplo Solar para: {pais_nombre} ({tshours_solarm_sens}h almacenamiento, FCR={fcr_solarm_sens})... ")

    if not os.path.exists(archivo_solar):
        print(f"  ERROR: Archivo solar no encontrado. Saltando...")
        continue

    for solarm in solarm_sensitivity_range:
        print(f"    Simulando con Múltiplo Solar = {solarm:.2f}...")
        try:
            csp_model_solarm = TCSMS.default("MSPTSingleOwner")
            csp_model_solarm.SolarResource.assign({"solar_resource_file": archivo_solar})
            csp_model_solarm.SystemDesign.assign({"tshours": tshours_solarm_sens, "solarm": solarm})
            csp_model_solarm.execute()

            annual_energy_solarm = csp_model_solarm.Outputs.annual_energy
            total_installed_cost_solarm = csp_model_solarm.Outputs.total_installed_cost

            lcoe_model_solarm = Lcoefcr.default("GenericCSPSystemLCOECalculator")
            lcoe_model_solarm.SimpleLCOE.assign({
                "annual_energy": annual_energy_solarm,
                "capital_cost": total_installed_cost_solarm,
                "fixed_charge_rate": fcr_solarm_sens,
                "fixed_operating_cost": fixed_operating_cost,
                "variable_operating_cost": variable_operating_cost
            })
            lcoe_model_solarm.execute()
            lcoe_solarm = lcoe_model_solarm.Outputs.lcoe_fcr
            print(f"      Energía: {annual_energy_solarm:.0f} kWh, Costo: ${total_installed_cost_solarm:,.0f}, LCOE: {lcoe_solarm:.4f} $/kWh")

            results_solarm_sens_all.append({
                'Pais': pais_nombre,
                'Multiplo_Solar': solarm,
                'Generacion_energia_kWh': annual_energy_solarm,
                'Costo_total_planta_$': total_installed_cost_solarm,
                'LCOE_$/kWh': lcoe_solarm
            })

        except Exception as e:
            print(f"      ERROR al ejecutar la simulación (Múltiplo Solar={solarm}): {e}")
            results_solarm_sens_all.append({
                'Pais': pais_nombre, 'Multiplo_Solar': solarm, 
                'Generacion_energia_kWh': None, 'Costo_total_planta_$': None, 'LCOE_$/kWh': None
            })

# Guardar resultados sensibilidad Múltiplo Solar combinados
df_results_solarm_sens = pd.DataFrame(results_solarm_sens_all)
df_results_solarm_sens.dropna(inplace=True)
if not df_results_solarm_sens.empty:
    output_path_solarm_sens = os.path.join(output_dir_results, output_csv_filename_solarm)
    try:
        df_results_solarm_sens.to_csv(output_path_solarm_sens, index=False, float_format='%.4f')
        print(f"\nResultados sensibilidad Múltiplo Solar combinados guardados en {output_path_solarm_sens}")
    except Exception as e:
        print(f"ERROR al guardar resultados sensibilidad Múltiplo Solar: {e}")
else:
    print("\nNo se generaron resultados válidos en el análisis de sensibilidad de Múltiplo Solar.")


# --- Generación de Gráficos Comparativos 2D --- 
print("-" * 50)
print("--- Generando Gráficos Comparativos --- ")
print("-" * 50)

# Paleta de colores para los gráficos
palette = {pais["nombre"]: pais["color"] for pais in paises}

# 1. LCOE vs Horas Almacenamiento
if not df_results_main.empty:
    try:
        plt.figure(figsize=(10, 6))
        for pais, group in df_results_main.groupby('Pais'):
            plt.plot(group['Horas_almacenamiento'], group['LCOE_$/kWh'], marker='o', linestyle='-', color=palette.get(pais, 'gray'), label=pais)
        plt.xlabel('Horas de Almacenamiento')
        plt.ylabel('LCOE ($/kWh)')
        plt.title('LCOE vs Horas de Almacenamiento por País (CSP)')
        plt.legend(title='País')
        plt.grid(True, linestyle='--')
        plt.gca().yaxis.set_major_formatter(mticker.FormatStrFormatter('%.4f'))
        plt.tight_layout()
        graph_path = os.path.join(output_dir_graphs, "comparativo_lcoe_vs_horas_csp.png")
        plt.savefig(graph_path)
        plt.close()
        print(f"Gráfico comparativo LCOE vs Horas guardado en {graph_path}")
    except Exception as e:
        print(f"Error generando gráfico LCOE vs Horas: {e}")

# 2. Energía vs Horas Almacenamiento
if not df_results_main.empty:
    try:
        plt.figure(figsize=(10, 6))
        for pais, group in df_results_main.groupby('Pais'):
            plt.plot(group['Horas_almacenamiento'], group['Generacion_energia_kWh'], marker='o', linestyle='-', color=palette.get(pais, 'gray'), label=pais)
        plt.xlabel('Horas de Almacenamiento')
        plt.ylabel('Generación Anual (kWh)')
        plt.title('Generación Anual vs Horas de Almacenamiento por País (CSP)')
        plt.legend(title='País')
        plt.grid(True, linestyle='--')
        plt.gca().yaxis.set_major_formatter(mticker.FormatStrFormatter('%.0f')) # Formato sin decimales
        plt.tight_layout()
        graph_path = os.path.join(output_dir_graphs, "comparativo_energia_vs_horas_csp.png")
        plt.savefig(graph_path)
        plt.close()
        print(f"Gráfico comparativo Energía vs Horas guardado en {graph_path}")
    except Exception as e:
        print(f"Error generando gráfico Energía vs Horas: {e}")

# 3. Costo Planta vs Horas Almacenamiento
if not df_results_main.empty:
    try:
        plt.figure(figsize=(10, 6))
        for pais, group in df_results_main.groupby('Pais'):
            plt.plot(group['Horas_almacenamiento'], group['Costo_total_planta_$'], marker='o', linestyle='-', color=palette.get(pais, 'gray'), label=pais)
        plt.xlabel('Horas de Almacenamiento')
        plt.ylabel('Costo Total Planta ($)')
        plt.title('Costo Total Planta vs Horas de Almacenamiento por País (CSP)')
        plt.legend(title='País')
        plt.grid(True, linestyle='--')
        plt.gca().yaxis.set_major_formatter(mticker.FormatStrFormatter('%.0f'))
        plt.tight_layout()
        graph_path = os.path.join(output_dir_graphs, "comparativo_costo_vs_horas_csp.png")
        plt.savefig(graph_path)
        plt.close()
        print(f"Gráfico comparativo Costo vs Horas guardado en {graph_path}")
    except Exception as e:
        print(f"Error generando gráfico Costo vs Horas: {e}")

# 4. Sensibilidad LCOE vs FCR
if not df_results_fcr_sens.empty:
    try:
        plt.figure(figsize=(10, 6))
        for pais, group in df_results_fcr_sens.groupby('Pais'):
            plt.plot(group['Tasa_carga_fija'], group['LCOE_$/kWh'], marker='o', linestyle='-', color=palette.get(pais, 'gray'), label=pais)
        plt.xlabel('Tasa Carga Fija (FCR)')
        plt.ylabel('LCOE ($/kWh)')
        plt.title(f'Sensibilidad LCOE a FCR por País ({tshours_sensitivity}h Almacenamiento) (CSP)')
        plt.legend(title='País')
        plt.grid(True, linestyle='--')
        plt.gca().xaxis.set_major_formatter(mticker.FormatStrFormatter('%.2f'))
        plt.gca().yaxis.set_major_formatter(mticker.FormatStrFormatter('%.4f'))
        plt.tight_layout()
        graph_path = os.path.join(output_dir_graphs, "comparativo_sensibilidad_lcoe_vs_fcr_csp.png")
        plt.savefig(graph_path)
        plt.close()
        print(f"Gráfico comparativo Sensibilidad LCOE vs FCR guardado en {graph_path}")
    except Exception as e:
        print(f"Error generando gráfico Sensibilidad LCOE vs FCR: {e}")

# 5. Sensibilidad LCOE vs Múltiplo Solar
if not df_results_solarm_sens.empty:
    try:
        plt.figure(figsize=(10, 6))
        for pais, group in df_results_solarm_sens.groupby('Pais'):
            plt.plot(group['Multiplo_Solar'], group['LCOE_$/kWh'], marker='o', linestyle='-', color=palette.get(pais, 'gray'), label=pais)
        plt.xlabel('Múltiplo Solar')
        plt.ylabel('LCOE ($/kWh)')
        plt.title(f'Sensibilidad LCOE a Múltiplo Solar por País ({tshours_solarm_sens}h, FCR={fcr_solarm_sens}) (CSP)')
        plt.legend(title='País')
        plt.grid(True, linestyle='--')
        plt.gca().xaxis.set_major_formatter(mticker.FormatStrFormatter('%.2f'))
        plt.gca().yaxis.set_major_formatter(mticker.FormatStrFormatter('%.4f'))
        plt.tight_layout()
        graph_path = os.path.join(output_dir_graphs, "comparativo_sensibilidad_lcoe_vs_solarm_csp.png")
        plt.savefig(graph_path)
        plt.close()
        print(f"Gráfico comparativo Sensibilidad LCOE vs Múltiplo Solar guardado en {graph_path}")
    except Exception as e:
        print(f"Error generando gráfico Sensibilidad LCOE vs Múltiplo Solar: {e}")

print("-" * 50)
print("Proceso de simulación y graficado comparativo finalizado.")


# --- BLOQUES DE GRÁFICOS 3D ANTERIORES ELIMINADOS --- 

# --- Fin del Script --- 
