import PySAM.TcsmoltenSalt as TCSMS
import pandas as pd
import os # Importar os para manejar rutas de archivo
import matplotlib.pyplot as plt # Importar matplotlib para gráficos
import numpy as np # Importar numpy para el rango de múltiplos solares

# Definir las ubicaciones y sus archivos de recursos solares
locations = [
    {"name": "australia", "file": "/home/nicole/proyecto/NicoleTorres/PRUEBA1/Datos/australia.csv"},
    {"name": "chile", "file": "/home/nicole/proyecto/NicoleTorres/PRUEBA1/Datos/chile.csv"},
    {"name": "espana", "file": "/home/nicole/proyecto/NicoleTorres/PRUEBA1/Datos/espana.csv"}
]

# Definir directorios de salida
output_dir = "/home/nicole/proyecto/NicoleTorres/PRUEBA1/Resultados"
output_dir_graficos = "/home/nicole/proyecto/NicoleTorres/PRUEBA1/Graficos"

def run_location_simulation(location_name: str, solar_file: str) -> pd.DataFrame:
    """Ejecuta simulación CSP variando tshours y devuelve los resultados como DataFrame."""
    print(f"--- Iniciando simulación por horas de almacenamiento para {location_name.capitalize()} ---")

    storage_hours_list = list(range(4, 19))  # Valores de almacenamiento de 4 a 7 horas
    energy_generation = []
    plant_costs = []

    for tshours in storage_hours_list:
        csp_model = TCSMS.default("MSPTSingleOwner")
        solar_resource_data = {"solar_resource_file": solar_file}
        csp_model.SolarResource.assign(solar_resource_data)
        system_design_data = {"tshours": tshours}
        csp_model.SystemDesign.assign(system_design_data)

        try:
            csp_model.execute()
            print(f"  Simulación con {tshours} horas ejecutada. Energía: {csp_model.Outputs.annual_energy} kWh")
            energy_generation.append(csp_model.Outputs.annual_energy)
            plant_costs.append(csp_model.Outputs.total_installed_cost)
        except Exception as e:
            print(f"  Error con {tshours} horas: {e}")
            energy_generation.append(None)
            plant_costs.append(None)

    # Crear DataFrame
    df_results = pd.DataFrame({
        'Horas_almacenamiento': storage_hours_list,
        'Generacion_energia_kWh': energy_generation,
        'Costo_total_planta_$': plant_costs
    })
    # Ya no guarda CSV ni genera gráfico aquí
    return df_results

