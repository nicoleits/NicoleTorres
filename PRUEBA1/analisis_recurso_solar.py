"""
Script para analizar archivos CSV de recurso solar (GHI, DHI, DNI)
para diferentes ubicaciones y generar gráficos resumen.
Lee archivos desde la carpeta ../Datos y guarda resultados en ../Resultados_Recurso_Solar.
"""
import polars as pl
import matplotlib.pyplot as plt
import os
import traceback # Para imprimir errores detallados

# --- Definición de Rutas y Ubicaciones ---

# Obtener el directorio del script de forma segura
try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
except NameError:
    # Si __file__ no está definido (ej. ejecución interactiva no estándar), usar CWD
    script_dir = os.getcwd()

# Asumiendo que este script está en PRUEBA1
datos_dir = os.path.abspath(os.path.join(script_dir, "Datos"))
# Directorio base para guardar resultados (se creará si no existe)
resultados_dir_base = os.path.abspath(os.path.join(script_dir, "graficos/recurso_solar"))
os.makedirs(resultados_dir_base, exist_ok=True)

print(f"Directorio del Script: {script_dir}")
print(f"Directorio de Datos: {datos_dir}")
print(f"Directorio Base de Resultados: {resultados_dir_base}")


# Definir las ubicaciones y sus archivos de datos únicos de la carpeta Datos
# (Excluyendo Antofagasta según solicitud)
# Ahora solo especificamos el archivo, los metadatos se leerán del CSV.
ubicaciones = {
    'Chile': {
        'archivo': os.path.join(datos_dir, 'chile.csv') # Usar el original
    },
    'Espana': {
        'archivo': os.path.join(datos_dir, 'espana.csv')
    },
    'Australia': {
        'archivo': os.path.join(datos_dir, 'australia.csv')
    }
    # Antofagasta excluida
}

# --- Funciones de Análisis y Gráficos ---

def analizar_estadisticas(df):
    """Calcula estadísticas descriptivas para columnas numéricas clave."""
    columnas_numericas = ['GHI', 'DHI', 'DNI', 'Temperature', 'Wind Speed']
    # Filtrar para incluir solo columnas numéricas que existen en el df
    columnas_a_describir = [col for col in columnas_numericas if col in df.columns and df[col].dtype in pl.NUMERIC_DTYPES]
    
    if not columnas_a_describir:
        print("  Advertencia: No se encontraron columnas numéricas adecuadas para estadísticas descriptivas.")
        return None
        
    print("  Calculando estadísticas descriptivas...")
    try:
        # Usar describe() para obtener estadísticas básicas
        stats_df = df.select(columnas_a_describir).describe(
             percentiles=[0.25, 0.5, 0.75]
        )
        return stats_df
    except Exception as e:
        print(f"  Error calculando estadísticas descriptivas: {e}")
        return None

def detectar_outliers_iqr(df, columna, factor_iqr=1.5):
    """Detecta outliers en una columna usando el método IQR."""
    if columna not in df.columns or df[columna].dtype not in pl.NUMERIC_DTYPES:
        return 0, 0, 0, None, None # Devolver ceros y None si la columna no es válida
        
    try:
        q1 = df[columna].quantile(0.25)
        q3 = df[columna].quantile(0.75)
        iqr = q3 - q1
        
        if iqr is None or q1 is None or q3 is None:
             print(f"  Advertencia: No se pudo calcular IQR para {columna} (posiblemente todos los valores son iguales o nulos).")
             return 0, 0, 0, None, None

        limite_inferior = q1 - factor_iqr * iqr
        limite_superior = q3 + factor_iqr * iqr
        
        # Contar outliers
        outliers_df = df.filter(
            (pl.col(columna) < limite_inferior) | (pl.col(columna) > limite_superior)
        )
        count_outliers = outliers_df.height
        
        # Calcular porcentaje
        total_validos = df[columna].is_not_null().sum()
        if total_validos > 0:
            porcentaje_outliers = (count_outliers / total_validos) * 100
        else:
            porcentaje_outliers = 0.0
            
        return count_outliers, porcentaje_outliers, total_validos, limite_inferior, limite_superior
        
    except Exception as e:
        print(f"  Error detectando outliers para {columna}: {e}")
        return 0, 0, df[columna].is_not_null().sum(), None, None # Devolver ceros pero intentar contar válidos

