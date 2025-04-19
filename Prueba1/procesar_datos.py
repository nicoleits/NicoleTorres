import polars as pl
from pathlib import Path

# Definir los pares de archivos por ubicación
ubicaciones = {
    '1504375': {
        'lat': -26.11,
        'lon': 27.50,
        'archivos': ['1504375_-26.11_27.50_2018.csv', '1504375_-26.11_27.50_2019.csv']
    },
    '4046597': {
        'lat': -0.96,
        'lon': 115.07,
        'archivos': ['4046597_-0.96_115.07_2018.csv', '4046597_-0.96_115.07_2019.csv']
    },
    '5815755': {
        'lat': -23.84,
        'lon': -69.89,
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
        
        # Agregar columnas de ubicación
        df = df.with_columns([
            pl.lit(id_ubicacion).alias('Location_ID'),
            pl.lit(info['lat']).alias('Latitude'),
            pl.lit(info['lon']).alias('Longitude')
        ])
        
        # Agregar el DataFrame a la lista
        dfs.append(df)
    
    # Combinar los DataFrames de los dos años
    df_final = pl.concat(dfs)
    
    # Ordenar por fecha y hora
    df_final = df_final.sort(['Year', 'Month', 'Day', 'Hour', 'Minute'])
    
    # Mostrar las primeras filas del DataFrame
    print(f"\nPrimeras filas del DataFrame para ubicación {id_ubicacion}:")
    print(df_final.head())
    
    # Mostrar información básica del DataFrame
    print(f"\nInformación del DataFrame para ubicación {id_ubicacion}:")
    print(df_final.describe())
    
    # Crear directorio para los resultados si no existe
    Path('resultados').mkdir(exist_ok=True)
    
    # Guardar el DataFrame en un nuevo archivo CSV
    nombre_archivo = f'resultados/datos_{id_ubicacion}.csv'
    df_final.write_csv(nombre_archivo)
    print(f"\nLos datos han sido guardados en '{nombre_archivo}'")

print("\nProcesamiento completado para todas las ubicaciones") 