import polars as pl
from pathlib import Path

# Definir los pares de archivos por ubicación
ubicaciones = {
    'Sudafrica': {
        'lat': -29.19,
        'lon': 21.30,
        'archivos': ['1155731_-29.19_21.30_2018.csv', '1155731_-29.19_21.30_2019.csv']
    },
    'China': {
        'lat': 44.73,
        'lon': 87.66,
        'archivos': ['3480150_44.73_87.66_2018.csv', '3480150_44.73_87.66_2019.csv']
    },
    'Chile': {
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
        
        # Seleccionar solo las columnas necesarias
        columnas_necesarias = ['Year', 'Month', 'Day', 'Hour', 'Minute', 'DNI', 'GHI', 'DHI']
        df = df.select(columnas_necesarias)
        
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
    
    # Guardar el DataFrame en un nuevo archivo CSV
    nombre_archivo = f'datos_{id_ubicacion}.csv'
    df_final.write_csv(nombre_archivo)
    print(f"\nLos datos han sido guardados en '{nombre_archivo}'")

print("\nProcesamiento completado para todas las ubicaciones") 