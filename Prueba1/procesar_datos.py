import polars as pl
from pathlib import Path

# Definir los pares de archivos por ubicación
ubicaciones = {
    'Sudafrica': {
        'lat': -29.19,
        'lon': 21.30,
        'elev': 0,  # Elevación por defecto
        'tz': 2,    # Zona horaria por defecto
        'archivos': ['1155731_-29.19_21.30_2018.csv', '1155731_-29.19_21.30_2019.csv']
    },
    'China': {
        'lat': 44.73,
        'lon': 87.66,
        'elev': 0,
        'tz': 8,
        'archivos': ['3480150_44.73_87.66_2018.csv', '3480150_44.73_87.66_2019.csv']
    },
    'Chile': {
        'lat': -23.84,
        'lon': -69.89,
        'elev': 735,  # Elevación real de Chile
        'tz': -4,
        'archivos': ['5815755_-23.84_-69.89_2018.csv', '5815755_-23.84_-69.89_2019.csv']
    }
}

# Procesar cada ubicación
for id_ubicacion, info in ubicaciones.items():
    print(f"\nProcesando ubicación {id_ubicacion} ({info['lat']}, {info['lon']})")
    
    # Lista para almacenar los DataFrames de cada año
    dfs = []
    
    # Procesar cada archivo de la ubicación
    for archivo in info['archivos']:
        # Leer el archivo CSV, saltando las primeras 2 filas que contienen metadatos
        df = pl.read_csv(archivo, skip_rows=2)
        
        # Seleccionar y renombrar las columnas necesarias
        df = df.select([
            pl.col('Year'),
            pl.col('Month'),
            pl.col('Day'),
            pl.col('Hour'),
            pl.col('Minute'),
            pl.col('DNI'),
            pl.col('GHI'),
            pl.col('DHI'),
            pl.col('Temperature'),
            pl.col('Wind Speed'),
            pl.col('Pressure'),
            pl.col('Relative Humidity')
        ])
        
        # Agregar el DataFrame a la lista
        dfs.append(df)
    
    # Combinar los DataFrames de los dos años
    df_final = pl.concat(dfs)
    
    # Ordenar por fecha y hora
    df_final = df_final.sort(['Year', 'Month', 'Day', 'Hour', 'Minute'])
    
    # Crear el archivo de salida con el formato PySAM
    nombre_archivo = f'datos_{id_ubicacion}.csv'
    
    # Escribir los metadatos y los datos en un solo paso
    with open(nombre_archivo, 'w') as f:
        # Escribir metadatos
        f.write(f"Latitude,{info['lat']}\n")
        f.write(f"Longitude,{info['lon']}\n")
        f.write(f"Time Zone,{info['tz']}\n")
        f.write(f"Elevation,{info['elev']}\n")
        
        # Escribir encabezados y datos
        df_final.write_csv(f)
    
    print(f"\nLos datos han sido guardados en '{nombre_archivo}' en formato PySAM")

print("\nProcesamiento completado para todas las ubicaciones") 