#!/usr/bin/env python3
"""
Simulación de sistema fotovoltaico usando PySAM (System Advisor Model)
Este script realiza una simulación de un sistema fotovoltaico y calcula su LCOE
"""

import PySAM.Pvwattsv7 as pv
import PySAM.Lcoefcr as Lcoefcr
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Configuración de parámetros del sistema
# ---------------------------------------
# Archivo de recursos solares - asegúrate de que la ruta sea correcta
solar_resource_file = "/home/nicole/proyecto/antofagasta.csv"

# Parámetros técnicos y económicos
system_capacity_kw = 1000.0       # Capacidad del sistema en kW
dc_ac_ratio = 1.2                 # Ratio DC/AC
tilt = 20                         # Inclinación de los paneles en grados
azimuth = 180                     # Azimut en grados (180 = orientación sur)
array_type = 1                    # 1 = montaje sobre techo con rack
gcr = 0.4                         # Ground Coverage Ratio
inv_eff = 96                      # Eficiencia del inversor (%)
losses = 14.0                     # Pérdidas del sistema (%)

# Parámetros económicos
fixed_charge_rate = 0.07          # Tasa de carga fija (%)
capital_cost = 1_000_000          # Costo total de capital ($)
fixed_operating_cost = 50_000     # Costo operativo fijo anual ($/año)
variable_operating_cost = 0.01    # Costo operativo variable ($/kWh)

def simular_sistema_pv():
    """Ejecuta la simulación del sistema fotovoltaico usando PySAM"""
    
    # 1. Crear un modelo PVWatts
    print("Creando modelo PVWatts...")
    pv_model = pv.new()
    
    # 2. Asignar el archivo de recurso solar
    print(f"Usando archivo de recurso solar: {solar_resource_file}")
    pv_model.SolarResource.solar_resource_file = solar_resource_file
    
    # 3. Configurar los parámetros del sistema PV
    print("Configurando parámetros del sistema...")
    pv_model.SystemDesign.system_capacity = system_capacity_kw
    pv_model.SystemDesign.dc_ac_ratio = dc_ac_ratio
    pv_model.SystemDesign.array_type = array_type
    pv_model.SystemDesign.azimuth = azimuth
    pv_model.SystemDesign.tilt = tilt
    pv_model.SystemDesign.gcr = gcr
    pv_model.SystemDesign.inv_eff = inv_eff
    pv_model.SystemDesign.losses = losses
    
    # 4. Ejecutar la simulación PVWatts
    print("Ejecutando simulación PVWatts...")
    pv_model.execute()
    
    # 5. Obtener los resultados
    print("Obteniendo resultados de la simulación...")
    annual_energy = pv_model.Outputs.annual_energy
    print(f"Generación anual de energía PV: {annual_energy:,.2f} kWh")
    
    # 6. Calcular el LCOE
    calcular_lcoe(annual_energy)
    
    # 7. Guardar resultados en CSV
    guardar_resultados(annual_energy)
    
    # 8. Opcional: visualizar resultados mensuales
    visualizar_resultados_mensuales(pv_model)
    
    return pv_model

def calcular_lcoe(annual_energy):
    """Calcula el LCOE (Levelized Cost of Energy)"""
    
    print("Calculando LCOE...")
    # Crear el modelo para cálculo de LCOE
    lcoe_model = Lcoefcr.new()

    # Asignar valores para el cálculo del LCOE
    lcoe_model.SimpleLCOE.annual_energy = annual_energy
    lcoe_model.SimpleLCOE.capital_cost = capital_cost
    lcoe_model.SimpleLCOE.fixed_charge_rate = fixed_charge_rate
    lcoe_model.SimpleLCOE.fixed_operating_cost = fixed_operating_cost
    lcoe_model.SimpleLCOE.variable_operating_cost = variable_operating_cost
    
    # Ejecutar el cálculo del LCOE
    lcoe_model.execute()
    
    # Obtener el LCOE calculado
    lcoe = lcoe_model.Outputs.lcoe_fcr
    print(f"LCOE: {lcoe:,.4f} $/kWh")
    
    return lcoe

