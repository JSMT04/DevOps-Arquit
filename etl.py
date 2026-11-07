import sqlite3
import pandas as pd


def extraer(ruta: str) -> pd.DataFrame:
    """
    Lee el archivo CSV crudo y lo carga en un DataFrame de pandas.
    """
    return pd.read_csv(ruta)


def transformar(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica las reglas de negocio y limpieza de datos:
    1. Elimina registros con valores nulos en 'id_venta' o 'monto'.
    2. Elimina duplicados basándose en 'id_venta'.
    3. Convierte la columna 'fecha' a formato datetime.
    4. Convierte la columna 'monto' a tipo numérico float.
    5. Filtra y conserva únicamente los registros con montos estrictamente positivos (> 0).
    """
    df = df.dropna(subset=["id_venta", "monto"])
    df = df.drop_duplicates(subset="id_venta").copy()
    df["fecha"] = pd.to_datetime(df["fecha"])
    df["monto"] = df["monto"].astype(float)
    return df[df["monto"] > 0]


def cargar(df: pd.DataFrame, ruta_db: str) -> None:
    """
    Guarda el DataFrame transformado en una base de datos SQLite de forma idempotente,
    reemplazando la tabla 'ventas' si ya existe y sin almacenar el índice.
    """
    with sqlite3.connect(ruta_db) as con:
        df.to_sql("ventas", con, if_exists="replace", index=False)


if __name__ == "__main__":
    datos_crudos = extraer("data/ventas.csv")
    datos_limpios = transformar(datos_crudos)
    cargar(datos_limpios, "ventas.db")
    print(f"Pipeline ejecutado exitosamente. Filas cargadas: {len(datos_limpios)}")