def main():
    """Función principal para ejecutar las simulaciones para todas las ubicaciones."""
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(output_dir_graficos, exist_ok=True)

    fixed_tshours_for_sensitivity = 10.0
    storage_results = {} # Diccionario para guardar resultados de la Fase 1

    print("--- Iniciando Fase 1: Simulaciones por Horas de Almacenamiento ---")
    for location_info in locations:
        location_name = location_info["name"]
        solar_file = location_info["file"]
        # Ejecutar la simulación y guardar resultados en el diccionario
        results_df_storage = run_location_simulation(location_name, solar_file)
        storage_results[location_name] = results_df_storage

        # Guardar CSV individual (opcional, pero lo mantenemos por ahora)
        output_csv = os.path.join(output_dir, f"resultados_almacenamiento_{location_name}.csv")
        results_df_storage.to_csv(output_csv, index=False)
        print(f"Resultados de almacenamiento para {location_name.capitalize()} guardados en {output_csv}")

    # --- Generar gráfico comparativo de Fase 1 ---
    print("\n--- Generando gráfico comparativo de almacenamiento ---")
    plt.figure(figsize=(12, 7))
    for name, df in storage_results.items():
        # Asegurarse de que hay datos para graficar
        if not df.empty and 'Horas_almacenamiento' in df.columns and 'Generacion_energia_kWh' in df.columns:
             # Filtrar filas donde la generación no sea None para evitar errores en el plot
            df_plot = df.dropna(subset=['Generacion_energia_kWh'])
            if not df_plot.empty:
                plt.plot(df_plot['Horas_almacenamiento'], df_plot['Generacion_energia_kWh'], marker='o', linestyle='-', label=name.capitalize())

    plt.xlabel("Horas de Almacenamiento Térmico (tshours)")
    plt.ylabel("Generación Anual de Energía (kWh)")
    plt.title("Comparación de Generación de Energía vs Horas de Almacenamiento")
    plt.grid(True)
    plt.legend()
    combined_plot_path = os.path.join(output_dir_graficos, "energia_vs_almacenamiento_comparacion.png")
    plt.savefig(combined_plot_path)
    print(f"Gráfico comparativo de almacenamiento guardado en {combined_plot_path}")
    plt.show()
    plt.close()
    # --- Fin del gráfico comparativo ---

    # --- Inicio Análisis de Sensibilidad Múltiplo Solar ---
    print("\n--- Iniciando Fase 2: Análisis de Sensibilidad del Múltiplo Solar ---")
    solar_multiple_results = {}
    fixed_tshours_for_sensitivity = 6.0 # Fijar tshours para este análisis, puedes ajustarlo

    for location_info in locations:
        location_name = location_info["name"]
        solar_file = location_info["file"]
        print(f"--- Iniciando análisis de sensibilidad del múltiplo solar para {location_name.capitalize()} (tshours={fixed_tshours_for_sensitivity}) ---")
        results_df_sm = run_solar_multiple_sensitivity(location_name, solar_file, fixed_tshours_for_sensitivity)
        solar_multiple_results[location_name] = results_df_sm

        # Guardar CSV individual
        output_csv_sm = os.path.join(output_dir, f"resultados_sensibilidad_sm_{location_name}.csv")
        results_df_sm.to_csv(output_csv_sm, index=False)
        print(f"Resultados de sensibilidad del múltiplo solar para {location_name.capitalize()} guardados en {output_csv_sm}")

    # --- Generar gráfico comparativo de Fase 2 ---
    print("\n--- Generando gráfico comparativo de sensibilidad del múltiplo solar ---")
    plt.figure(figsize=(12, 7))
    for name, df in solar_multiple_results.items():
        if not df.empty and 'Multiplo_Solar' in df.columns and 'Generacion_energia_kWh' in df.columns:
            df_plot = df.dropna(subset=['Generacion_energia_kWh'])
            if not df_plot.empty:
                plt.plot(df_plot['Multiplo_Solar'], df_plot['Generacion_energia_kWh'], marker='x', linestyle='--', label=f"{name.capitalize()} (tshours={fixed_tshours_for_sensitivity})")

    plt.xlabel("Múltiplo Solar")
    plt.ylabel("Generación Anual de Energía (kWh)")
    plt.title(f"Análisis de Sensibilidad: Generación vs Múltiplo Solar (con tshours={fixed_tshours_for_sensitivity})")
    plt.grid(True)
    plt.legend()
    sm_plot_path = os.path.join(output_dir_graficos, "energia_vs_multiplo_solar_comparacion.png")
    plt.savefig(sm_plot_path)
    print(f"Gráfico comparativo de sensibilidad del múltiplo solar guardado en {sm_plot_path}")
    plt.show()
    plt.close()
    # --- Fin Análisis de Sensibilidad Múltiplo Solar ---

    print("\n--- Todas las simulaciones y análisis completados ---")

def run_solar_multiple_sensitivity(location_name: str, solar_file: str, fixed_tshours: float) -> pd.DataFrame:
    """Ejecuta simulación CSP variando solar_multiple con tshours fijo y devuelve los resultados."""
    print(f"  Ejecutando análisis de sensibilidad del múltiplo solar para {location_name.capitalize()}...")

    solar_multiple_range = np.arange(1.5, 3.6, 0.25) # Rango de múltiplos solares (ej: 1.5 a 3.5 con paso 0.25)
    energy_generation = []
    plant_costs = []

    for sm in solar_multiple_range:
        csp_model = TCSMS.default("MSPTSingleOwner")
        solar_resource_data = {"solar_resource_file": solar_file}
        csp_model.SolarResource.assign(solar_resource_data)
        # Asignar tshours fijo y el múltiplo solar actual
        system_design_data = {
            "tshours": fixed_tshours,
            "solar_multiple": sm
        }
        csp_model.SystemDesign.assign(system_design_data)

        try:
            csp_model.execute()
            print(f"    Simulación con SM={sm:.2f} ejecutada. Energía: {csp_model.Outputs.annual_energy} kWh")
            energy_generation.append(csp_model.Outputs.annual_energy)
            plant_costs.append(csp_model.Outputs.total_installed_cost)
        except Exception as e:
            print(f"    Error con SM={sm:.2f}: {e}")
            energy_generation.append(None)
            plant_costs.append(None)

    # Crear DataFrame
    df_results = pd.DataFrame({
        'Multiplo_Solar': solar_multiple_range,
        'Generacion_energia_kWh': energy_generation,
        'Costo_total_planta_$': plant_costs
    })
    return df_results

if __name__ == "__main__":
    main() 