def guardar_resultados(annual_energy):
    """Guarda los resultados en un archivo CSV"""
    
    print("Guardando resultados en CSV...")
    # Crear un DataFrame con los resultados
    df_results = pd.DataFrame({
        "System_Capacity_kW": [system_capacity_kw],
        "Annual_Energy_kWh": [annual_energy],
        "Capital_Cost_$": [capital_cost],
        "Fixed_Charge_Rate": [fixed_charge_rate],
        "Fixed_Operating_Cost_$/yr": [fixed_operating_cost],
        "Variable_Operating_Cost_$/kWh": [variable_operating_cost],
        "LCOE_$/kWh": [calcular_lcoe(annual_energy)]
    })
    
    # Guardar en CSV
    df_results.to_csv("pv_lcoe_results.csv", index=False)
    print("Resultados guardados en pv_lcoe_results.csv")

def visualizar_resultados_mensuales(pv_model):
    """Visualiza la generación mensual de energía"""
    
    try:
        # Obtener generación mensual
        monthly_energy = pv_model.Outputs.monthly_energy
        
        # Crear gráfico de barras
        plt.figure(figsize=(10, 6))
        meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
        plt.bar(meses, monthly_energy)
        plt.title(f'Generación Mensual de Energía - Sistema FV de {system_capacity_kw} kW')
        plt.xlabel('Mes')
        plt.ylabel('Energía (kWh)')
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        
        # Guardar gráfico
        plt.savefig('generacion_mensual.png', dpi=300, bbox_inches='tight')
        print("Gráfico de generación mensual guardado como 'generacion_mensual.png'")
        
        # Mostrar el gráfico
        plt.tight_layout()
        plt.show()
    except Exception as e:
        print(f"No se pudo generar el gráfico: {e}")

def analisis_sensibilidad_tilt():
    """Realiza un análisis de sensibilidad variando la inclinación"""
    
    print("\nRealizando análisis de sensibilidad para la inclinación de los paneles...")
    inclinaciones = [0, 10, 20, 30, 40]
    energias = []
    
    for tilt_value in inclinaciones:
        # Crear modelo para cada inclinación
        test_model = pv.new()
        test_model.SolarResource.solar_resource_file = solar_resource_file
        
        # Configurar parámetros
        test_model.SystemDesign.system_capacity = system_capacity_kw
        test_model.SystemDesign.dc_ac_ratio = dc_ac_ratio
        test_model.SystemDesign.array_type = array_type
        test_model.SystemDesign.azimuth = azimuth
        test_model.SystemDesign.tilt = tilt_value  # Variar inclinación
        test_model.SystemDesign.gcr = gcr
        test_model.SystemDesign.inv_eff = inv_eff
        test_model.SystemDesign.losses = losses
        
        # Ejecutar simulación
        test_model.execute()
        
        # Obtener energía anual
        annual_energy = test_model.Outputs.annual_energy
        energias.append(annual_energy)
        print(f"  Inclinación: {tilt_value}°, Energía anual: {annual_energy:,.2f} kWh")
    
    # Crear gráfico
    plt.figure(figsize=(10, 6))
    plt.plot(inclinaciones, energias, marker='o', linestyle='-', linewidth=2)
    plt.title('Análisis de sensibilidad - Inclinación de paneles')
    plt.xlabel('Inclinación (grados)')
    plt.ylabel('Energía anual (kWh)')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # Guardar gráfico
    plt.savefig('analisis_inclinacion.png', dpi=300, bbox_inches='tight')
    print("Gráfico de análisis de sensibilidad guardado como 'analisis_inclinacion.png'")
    
    # Mostrar el gráfico
    plt.show()

if __name__ == "__main__":
    print("======== SIMULACIÓN DE SISTEMA FOTOVOLTAICO CON PySAM ========")
    # Ejecutar la simulación principal
    modelo = simular_sistema_pv()
    
    # Realizar análisis de sensibilidad
    respuesta = input("\n¿Deseas realizar un análisis de sensibilidad para la inclinación? (s/n): ")
    if respuesta.lower() == 's':
        analisis_sensibilidad_tilt()
    
    print("\n======== SIMULACIÓN COMPLETADA ========")
    print("Puedes modificar los parámetros del sistema en la parte superior del script")
    print("y volver a ejecutarlo para probar diferentes configuraciones.") 