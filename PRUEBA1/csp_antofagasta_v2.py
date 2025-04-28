# csp_antofagasta_v2.py
import PySAM.TcsmoltenSalt as tcsmolten_salt # Modelo CSP Torre Sales Fundidas
import PySAM.Lcoefcr as Lcoefcr
import os
import pandas as pd
import numpy as np # Para manejar posibles NaN

def main():
    """
    Realiza una simulación CSP de Torre de Sales Fundidas para Antofagasta
    utilizando PySAM y calcula el LCOE.
    """
    print("--- Iniciando Simulación CSP v2 para Antofagasta ---")

    # --- 1. Definir Rutas y Parámetros ---
    try:
        # Ruta base (asumiendo que el script está en PRUEBA1)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        datos_base_dir = os.path.abspath(os.path.join(script_dir, 'Datos'))
        output_dir = os.path.abspath(os.path.join(script_dir, 'graficos', 'simulacion_csp'))
        os.makedirs(output_dir, exist_ok=True)

        solar_resource_file = os.path.join(datos_base_dir, "antofagasta.csv")

        if not os.path.exists(solar_resource_file):
            print(f"Error Crítico: No se encontró el archivo de recurso solar en {solar_resource_file}")
            print("Asegúrate de que el archivo 'antofagasta.csv' exista en la carpeta 'Datos' dentro de 'PRUEBA1'.")
            return # Salir si no se encuentra el archivo

        print(f"Usando archivo de recurso solar: {solar_resource_file}")

    except Exception as e:
        print(f"Error configurando rutas: {e}")
        return

    # --- Parámetros Técnicos CSP (EJEMPLOS - ¡AJUSTAR!) ---
    # Estos valores son representativos, modifícalos según tu diseño específico.
    print("\nConfigurando parámetros técnicos (valores de ejemplo)...")
    P_ref = 115.0             # Potencia nominal bruta del ciclo (MWe)
    gross_net_conversion_factor = 0.9 # Factor conversión bruto a neto
    h_tower = 193.0           # Altura de la torre (m) - Corregido
    solar_mult = 2.4          # Múltiplo solar (tamaño campo solar / necesidad ciclo potencia)
    tes_hours = 12.0          # Horas de almacenamiento térmico
    T_htf_hot_des = 565.0     # Temp. HTF caliente de diseño (°C)
    T_htf_cold_des = 290.0    # Temp. HTF fría de diseño (°C)
    # Parámetros adicionales (puedes añadir/modificar más según sea necesario)
    rec_height = 18.0         # Altura del receptor (m)
    D_rec = 17.7              # Diámetro del receptor (m)
    design_eff = 0.6          # Eficiencia térmica bruta de diseño (usada para cálculo interno)
    dni_des = 950.0           # DNI de diseño (W/m2) - Usado para diseño interno
    cycle_max_fraction = 1.05 # Fracción máxima de carga del ciclo
    cycle_cutoff_frac = 0.2   # Fracción mínima de carga del ciclo


    # --- Parámetros Económicos (EJEMPLOS - ¡AJUSTAR!) ---
    print("Configurando parámetros económicos (valores de ejemplo)...")
    # El costo de capital es muy dependiente del tamaño y diseño exacto
    # Este es un valor estimado para una planta ~100-115 MWe con TES
    total_installed_cost = 750e6  # Costo total instalado ($) - ¡ESTIMACIÓN, AJUSTAR!
    # Los costos de operación también varían
    fixed_operating_cost = 65.0   # Costo operativo fijo ($/kWe/año) -> PySAM lo escala por P_ref
    variable_operating_cost = 3.5 # Costo operativo variable ($/MWh) -> Bruto
    fixed_charge_rate = 0.07      # Tasa de carga fija (FCR) para LCOE simple

    # --- 2. Crear y Configurar Modelos PySAM ---
    print("Creando modelos PySAM...")
    try:
        csp_model = tcsmolten_salt.new()
        lcoe_model = Lcoefcr.new()
    except Exception as e:
        print(f"Error creando modelos PySAM: {e}")
        return

    print("Configurando modelo CSP...")
    try:
        # Asignar recurso solar
        csp_model.SolarResource.solar_resource_file = solar_resource_file

        # Configurar parámetros técnicos
        csp_model.SystemDesign.P_ref = P_ref
        csp_model.SystemDesign.gross_net_conversion_factor = gross_net_conversion_factor
        csp_model.SystemDesign.h_tower = h_tower # Altura de torre
        csp_model.SystemDesign.solar_mult = solar_mult # Múltiplo solar

        csp_model.TowerAndReceiver.rec_height = rec_height
        csp_model.TowerAndReceiver.D_rec = D_rec
        csp_model.TowerAndReceiver.design_eff = design_eff
        csp_model.TowerAndReceiver.dni_des = dni_des

        csp_model.SystemControl.tes_hours = tes_hours

        csp_model.PowerCycle.cycle_max_fraction = cycle_max_fraction
        csp_model.PowerCycle.cycle_cutoff_frac = cycle_cutoff_frac

        csp_model.HeatTransportSystem.T_htf_hot_des = T_htf_hot_des
        csp_model.HeatTransportSystem.T_htf_cold_des = T_htf_cold_des

        # Configurar costos directamente en el modelo tecnológico si se usa LCOE completo
        # o para que estén disponibles en los resultados.
        # Para Lcoefcr simple, estos se pasan al modelo LCOE más tarde.
        # csp_model.FinancialParameters.total_installed_cost = total_installed_cost (Si usaras modelo financiero completo)
        csp_model.SystemCosts.om_fixed = fixed_operating_cost  # Asigna costo fijo por kWe-año
        csp_model.SystemCosts.om_variable = variable_operating_cost # Asigna costo variable por MWhe bruto

        # Podrías necesitar configurar muchos más parámetros para una simulación detallada
        # Ejemplo: csp_model.HeliostatField. ... , csp_model.SystemControl. ... , etc.

    except AttributeError as ae:
         print(f"Error de Atributo configurando CSP: {ae}")
         print("Verifica que los nombres y grupos de parámetros sean correctos para TcsmoltenSalt.")
         return
    except Exception as e:
        print(f"Error configurando parámetros CSP: {e}")
        return

    # --- 3. Ejecutar Simulación CSP ---
    print("Ejecutando simulación CSP...")
    try:
        csp_model.execute()
        print("Simulación CSP completada.")
    except Exception as e:
        print(f"Error durante la ejecución de la simulación CSP: {e}")
        # Intentar obtener más detalles si falla
        try:
             # Los errores específicos a veces están en csp_model.Outputs.errors (si existe)
             # o pueden requerir inspeccionar logs si la configuración es compleja.
             if hasattr(csp_model, 'Outputs') and hasattr(csp_model.Outputs, 'errors'):
                  print("Errores específicos del modelo:", csp_model.Outputs.errors)
        except Exception as ie:
             print(f"No se pudieron obtener errores específicos del modelo: {ie}")
        return # Salir si la simulación falla

    # --- 4. Extraer Resultados CSP --- 
    print("\nExtrayendo resultados de la simulación...")
    try:
        annual_energy_kwh = csp_model.Outputs.annual_energy # Energía neta anual (kWh)
        capacity_factor = csp_model.Outputs.capacity_factor # Factor de capacidad neto(%)
        annual_gross_energy_kwh = csp_model.Outputs.annual_gross_energy # Energía bruta anual (kWh)
        kwh_per_kw = csp_model.Outputs.kwh_per_kw # kWh/kW (Neto)
        # Otros resultados útiles
        ppa_price = csp_model.Outputs.ppa # Precio PPA calculado (si se usa modelo financiero)
        lcoe_nom = csp_model.Outputs.lcoe_nom # LCOE Nominal calculado (si se usa modelo financiero)
        lcoe_real = csp_model.Outputs.lcoe_real # LCOE Real calculado (si se usa modelo financiero)
        project_return_aftertax_npv = csp_model.Outputs.project_return_aftertax_npv # NPV (si se usa modelo financiero)

        print("\n--- Resultados Simulación CSP ---")
        print(f"Energía Neta Anual:          {annual_energy_kwh:,.0f} kWh")
        print(f"Energía Bruta Anual:         {annual_gross_energy_kwh:,.0f} kWh")
        print(f"Factor de Capacidad (Neto):  {capacity_factor:.2f} %")
        print(f"Generación Específica (Neto): {kwh_per_kw:.1f} kWh/kW")
        # Imprimir resultados financieros si existen (serán 0 si no se configuró modelo financiero)
        print(f"LCOE Nominal (Modelo Finan.): {lcoe_nom:.4f} $/kWh")
        print(f"LCOE Real (Modelo Finan.):   {lcoe_real:.4f} $/kWh")
        print(f"PPA (Modelo Finan.):         {ppa_price:.4f} $/kWh")
        print(f"NPV (Modelo Finan.):         ${project_return_aftertax_npv:,.0f}")


    except AttributeError as ae:
        print(f"Error extrayendo resultados: Falta el atributo {ae}")
        print("La simulación pudo haber fallado o no produjo todas las salidas esperadas.")
        return
    except Exception as e:
        print(f"Error extrayendo resultados: {e}")
        return


    # --- 5. Calcular LCOE Simple (Usando Lcoefcr) ---
    print("\nCalculando LCOE Simple (con Lcoefcr)...")
    lcoe_simple = np.nan # Inicializar como NaN
    if annual_energy_kwh > 0:
        try:
            lcoe_model.SimpleLCOE.annual_energy = annual_energy_kwh
            lcoe_model.SimpleLCOE.capital_cost = total_installed_cost
            lcoe_model.SimpleLCOE.fixed_charge_rate = fixed_charge_rate

            # O&M Fijo: PySAM espera $/año. Se calculó arriba como $/kWe/año.
            # Convertir a $/año total multiplicando por P_ref en kWe
            om_fixed_total_annual = fixed_operating_cost * (P_ref * 1000.0)
            lcoe_model.SimpleLCOE.fixed_operating_cost = om_fixed_total_annual

            # O&M Variable: PySAM espera $/kWh. Se definió arriba como $/MWh (bruto).
            # Convertir a $/kWh dividiendo por 1000.
            om_variable_per_kwh = variable_operating_cost / 1000.0
            lcoe_model.SimpleLCOE.variable_operating_cost = om_variable_per_kwh

            lcoe_model.execute()
            lcoe_simple = lcoe_model.Outputs.lcoe_fcr
            print(f"LCOE Simple (Calculado): ${lcoe_simple:.4f}/kWh")
            print(f"  (Usando Costo Capital: ${total_installed_cost:,.0f}, FCR: {fixed_charge_rate:.3f})")
            print(f"  (Usando OM Fijo Total: ${om_fixed_total_annual:,.0f}/año)")
            print(f"  (Usando OM Variable: ${om_variable_per_kwh:.5f}/kWh)")

        except Exception as e:
            print(f"Error durante el cálculo del LCOE Simple: {e}")
            lcoe_simple = np.nan
    else:
        print("Energía anual neta es 0, no se puede calcular LCOE Simple.")
        lcoe_simple = np.nan

    # --- 6. Guardar Resumen ---
    print("\nGuardando resumen de resultados...")
    results_data = {
        'Parametro': [
            'Energia Neta Anual (kWh)', 'Factor Capacidad Neto (%)', 'Generacion Especifica (kWh/kW)',
            'LCOE Simple ($/kWh)', 'LCOE Nominal (Finan.) ($/kWh)', 'LCOE Real (Finan.) ($/kWh)',
            'Costo Capital Total ($)', 'Costo Op. Fijo ($/kWe/año)', 'Costo Op. Variable ($/MWh)',
            'FCR (para LCOE Simple)', 'Horas TES', 'Potencia Ciclo Bruta (MWe)',
            'Múltiplo Solar', 'Altura Torre (m)'
        ],
        'Valor': [
            annual_energy_kwh, capacity_factor, kwh_per_kw,
            lcoe_simple, lcoe_nom, lcoe_real,
            total_installed_cost, fixed_operating_cost, variable_operating_cost,
            fixed_charge_rate, tes_hours, P_ref,
            solar_mult, h_tower
        ]
    }
    results_summary = pd.DataFrame(results_data)

    output_filename = os.path.join(output_dir, 'csp_antofagasta_v2_summary.csv')
    try:
        results_summary.to_csv(output_filename, index=False, float_format='%.5f')
        print(f"Resumen guardado en: {output_filename}")
    except Exception as e:
        print(f"Error al guardar el resumen: {e}")

    print("\n--- Simulación Finalizada ---")

# --- Punto de Entrada del Script ---
if __name__ == "__main__":
    main() 