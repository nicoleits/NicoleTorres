import polars as pl
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import PySAM
import PySAM.Pvwattsv7 as pv
import PySAM.Lcoefcr as Lcoefcr
import numpy as np

# Definir las ubicaciones y sus archivos de datos
ubicaciones = {
    'Chile': {
        'archivo': 'Prueba1/datos_Chile.csv',
        'lat': -23.84,
        'lon': -69.89
    },
    'China': {
        'archivo': 'Prueba1/datos_China.csv',
        'lat': 44.73,
        'lon': 87.66
    },
    'Sudafrica': {
        'archivo': 'Prueba1/datos_Sudafrica.csv',
        'lat': -29.19,
        'lon': 21.30
    }
}

# Configuración del sistema PV
config_pv = {
    'system_capacity': 500,  # kW
    'module_type': 0,  # 0: Standard
    'array_type': 0,  # 0: Fixed - Open Rack
    'azimuth': 180,  # Grados (sur)
    'tilt': 30,  # Grados
    'gcr': 0.4,  # Ground Coverage Ratio
    'inverter_efficiency': 0.96,
    'dc_ac_ratio': 1.2
}

# Función para procesar los datos de un país
def procesar_pais(nombre_pais, info):
    print(f"\nProcesando datos para {nombre_pais}")
    
    # Leer datos
    df = pl.read_csv(info['archivo'])
    
    # Configurar el modelo PVWatts
    pv_model = pv.new()
    pv_model.SystemDesign.assign({
        'lat': info['lat'],
        'lon': info['lon'],
        **config_pv
    })
    
    # Preparar datos para la simulación
    weather_data = {
        'year': df['Year'].to_numpy(),
        'month': df['Month'].to_numpy(),
        'day': df['Day'].to_numpy(),
        'hour': df['Hour'].to_numpy(),
        'minute': df['Minute'].to_numpy(),
        'dn': df['DNI'].to_numpy(),
        'df': df['DHI'].to_numpy(),
        'gh': df['GHI'].to_numpy(),
        'wspd': np.zeros_like(df['Year'].to_numpy()),  # Velocidad del viento (no disponible)
        'tdry': np.zeros_like(df['Year'].to_numpy())  # Temperatura (no disponible)
    }
    
    # Ejecutar simulación
    pv_model.Weather.assign(weather_data)
    pv_model.execute()
    
    # Obtener resultados
    resultados = pv_model.Outputs.export()
    
    # Calcular LCOE
    lcoe_model = Lcoefcr.new()
    lcoe_model.FinancialParameters.assign({
        'analysis_period': 25,
        'system_capacity': config_pv['system_capacity'],
        'debt_fraction': 0.7,
        'debt_rate': 0.05,
        'debt_term': 15,
        'system_cost': 1000,  # $/kW
        'om_cost': 15,  # $/kW/year
        'property_tax_rate': 0.02,
        'insurance_rate': 0.005,
        'real_discount_rate': 0.07,
        'inflation_rate': 0.025,
        'derate': 0.99,
        'reserves_fraction': 0.0,
        'construction_financing_cost': 0.0,
        'cost_degradation': 0.005,
        'degradation_type': 0,
        'total_lcoe': 0.0,
        'total_revenue': 0.0
    })
    
    lcoe_model.SystemOutput.assign({
        'gen': resultados['gen']  # kWh/year
    })
    
    lcoe_model.execute()
    lcoe = lcoe_model.Outputs.export()['lcoe_real']
    
    return {
        'nombre': nombre_pais,
        'lat': info['lat'],
        'lon': info['lon'],
        'generacion_anual': resultados['gen'],
        'lcoe': lcoe,
        'eficiencia': resultados['system_efficiency'],
        'perdidas': resultados['system_losses']
    }

# Procesar todos los países
resultados = []
for nombre_pais, info in ubicaciones.items():
    try:
        resultado = procesar_pais(nombre_pais, info)
        resultados.append(resultado)
    except Exception as e:
        print(f"Error procesando {nombre_pais}: {str(e)}")

# Crear visualizaciones
plt.figure(figsize=(15, 10))

# 1. Generación anual por país
plt.subplot(2, 2, 1)
generacion = [r['generacion_anual'] for r in resultados]
paises = [r['nombre'] for r in resultados]
plt.bar(paises, generacion)
plt.title('Generación Anual por País')
plt.ylabel('Generación (kWh/año)')
plt.xticks(rotation=45)

# 2. LCOE por país
plt.subplot(2, 2, 2)
lcoe = [r['lcoe'] for r in resultados]
plt.bar(paises, lcoe)
plt.title('LCOE por País')
plt.ylabel('LCOE ($/kWh)')
plt.xticks(rotation=45)

# 3. Eficiencia del sistema por país
plt.subplot(2, 2, 3)
eficiencia = [r['eficiencia'] for r in resultados]
plt.bar(paises, eficiencia)
plt.title('Eficiencia del Sistema por País')
plt.ylabel('Eficiencia')
plt.xticks(rotation=45)

# 4. Pérdidas del sistema por país
plt.subplot(2, 2, 4)
perdidas = [r['perdidas'] for r in resultados]
plt.bar(paises, perdidas)
plt.title('Pérdidas del Sistema por País')
plt.ylabel('Pérdidas (%)')
plt.xticks(rotation=45)

plt.tight_layout()
plt.savefig('Prueba1/resultados_simulacion.png')
plt.close()

# Imprimir resultados
print("\nResultados de la simulación:")
print("-" * 50)
for r in resultados:
    print(f"\nPaís: {r['nombre']}")
    print(f"Latitud: {r['lat']}°")
    print(f"Longitud: {r['lon']}°")
    print(f"Generación anual: {r['generacion_anual']:.2f} kWh/año")
    print(f"LCOE: {r['lcoe']:.4f} $/kWh")
    print(f"Eficiencia del sistema: {r['eficiencia']:.2%}")
    print(f"Pérdidas del sistema: {r['perdidas']:.2f}%") 