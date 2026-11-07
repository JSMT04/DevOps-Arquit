import logging
import sqlite3
import pandas as pd

# Configuración de logging para observabilidad de datos (Pilar: Volumen y Calidad)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("pipeline_ventas")


def extraer(ruta: str) -> pd.DataFrame:
    """
    Lee el archivo CSV crudo y lo carga en un DataFrame de pandas.
    """
    logger.info(f"Iniciando extracción desde: {ruta}")
    df = pd.read_csv(ruta)
    logger.info(f"Extracción completada. Filas crudas leídas: {len(df)}")
    return df


def transformar(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica las reglas de negocio, limpieza y calidad de datos:
    1. Preserva el DataFrame original creando una copia independiente.
    2. Elimina nulos en 'id_venta' y 'monto'.
    3. Elimina duplicados basándose en 'id_venta'.
    4. Convierte 'fecha' y 'monto' de manera segura (descartando valores no parseables).
    5. Descarta registros con fecha en el futuro respecto a la fecha actual.
    6. Filtra y conserva únicamente los registros con montos estrictamente positivos (> 0).
    """
    df = df.copy(deep=True)
    filas_iniciales = len(df)
    logger.info(f"Iniciando transformación. Registros entrantes: {filas_iniciales}")

    # 1. Eliminación de nulos iniciales en id_venta y monto
    df = df.dropna(subset=["id_venta", "monto"])

    # 2. Eliminación de duplicados basados en id_venta
    df = df.drop_duplicates(subset="id_venta").copy()

    # 3. Conversión segura de fecha y monto, eliminando no parseables
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    df["monto"] = pd.to_numeric(df["monto"], errors="coerce")
    df = df.dropna(subset=["fecha", "monto"])

    # 4. Descarte de fechas futuras
    ahora = pd.Timestamp.now()
    df = df[df["fecha"] <= ahora]

    # 5. Filtrado de montos estrictamente positivos
    df["monto"] = df["monto"].astype(float)
    df = df[df["monto"] > 0]

    filas_finales = len(df)
    filas_descartadas = filas_iniciales - filas_finales
    logger.info(
        f"Transformación finalizada. Filas válidas: {filas_finales} | Filas descartadas: {filas_descartadas}"
    )
    return df


def cargar(df: pd.DataFrame, ruta_db: str) -> None:
    """
    Guarda el DataFrame transformado en una base de datos SQLite de forma idempotente,
    reemplazando la tabla 'ventas' si ya existe y sin almacenar el índice.
    """
    logger.info(f"Cargando {len(df)} registros en la base de datos: {ruta_db}")
    with sqlite3.connect(ruta_db) as con:
        df.to_sql("ventas", con, if_exists="replace", index=False)
    logger.info("Carga completada exitosamente de forma idempotente.")


if __name__ == "__main__":
    datos_crudos = extraer("data/ventas.csv")
    datos_limpios = transformar(datos_crudos)
    cargar(datos_limpios, "ventas.db")
    logger.info(
        f"MÉTRICA DE OBSERVABILIDAD - Filas leídas: {len(datos_crudos)} | Filas cargadas: {len(datos_limpios)}"
    )
