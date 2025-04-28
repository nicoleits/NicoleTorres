# simulation_logic.py
import PySAM.Pvwattsv7 as pv
import PySAM.Lcoefcr as Lcoefcr
import numpy as np
import pandas as pd # Aunque no se use directamente aquí, puede ser útil
import os

# Constante para la ruta base de datos, relativa a este script
# Sube un nivel desde 'dashboard' a 'PRUEBA1', luego entra a 'Datos'
DATOS_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Datos'))

def get_paises_config():
    """Devuelve la configuración de países con rutas absolutas a los archivos."""
    return [
        {"nombre": "australia", "archivo": os.path.join(DATOS_BASE_DIR, "australia.csv"), "color": "deeppink"},
        {"nombre": "chile", "archivo": os.path.join(DATOS_BASE_DIR, "chile.csv"), "color": "mediumpurple"},
        {"nombre": "espana", "archivo": os.path.join(DATOS_BASE_DIR, "espana.csv"), "color": "turquoise"}
    ]

def run_single_simulation(solar_file, capacity_kw=1000, tilt=20, azimuth=180, inv_eff=96, losses=14, dc_ac_ratio=1.2, gcr=0.4, array_type=1, adjust_constant=0):
    """Ejecuta una simulación PVWatts simple y devuelve la energía anual y/o el modelo."""
    try:
        if not os.path.exists(solar_file):
             print(f"Error: Archivo de recurso solar no encontrado en {solar_file}")
             return None # Indicar fallo

        pv_model = pv.new()
        pv_model.SolarResource.solar_resource_file = solar_file
        pv_model.SystemDesign.system_capacity = capacity_kw
        pv_model.SystemDesign.dc_ac_ratio = dc_ac_ratio
        pv_model.SystemDesign.array_type = array_type
        pv_model.SystemDesign.azimuth = azimuth
        pv_model.SystemDesign.tilt = tilt
        pv_model.SystemDesign.gcr = gcr
        pv_model.SystemDesign.inv_eff = inv_eff
        pv_model.SystemDesign.losses = losses
        pv_model.execute()
        return pv_model # Devolver el modelo para acceder a más outputs si es necesario
    except Exception as e:
        print(f"Error en simulación PV: {e}")
        print(f"  Archivo: {solar_file}")
        print(f"  Parámetros: Cap={capacity_kw}, Tilt={tilt}, Az={azimuth}")
        return None # Indicar fallo

def calculate_lcoe_point(annual_energy, capital_cost, fcr, fixed_op_cost, var_op_cost):
    """Calcula un único punto LCOE."""
    if annual_energy is None or annual_energy <= 0:
        return np.nan # No se puede calcular LCOE sin energía
    try:
        lcoe_model = Lcoefcr.new()
        lcoe_model.SimpleLCOE.annual_energy = annual_energy
        lcoe_model.SimpleLCOE.capital_cost = capital_cost
        lcoe_model.SimpleLCOE.fixed_charge_rate = fcr
        lcoe_model.SimpleLCOE.fixed_operating_cost = fixed_op_cost
        lcoe_model.SimpleLCOE.variable_operating_cost = var_op_cost
        lcoe_model.execute()
        return lcoe_model.Outputs.lcoe_fcr
    except Exception as e:
        print(f"Error calculando LCOE: {e}")
        return np.nan

def get_tilt_sensitivity_data(pais_info, config):
    """Calcula datos para gráfico de sensibilidad de inclinación."""
    capacity = config.get("capacity_kw", 1000)
    solar_file = pais_info["archivo"]
    azimuth = 0 if pais_info["nombre"] in ["chile", "australia"] else 180
    
    # Parámetros adicionales que podrían venir en config
    inv_eff = config.get("inv_eff", 96)
    losses = config.get("losses", 14.0)
    dc_ac_ratio = config.get("dc_ac_ratio", 1.2)
    gcr = config.get("gcr", 0.4)

    tilts = np.arange(0, 91, 5) # Rango más amplio, ajustar si es lento
    energies = []
    valid_tilts = []

    for tilt in tilts:
        pv_model_result = run_single_simulation(
            solar_file=solar_file,
            capacity_kw=capacity,
            tilt=float(tilt),
            azimuth=azimuth,
            inv_eff=inv_eff,
            losses=losses,
            dc_ac_ratio=dc_ac_ratio,
            gcr=gcr
        )
        if pv_model_result is not None:
             energy = pv_model_result.Outputs.annual_energy
             energies.append(energy)
             valid_tilts.append(tilt)
        else:
            energies.append(np.nan) # Marcar como inválido si la simulación falló
            valid_tilts.append(tilt)

    return {"tilts": valid_tilts, "energies": energies, "color": pais_info["color"]}

def get_dcac_sensitivity_data(pais_info, config):
    """Calcula datos para sensibilidad DC/AC."""
    capacity = config.get("capacity_kw", 1000)
    tilt = config.get("tilt", 20.0)
    solar_file = pais_info["archivo"]
    azimuth = 0 if pais_info["nombre"] in ["chile", "australia"] else 180
    
    # Parámetros adicionales
    inv_eff = config.get("inv_eff", 96)
    losses = config.get("losses", 14.0)
    gcr = config.get("gcr", 0.4)

    dc_ac_ratios = np.arange(1.0, 2.01, 0.1) # Ajustar paso si es necesario
    energies = []
    valid_ratios = []

    for ratio in dc_ac_ratios:
        pv_model_result = run_single_simulation(
            solar_file=solar_file,
            capacity_kw=capacity,
            tilt=tilt,
            azimuth=azimuth,
            dc_ac_ratio=round(ratio, 2),
            inv_eff=inv_eff,
            losses=losses,
            gcr=gcr
        )
        if pv_model_result is not None:
            energy = pv_model_result.Outputs.annual_energy
            energies.append(energy)
            valid_ratios.append(ratio)
        else:
            energies.append(np.nan)
            valid_ratios.append(ratio)
            
    return {"ratios": valid_ratios, "energies": energies, "color": pais_info["color"]}

