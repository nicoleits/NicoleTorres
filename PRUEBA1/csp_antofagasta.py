# csp_antofagasta.py
import PySAM.TcsmoltenSalt as tcsmolten_salt # Modelo CSP Torre Sales Fundidas
import PySAM.Lcoefcr as Lcoefcr
import os
import pandas as pd
import numpy as np # Para manejar posibles NaN

def main():
    """Realiza una simulación CSP de Torre de Sales Fundidas para Antofagasta."""
    print("--- Iniciando Simulación CSP para Antofagasta ---")

    # --- 1. Definir Rutas y Parámetros --- 
    # Ruta base (asumiendo que el script está en PRUEBA1)
    script_dir = os.path.dirname(__file__)
    datos_base_dir = os.path.abspath(os.path.join(script_dir, 'Datos'))
    output_dir = os.path.abspath(os.path.join(script_dir, 'graficos', 'simulacion_csp')) # O donde quieras guardar resultados
    os.makedirs(output_dir, exist_ok=True)

    solar_resource_file = os.path.join(datos_base_dir, "antofagasta.csv")

    if not os.path.exists(solar_resource_file):
        print(f"Error: No se encontró el archivo de recurso solar en {solar_resource_file}")
        return
    
    print(f"Usando archivo de recurso solar: {solar_resource_file}")

    # --- Parámetros Técnicos CSP (Ejemplos - ¡AJUSTAR SEGÚN TU NOTEBOOK!) ---
    # Diseño del Sistema
    P_ref = 115.0             # Potencia nominal del ciclo (MWe)
    gross_net_conversion_factor = 0.9 # Factor conversión bruto a neto
    # Campo Solar y Receptor
    H_tower = 193.0           # Altura de la torre (m)
    rec_height = 18.0         # Altura del receptor (m)
    D_rec = 17.7              # Diámetro del receptor (m)
    design_eff = 0.6          # Eficiencia térmica bruta de diseño
    dni_des = 950.0           # DNI de diseño (W/m2)
    sf_A_sf = 1036700.0       # Área total de apertura del campo solar (m2)
    # Almacenamiento Térmico (TES)
    tes_hours = 12.0          # Horas de almacenamiento térmico
    # Ciclo de Potencia
    cycle_max_fraction = 1.05 # Fracción máxima de carga del ciclo
    cycle_cutoff_frac = 0.2   # Fracción mínima de carga del ciclo
    # HTF (Sales Fundidas)
    T_htf_hot_des = 565.0     # Temp. HTF caliente de diseño (°C)
    T_htf_cold_des = 290.0    # Temp. HTF fría de diseño (°C)

    # --- Parámetros Económicos (Ejemplos - ¡AJUSTAR!) ---
    total_installed_cost = 600e6  # Costo total instalado ($) - ¡MUY VARIABLE!
    fixed_operating_cost = 8e6    # Costo operativo fijo anual ($/año)
    variable_operating_cost = 3.0 # Costo operativo variable ($/MWh)
    fixed_charge_rate = 0.07      # Tasa de carga fija (FCR)

    # --- 2. Crear y Configurar Modelos PySAM --- 
    print("Creando y configurando modelos PySAM...")
    # Modelo CSP
    csp_model = tcsmolten_salt.new()
    
    # Asignar recurso solar
    csp_model.SolarResource.solar_resource_file = solar_resource_file

    # Configurar parámetros técnicos (¡ESTA ES LA PARTE MÁS DETALLADA!) 
    # Es posible que necesites muchos más parámetros según tu notebook
    csp_model.SystemDesign.P_ref = P_ref
    csp_model.SystemDesign.gross_net_conversion_factor = gross_net_conversion_factor
    csp_model.SystemDesign.h_tower = H_tower
    csp_model.TowerAndReceiver.rec_height = rec_height
    csp_model.TowerAndReceiver.D_rec = D_rec
    csp_model.TowerAndReceiver.design_eff = design_eff
    csp_model.TowerAndReceiver.dni_des = dni_des
    csp_model.SystemControl.tes_hours = tes_hours
    csp_model.PowerCycle.cycle_max_fraction = cycle_max_fraction
    csp_model.PowerCycle.cycle_cutoff_frac = cycle_cutoff_frac
    csp_model.HeatTransportSystem.T_htf_hot_des = T_htf_hot_des
    csp_model.HeatTransportSystem.T_htf_cold_des = T_htf_cold_des
    # Campo solar - A menudo se configuran más detalles aquí (layout, tipo heliostato, etc.)
    csp_model.SolarField.A_sf = sf_A_sf 

    # Modelo LCOE
    lcoe_model = Lcoefcr.new()

    # --- 3. Ejecutar Simulación CSP --- 
    print("Ejecutando simulación CSP...")
    try:
        csp_model.execute()
        print("Simulación CSP completada.")
    except Exception as e:
        print(f"Error durante la ejecución de la simulación CSP: {e}")
        # Intentar obtener más detalles si falla
        try:
             print("Errores específicos del modelo:", csp_model.Outputs.errors)
        except:
             pass # No hacer nada si no se pueden obtener errores
        return # Salir si la simulación falla

    # --- 4. Extraer Resultados CSP --- 
    annual_energy_kwh = csp_model.Outputs.annual_energy # Energía neta anual (kWh)
    capacity_factor = csp_model.Outputs.capacity_factor # Factor de capacidad (%)
    annual_gross_energy_kwh = csp_model.Outputs.annual_gross_energy # Energía bruta anual (kWh)
    kwh_per_kw = csp_model.Outputs.kwh_per_kw # kWh/kW

    print("\n--- Resultados Simulación CSP ---")
    print(f"Energía Neta Anual: {annual_energy_kwh:,.0f} kWh")
    print(f"Energía Bruta Anual: {annual_gross_energy_kwh:,.0f} kWh")
    print(f"Factor de Capacidad Neto: {capacity_factor:.2f} %")
    print(f"kWh/kW (Neto): {kwh_per_kw:.2f}")

    # --- 5. Calcular LCOE --- 
    print("\nCalculando LCOE...")
    if annual_energy_kwh > 0:
        try:
            lcoe_model.SimpleLCOE.annual_energy = annual_energy_kwh
            lcoe_model.SimpleLCOE.capital_cost = total_installed_cost
            lcoe_model.SimpleLCOE.fixed_charge_rate = fixed_charge_rate
            lcoe_model.SimpleLCOE.fixed_operating_cost = fixed_operating_cost
            # Convertir costo variable de $/MWh a $/kWh
            lcoe_model.SimpleLCOE.variable_operating_cost = variable_operating_cost / 1000.0 
            
            lcoe_model.execute()
            lcoe = lcoe_model.Outputs.lcoe_fcr
            print(f"LCOE (Calculado): ${lcoe:.4f}/kWh")
        except Exception as e:
            print(f"Error durante el cálculo del LCOE: {e}")
            lcoe = np.nan
    else:
        print("Energía anual es 0, no se puede calcular LCOE.")
        lcoe = np.nan

    # --- 6. Guardar Resumen --- 
    print("\nGuardando resumen de resultados...")
    results_summary = pd.DataFrame({
        'Parametro': ['Energia Neta Anual (kWh)', 'Factor Capacidad (%)', 'LCOE ($/kWh)', 'Costo Capital Total ($)', 'Costo Op. Fijo ($/año)', 'Costo Op. Variable ($/MWh)', 'FCR', 'Horas TES', 'Potencia Ciclo (MWe)', 'Area Campo Solar (m2)'],
        'Valor': [annual_energy_kwh, capacity_factor, lcoe, total_installed_cost, fixed_operating_cost, variable_operating_cost, fixed_charge_rate, tes_hours, P_ref, sf_A_sf ]
    })
    
    output_filename = os.path.join(output_dir, 'csp_antofagasta_summary.csv')
    try:
        results_summary.to_csv(output_filename, index=False)
        print(f"Resumen guardado en: {output_filename}")
    except Exception as e:
        print(f"Error al guardar el resumen: {e}")

    print("\n--- Simulación Finalizada ---")

# --- Punto de Entrada del Script --- 
if __name__ == "__main__":
    main() 