def resumen_outliers(df):
    """Genera un resumen de outliers para columnas numéricas clave."""
    print("  Detectando outliers (método IQR)...")
    columnas_numericas = ['GHI', 'DHI', 'DNI', 'Temperature', 'Wind Speed']
    resumen = {}
    for col in columnas_numericas:
        if col in df.columns:
             count, percent, total_validos, lim_inf, lim_sup = detectar_outliers_iqr(df, col)
             if total_validos > 0: # Solo reportar si hubo datos válidos para analizar
                 resumen[col] = {
                     'count': count,
                     'percentage': percent,
                     'lower_bound': lim_inf,
                     'upper_bound': lim_sup,
                     'total_valid': total_validos
                 }
             else:
                  print(f"  Columna {col} no tenía datos válidos para análisis de outliers.")
        else:
             print(f"  Advertencia: Columna {col} no encontrada para análisis de outliers.")
             
    return resumen

def analizar_irradiacion_anual(df):
    """Analiza la irradiación anual por tipo"""
    resultados = {}
    for col_name in ['GHI', 'DHI', 'DNI']:
        if col_name in df.columns:
            try:
                df_col = df.select(pl.col(col_name).cast(pl.Float64, strict=False).fill_null(0.0))
                resultados[col_name] = {
                    'promedio': float(df_col.mean()[0,0] or 0.0),
                    'maximo': float(df_col.max()[0,0] or 0.0),
                    'minimo': float(df_col.min()[0,0] or 0.0),
                    'total': float(df_col.sum()[0,0] or 0.0)
                }
            except Exception as e:
                print(f"  Error al procesar columna anual {col_name}: {e}")
                resultados[col_name] = {'promedio': 0.0, 'maximo': 0.0, 'minimo': 0.0, 'total': 0.0}
        else:
            print(f"  Advertencia: Columna {col_name} no encontrada para análisis anual.")
            resultados[col_name] = {'promedio': 0.0, 'maximo': 0.0, 'minimo': 0.0, 'total': 0.0}
    return resultados

def analizar_irradiacion_mensual(df):
    """Analiza la irradiación mensual"""
    if 'Month' not in df.columns:
        print("  Error: Columna 'Month' no encontrada para análisis mensual.")
        return pl.DataFrame()

    agg_exprs = []
    columnas_irradiacion = ['GHI', 'DHI', 'DNI']
    columnas_presentes = [col for col in columnas_irradiacion if col in df.columns]

    if not columnas_presentes:
         print("  Error: No hay columnas de irradiación (GHI, DHI, DNI) disponibles para análisis mensual.")
         return pl.DataFrame()

    for col_name in columnas_presentes:
        agg_exprs.append(pl.col(col_name).cast(pl.Float64, strict=False).fill_null(0.0).mean().alias(f'{col_name}_promedio'))

    try:
        mensual = df.group_by('Month').agg(agg_exprs).sort('Month')
        meses_completos = pl.DataFrame({'Month': range(1, 13)})
        mensual_completo = meses_completos.join(mensual, on='Month', how='left').fill_null(0.0)
    except Exception as e:
        print(f"  Error durante la agregación mensual: {e}")
        return pl.DataFrame()

    return mensual_completo