def get_lcoe_vs_fcr_data(pais_info, config_lcoe):
    """Calcula datos para LCOE vs FCR."""
    capacity = config_lcoe.get("capacity_kw", 1000)
    tilt = config_lcoe.get("tilt", 20.0)
    solar_file = pais_info["archivo"]
    azimuth = 0 if pais_info["nombre"] in ["chile", "australia"] else 180

    # Parámetros base PV
    inv_eff = config_lcoe.get("inv_eff", 96)
    losses = config_lcoe.get("losses", 14.0)
    dc_ac_ratio = config_lcoe.get("dc_ac_ratio", 1.2)
    gcr = config_lcoe.get("gcr", 0.4)
    
    # Parámetros base económicos
    capital_cost = config_lcoe.get("capital_cost", 1_000_000)
    fixed_op_cost = config_lcoe.get("fixed_operating_cost", 50_000)
    var_op_cost = config_lcoe.get("variable_operating_cost", 0.01)

    fcr_values_range = np.arange(0.01, 0.11, 0.01)
    lcoes = []

    # Calcular energía base
    pv_model_result = run_single_simulation(
        solar_file=solar_file, capacity_kw=capacity, tilt=tilt, azimuth=azimuth,
        inv_eff=inv_eff, losses=losses, dc_ac_ratio=dc_ac_ratio, gcr=gcr
    )

    if pv_model_result is None:
        print(f"Error: No se pudo calcular energía base para {pais_info['nombre']} en LCOE vs FCR.")
        return {"fcrs": list(fcr_values_range), "lcoes": [np.nan] * len(fcr_values_range), "color": pais_info["color"]}
        
    annual_energy = pv_model_result.Outputs.annual_energy

    for fcr in fcr_values_range:
        lcoe = calculate_lcoe_point(annual_energy, capital_cost, round(fcr, 2), fixed_op_cost, var_op_cost)
        lcoes.append(lcoe)
        
    return {"fcrs": list(fcr_values_range), "lcoes": lcoes, "color": pais_info["color"]}

def get_lcoe_sensitivity_data(pais_info, config_base, sens_ranges):
    """Calcula datos para sensibilidad LCOE para todos los parámetros."""
    results_by_param = {} # {param_name: {values: [], lcoes: []}}
    solar_file = pais_info["archivo"]
    azimuth = 0 if pais_info["nombre"] in ["chile", "australia"] else 180

    # Calcular energía anual base inicial
    pv_model_base = run_single_simulation(
        solar_file=solar_file, 
        capacity_kw=config_base.get("capacity_kw", 1000.0),
        tilt=config_base.get("tilt", 20.0),
        azimuth=azimuth,
        inv_eff=config_base.get("inv_eff", 96),
        losses=config_base.get("losses", 14.0),
        dc_ac_ratio=config_base.get("dc_ac_ratio", 1.2),
        gcr=config_base.get("gcr", 0.4)
    )
    if pv_model_base is None:
        print(f"Error: No se pudo calcular energía base para {pais_info['nombre']} en Sensibilidad LCOE.")
        return {} # Devolver vacío si falla la base
    annual_energy_base = pv_model_base.Outputs.annual_energy

    for param_name, param_range in sens_ranges.items():
        lcoe_values_sens = []
        param_values_used = []

        for param_value in param_range:
            current_config = config_base.copy()
            current_annual_energy = annual_energy_base

            if param_name == "inv_eff":
                # Recalcular energía
                pv_model_temp = run_single_simulation(
                    solar_file=solar_file, 
                    capacity_kw=current_config.get("capacity_kw", 1000.0),
                    tilt=current_config.get("tilt", 20.0),
                    azimuth=azimuth,
                    inv_eff=float(param_value), # <<< Variando este
                    losses=current_config.get("losses", 14.0),
                    dc_ac_ratio=current_config.get("dc_ac_ratio", 1.2),
                    gcr=current_config.get("gcr", 0.4)
                )
                if pv_model_temp is None:
                    lcoe_values_sens.append(np.nan)
                    param_values_used.append(param_value)
                    continue
                current_annual_energy = pv_model_temp.Outputs.annual_energy
                current_config[param_name] = float(param_value)
            elif param_name in current_config:
                 current_config[param_name] = param_value
            elif param_name == 'capital_cost': # Caso especial si no estaba en config_base
                current_config['capital_cost'] = param_value
            else:
                 continue

            lcoe = calculate_lcoe_point(
                current_annual_energy,
                current_config.get("capital_cost", 1_000_000),
                current_config.get("fixed_charge_rate", 0.07),
                current_config.get("fixed_operating_cost", 50_000),
                current_config.get("variable_operating_cost", 0.01)
            )
            lcoe_values_sens.append(lcoe)
            param_values_used.append(param_value)

        results_by_param[param_name] = {"values": param_values_used, "lcoes": lcoe_values_sens}
        
    return results_by_param # Devuelve dict {param_name: {values: [], lcoes: []}} 