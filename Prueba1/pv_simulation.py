import PySAM.Pvwattsv7 as pv
import PySAM.Lcoefcr as Lcoefcr
import pandas as pd

# Leer los metadatos del archivo TMY
tmy_file = "/home/nicole/proyecto/NicoleTorres/Prueba1/datos_Chile_tmy.csv"
metadata = {}
with open(tmy_file, 'r') as f:
    for i in range(12):  # Leer las primeras 12 líneas de metadatos
        line = f.readline().strip()
        if 'Latitude:' in line:
            metadata['lat'] = float(line.split(':')[1].strip())
        elif 'Longitude:' in line:
            metadata['lon'] = float(line.split(':')[1].strip())
        elif 'Time Zone:' in line:
            metadata['tz'] = float(line.split(':')[1].strip())
        elif 'Elevation:' in line:
            metadata['elev'] = float(line.split(':')[1].strip())

# Leer los datos del archivo TMY
df = pd.read_csv(tmy_file, skiprows=12)

# Crear un modelo PVWatts "desde cero"
pv_model = pv.new()

# Configurar datos solares y ubicación
weather = {
    'lat': metadata['lat'],
    'lon': metadata['lon'],
    'tz': metadata['tz'],
    'elev': metadata['elev'],
    'year': df['Year'].iloc[0],
    'month': df['Month'].tolist(),
    'day': df['Day'].tolist(),
    'hour': df['Hour'].tolist(),
    'minute': df['Minute'].tolist(),
    'dn': df['DNI'].tolist(),  # Direct Normal Irradiance
    'df': df['DHI'].tolist(),  # Diffuse Horizontal Irradiance
    'gh': df['GHI'].tolist(),  # Global Horizontal Irradiance
    'temp': df['Temperature'].tolist(),
    'wspd': df['Wind Speed'].tolist(),
    'pres': df['Pressure'].tolist(),
    'rh': df['Relative Humidity'].tolist()
}

pv_model.SolarResource.assign(weather)

# Configurar parámetros del sistema PV
pv_model.SystemDesign.system_capacity = 1000.0  # 1 MW
pv_model.SystemDesign.dc_ac_ratio = 1.2
pv_model.SystemDesign.array_type = 1  # Fixed open rack
pv_model.SystemDesign.azimuth = 180
pv_model.SystemDesign.tilt = 20
pv_model.SystemDesign.gcr = 0.4
pv_model.SystemDesign.inv_eff = 96
pv_model.SystemDesign.losses = 14.0

# Ejecutar la simulación PVWatts
pv_model.execute()

# Obtener la generación anual de energía (kWh)
annual_energy = pv_model.Outputs.annual_energy
print(f"Generación anual de energía PV: {annual_energy} kWh")

# Calcular LCOE
lcoe_model = Lcoefcr.new()
lcoe_model.SystemCosts.total_installed_cost = 1_000_000
lcoe_model.SystemCosts.fixed_operating_cost = 50_000
lcoe_model.SystemCosts.variable_operating_cost = 0.01
lcoe_model.FinancialParameters.fixed_charge_rate = 0.07
lcoe_model.SystemOutput.annual_energy = annual_energy

lcoe_model.execute()
lcoe = lcoe_model.Outputs.lcoe_real
print(f"LCOE: {lcoe} $/kWh")

# Guardar resultados en un archivo CSV
results = {
    'annual_energy_kwh': annual_energy,
    'lcoe_usd_kwh': lcoe,
    'system_capacity_kw': 1000.0,
    'capital_cost_usd': 1_000_000,
    'fixed_operating_cost_usd': 50_000,
    'variable_operating_cost_usd_kwh': 0.01,
    'fixed_charge_rate': 0.07,
    'latitude': metadata['lat'],
    'longitude': metadata['lon']
}

df_results = pd.DataFrame([results])
df_results.to_csv('pv_lcoe_results.csv', index=False)
print("Resultados guardados en pv_lcoe_results.csv") 