def crear_graficos(df, resultados_dir_ubicacion, resultados_anuales, resultados_mensuales, ubicacion):
    """Crea los gráficos de análisis para una ubicación específica"""
    os.makedirs(resultados_dir_ubicacion, exist_ok=True)
    print(f"  Guardando gráficos para {ubicacion} en '{resultados_dir_ubicacion}'.")

    # --- Gráfico Mensual ---
    if not resultados_mensuales.is_empty() and resultados_mensuales.height == 12:
        plt.figure(figsize=(12, 6))
        meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
                 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
        plot_legend_mensual = False
        if 'GHI_promedio' in resultados_mensuales.columns and resultados_mensuales['GHI_promedio'].sum() > 0:
            plt.plot(meses, resultados_mensuales['GHI_promedio'], label='GHI', marker='o')
            plot_legend_mensual = True
        if 'DHI_promedio' in resultados_mensuales.columns and resultados_mensuales['DHI_promedio'].sum() > 0:
             plt.plot(meses, resultados_mensuales['DHI_promedio'], label='DHI', marker='s')
             plot_legend_mensual = True
        if 'DNI_promedio' in resultados_mensuales.columns and resultados_mensuales['DNI_promedio'].sum() > 0:
            plt.plot(meses, resultados_mensuales['DNI_promedio'], label='DNI', marker='^')
            plot_legend_mensual = True

        plt.xlabel('Mes')
        plt.ylabel('Irradiancia Promedio (W/m²)')
        plt.title(f'Irradiancia Promedio Mensual en {ubicacion}')
        if plot_legend_mensual:
             plt.legend()
        else:
             plt.text(0.5, 0.5, 'No hay datos de irradiación válidos para mostrar',
                      horizontalalignment='center', verticalalignment='center',
                      transform=plt.gca().transAxes, fontsize=12, color='red')
        plt.grid(True)
        plt.tight_layout()
        try:
            plt.savefig(os.path.join(resultados_dir_ubicacion, f'irradiacion_mensual_{ubicacion}.png'))
            print(f"    Gráfico mensual guardado.")
        except Exception as e:
            print(f"    Error al guardar gráfico mensual: {e}")
        plt.close()
    else:
        print(f"  No se generó gráfico mensual para {ubicacion} (datos mensuales vacíos o incompletos: {resultados_mensuales.height} filas).")

    # --- Gráfico Horario ---
    if 'Hour' not in df.columns:
        print(f"  Advertencia: Columna 'Hour' no encontrada. No se puede generar gráfico horario para {ubicacion}.")
        return

    agg_exprs_horaria = []
    columnas_irradiacion = ['GHI', 'DHI', 'DNI']
    columnas_presentes_hr = [col for col in columnas_irradiacion if col in df.columns]

    if not columnas_presentes_hr:
        print(f"  Advertencia: No hay columnas de irradiación para gráfico horario de {ubicacion}.")
        return

    for col_name in columnas_presentes_hr:
        agg_exprs_horaria.append(pl.col(col_name).cast(pl.Float64, strict=False).fill_null(0.0).mean().alias(f'{col_name}_promedio'))

    try:
        horaria = df.group_by('Hour').agg(agg_exprs_horaria).sort('Hour')

        if not horaria.is_empty():
            plt.figure(figsize=(12, 6))
            horas = range(24)
            horas_df = pl.DataFrame({'Hour': range(24)})
            horaria_completa = horas_df.join(horaria, on='Hour', how='left').fill_null(0.0)

            plot_legend_horaria = False
            if 'GHI_promedio' in horaria_completa.columns and horaria_completa['GHI_promedio'].sum() > 0:
                plt.plot(horas, horaria_completa['GHI_promedio'], label='GHI', marker='o')
                plot_legend_horaria = True
            if 'DHI_promedio' in horaria_completa.columns and horaria_completa['DHI_promedio'].sum() > 0:
                 plt.plot(horas, horaria_completa['DHI_promedio'], label='DHI', marker='s')
                 plot_legend_horaria = True
            if 'DNI_promedio' in horaria_completa.columns and horaria_completa['DNI_promedio'].sum() > 0:
                plt.plot(horas, horaria_completa['DNI_promedio'], label='DNI', marker='^')
                plot_legend_horaria = True

            plt.xticks(range(0, 24, 1))
            plt.gca().set_xticklabels([f'{h:02d}:00' for h in range(24)])
            plt.xlabel('Hora del día (24h)')
            plt.ylabel('Irradiancia Promedio (W/m²)')
            plt.title(f'Distribución Horaria de la Irradiancia en {ubicacion}')
            if plot_legend_horaria:
                plt.legend()
            else:
                 plt.text(0.5, 0.5, 'No hay datos de irradiación válidos para mostrar',
                      horizontalalignment='center', verticalalignment='center',
                      transform=plt.gca().transAxes, fontsize=12, color='red')
            plt.grid(True)
            plt.tight_layout()
            try:
                plt.savefig(os.path.join(resultados_dir_ubicacion, f'distribucion_horaria_{ubicacion}.png'))
                print(f"    Gráfico horario guardado.")
            except Exception as e:
                print(f"    Error al guardar gráfico horario: {e}")
            plt.close()
        else:
             print(f"  No se generó gráfico horario para {ubicacion} (datos horarios vacíos).")

    except Exception as e:
        print(f"  Error durante la agregación horaria o graficación para {ubicacion}: {e}")

# --- Bloque Principal de Ejecución ---

