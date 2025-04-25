# PV vs CSP: Comparativo Internacional

# ✅ Módulos necesarios
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import PySAM.TcsmoltenSalt as TCSMS
import PySAM.Lcoefcr as Lcoefcr

# ✅ Parámetros configurables
storage_hours = list(range(4, 7))
solar_resource_path = "/home/nicole/proyecto/NicoleTorres/PRUEBA1/antofagasta.csv"  # Cambia a la ruta correspondiente
fixed_charge_rate = 0.08
fixed_om_cost = 1_000_000  # USD/año
dynamic_om_cost = 0.02     # USD/kWh

# ✅ Contenedores de resultados
energy_generation = []
plant_costs = []
lcoe_values = []

# ✅ Simulación para diferentes horas de almacenamiento
for tshours in storage_hours:
    try:
        model = TCSMS.default("MSPTSingleOwner")

        # 📥 Recurso solar
        model.SolarResource.solar_resource_file = solar_resource_path

        # 🔧 Diseño del sistema
        model.SystemDesign.tshours = tshours

        # ▶️ Ejecutar simulación
        model.execute()

        annual_energy = model.Outputs.annual_energy
        installed_cost = model.Outputs.total_installed_cost
        capacity = model.Outputs.system_capacity

        energy_generation.append(annual_energy)
        plant_costs.append(installed_cost)

        # 🧮 Cálculo de LCOE
        lcoe_model = Lcoefcr.default("GenericCSPSystemLCOECalculator")
        lcoe_model.SimpleLCOE.annual_energy = annual_energy
        lcoe_model.SimpleLCOE.capital_cost = installed_cost
        lcoe_model.SimpleLCOE.fixed_charge_rate = fixed_charge_rate
        lcoe_model.SimpleLCOE.fixed_operating_cost = fixed_om_cost
        lcoe_model.SimpleLCOE.variable_operating_cost = dynamic_om_cost
        lcoe_model.execute()
        lcoe = lcoe_model.Outputs.lcoe_fcr

        lcoe_values.append(lcoe)

    except Exception as e:
        print(f"Error en tshours={tshours}: {e}")
        energy_generation.append(None)
        plant_costs.append(None)
        lcoe_values.append(None)

# ✅ Crear DataFrame con resultados
df_results = pd.DataFrame({
    "Horas_almacenamiento": storage_hours,
    "Energia_kWh": energy_generation,
    "Costo_total_USD": plant_costs,
    "LCOE_USD_kWh": lcoe_values
})

# 💾 Guardar resultados
output_csv = "/home/nicole/proyecto/NicoleTorres/PRUEBA1/resultados/csp_lcoe_antofagasta.csv"
df_results.to_csv(output_csv, index=False)
print(f"Resultados guardados en {output_csv}")

# 📊 Visualizaciones
plt.figure(figsize=(10, 6))
plt.plot(df_results["Horas_almacenamiento"], df_results["Energia_kWh"])
plt.title("Generaci\u00f3n de Energ\u00eda Anual vs Horas de Almacenamiento")
plt.xlabel("Horas de almacenamiento (tshours)")
plt.ylabel("Energ\u00eda generada (kWh)")
plt.grid(True)
plt.savefig("/home/nicole/proyecto/NicoleTorres/PRUEBA1/resultados/energia_vs_tshours.png")
plt.close()

plt.figure(figsize=(10, 6))
plt.plot(df_results["Horas_almacenamiento"], df_results["LCOE_USD_kWh"])
plt.title("LCOE vs Horas de Almacenamiento")
plt.xlabel("Horas de almacenamiento (tshours)")
plt.ylabel("LCOE (USD/kWh)")
plt.grid(True)
plt.savefig("/home/nicole/proyecto/NicoleTorres/PRUEBA1/resultados/lcoe_vs_tshours.png")
plt.close()