def main():
    print("\n--- Iniciando Análisis de Recurso Solar ---")
    resultados_generales = {}
    
    # Directorio específico para el archivo TXT de resumen
    resultados_txt_dir = os.path.abspath(os.path.join(script_dir, "Resultados"))
    os.makedirs(resultados_txt_dir, exist_ok=True) # Crear si no existe
    
    # Definir el nombre del archivo de texto para el resumen completo
    archivo_resumen_txt = os.path.join(resultados_txt_dir, "analisis_estadistico_completo.txt")

    # Abrir el archivo de texto en modo escritura (sobrescribirá si existe)
    try:
        with open(archivo_resumen_txt, 'w', encoding='utf-8') as f_resumen:
            f_resumen.write("=== RESUMEN DE ANÁLISIS ESTADÍSTICO Y DE ANOMALÍAS ===\n\n")

            for nombre_ubicacion, datos_ubicacion in ubicaciones.items():
                print(f"\nProcesando ubicación: {nombre_ubicacion}")
                # Escribir encabezado de ubicación en el archivo de resumen
                f_resumen.write(f"=== {nombre_ubicacion} ===\n")
                archivo_csv = datos_ubicacion['archivo']
                lat, lon, elev, tz = None, None, None, None # Inicializar metadatos

                if not os.path.exists(archivo_csv):
                    print(f"  Error: Archivo no encontrado -> {archivo_csv}")
                    f_resumen.write(f"  Error: Archivo no encontrado -> {archivo_csv}\n\n")
                    continue

                try:
                    # --- Leer Metadatos --- 
                    print(f"  Leyendo metadatos de: {archivo_csv}")
                    with open(archivo_csv, 'r', encoding='utf-8') as f:
                        header_names_line = f.readline().strip()
                        header_values_line = f.readline().strip()
                    header_names = [h.strip() for h in header_names_line.split(',')] 
                    header_values = [v.strip() for v in header_values_line.split(',')] 
                    metadata_dict = dict(zip(header_names, header_values))
                    try:
                        lat = float(metadata_dict.get('Latitude', None))
                    except (TypeError, ValueError): pass
                    try:
                         lon = float(metadata_dict.get('Longitude', None))
                    except (TypeError, ValueError): pass
                    try:
                         elev = float(metadata_dict.get('Elevation', None))
                    except (TypeError, ValueError): pass
                    try:
                         tz = int(metadata_dict.get('Local Time Zone', None))
                    except (TypeError, ValueError): pass

                    print(f"  Metadatos extraídos: Lat={lat}, Lon={lon}, Elev={elev}, TZ={tz}")
                    f_resumen.write(f"  Archivo: {os.path.basename(archivo_csv)}\n")
                    f_resumen.write(f"  Metadatos: Lat={lat}, Lon={lon}, Elev={elev}, TZ={tz}\n")
                    datos_ubicacion['lat'] = lat
                    datos_ubicacion['lon'] = lon
                    datos_ubicacion['elev'] = elev
                    datos_ubicacion['tz'] = tz
                    # ----------------------------------------------------

                    # --- Leer Datos --- 
                    print(f"  Leyendo datos de: {archivo_csv}")
                    df = pl.read_csv(archivo_csv, skip_rows=2, infer_schema_length=10000, null_values=['NA', '', 'NULL'])
                    print(f"  Archivo leído. Columnas detectadas: {df.columns}")
                    print(f"  Número inicial de filas: {df.height}")
                    f_resumen.write(f"  Filas de datos leídas: {df.height}\n")

                    # --- Corrección Chile --- 
                    if nombre_ubicacion == 'Chile':
                        print("  Aplicando corrección específica para Chile (añadir Wind Speed y reordenar)...")
                        target_columns_chile = [
                            'Year', 'Month', 'Day', 'Hour', 'Minute',
                            'Temperature', 'DHI', 'GHI', 'Wind Direction', 'Wind Speed',
                            'DNI', 'Relative Humidity', 'Pressure', 'Solar Zenith Angle',
                            'Precipitable Water'
                        ]
                        if 'Wind Speed' not in df.columns:
                            print("    Columna 'Wind Speed' no encontrada. Intentando leerla por posición (índice 10).")
                            try:
                                df_wind = pl.read_csv(archivo_csv, skip_rows=2, has_header=False, use_cols=[10], new_columns=['Wind Speed'])
                                df = df.with_row_count()
                                df_wind = df_wind.with_row_count()
                                df = df.join(df_wind, on="row_nr").drop("row_nr")
                                print("    Columna 'Wind Speed' añadida.")
                            except Exception as wind_err:
                                print(f"    *** Error: No se pudo leer/añadir la columna 'Wind Speed' por posición: {wind_err} ***")
                        cols_existentes_para_chile = [col for col in target_columns_chile if col in df.columns]
                        if set(cols_existentes_para_chile) != set(target_columns_chile):
                            print(f"    Advertencia: Columnas finales para Chile después de corrección: {cols_existentes_para_chile}")
                        if not cols_existentes_para_chile:
                             print("    Error Crítico: No quedan columnas válidas para Chile después de la corrección.")
                             f_resumen.write("    Error Crítico: No quedan columnas válidas para Chile después de la corrección.\n\n")
                             continue
                        df = df.select(cols_existentes_para_chile)
                        print(f"    Columnas reordenadas para Chile: {df.columns}")
                    # --------------------------

                    # --- Análisis Estadístico y Anomalías --- 
                    estadisticas = analizar_estadisticas(df)
                    if estadisticas is not None:
                        print("\n  Estadísticas Descriptivas:")
                        print(estadisticas)
                        f_resumen.write("\n  Estadísticas Descriptivas:\n")
                        f_resumen.write(str(estadisticas) + "\n") # Convertir DataFrame a string
                    else:
                         f_resumen.write("\n  No se pudieron calcular estadísticas descriptivas.\n")
                    
                    resumen_anomalias = resumen_outliers(df)
                    if resumen_anomalias:
                        print("\n  Resumen de Anomalías (Outliers por IQR):")
                        f_resumen.write("\n  Resumen de Anomalías (Outliers por IQR):\n")
                        for col, data in resumen_anomalias.items():
                            linea_outlier = f"    {col}: {data['count']} outliers ({data['percentage']:.2f}%) [Límites: {data.get('lower_bound', 'N/A'):.2f} - {data.get('upper_bound', 'N/A'):.2f}] de {data['total_valid']} válidos"
                            print(linea_outlier)
                            f_resumen.write(linea_outlier + "\n")
                    else:
                         f_resumen.write("\n  No se detectaron outliers o no se pudo realizar el análisis.\n")
                    # ---------------------------------------------

                    # --- Análisis Irradiación y Gráficos --- 
                    print("\n  Realizando análisis de irradiación anual...")
                    resultados_anuales = analizar_irradiacion_anual(df)
                    print("  Realizando análisis de irradiación mensual...")
                    resultados_mensuales = analizar_irradiacion_mensual(df)

                    resultados_generales[nombre_ubicacion] = {
                        'metadata': datos_ubicacion,
                        'stats': estadisticas.to_dict(as_series=False) if estadisticas is not None else None, 
                        'outliers': resumen_anomalias,
                        'anual': resultados_anuales,
                        'mensual_df_polars': resultados_mensuales # Guardar el DF por si acaso
                    }

                    resultados_dir_ubicacion = os.path.join(resultados_dir_base, nombre_ubicacion)
                    print("\n  Creando gráficos...")
                    crear_graficos(df, resultados_dir_ubicacion, resultados_anuales, resultados_mensuales, nombre_ubicacion)
                    
                    print("\n  Resumen Anual Irradiación:")
                    f_resumen.write("\n  Resumen Anual Irradiación:\n")
                    for tipo, valores in resultados_anuales.items():
                         if valores: 
                             linea_anual = f"    {tipo}: Promedio={valores['promedio']:.2f}, Max={valores['maximo']:.2f}, Min={valores['minimo']:.2f}, Total={valores['total']:.0f} Wh/m² (aprox)"
                             print(linea_anual)
                             f_resumen.write(linea_anual + "\n")
                    # ---------------------------------------------

                except Exception as e:
                    print(f"*** Error procesando {nombre_ubicacion} ***")
                    print(f"  Archivo: {archivo_csv}")
                    print(f"  Error: {e}")
                    traceback.print_exc()
                    f_resumen.write(f"\n*** Error procesando {nombre_ubicacion}: {e} ***\n")
                
                # Separador entre ubicaciones en el archivo de texto
                f_resumen.write("\n" + "="*70 + "\n\n") 

            print(f"\n--- Análisis Completado --- Resumen guardado en: {archivo_resumen_txt}")

    except IOError as e:
         print(f"Error: No se pudo abrir o escribir en el archivo de resumen: {archivo_resumen_txt}")
         print(e)

    # ... (resto del código, if __name__ == '__main__': main()) ...

if __name__ == "__main__":
    main() 