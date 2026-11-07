import pandas as pd
from etl import transformar


def datos_crudos() -> pd.DataFrame:
    """
    Genera un conjunto de datos crudo con casos de prueba:
    - Duplicados en id_venta
    - Nulos en id_venta y monto
    - Montos negativos
    """
    return pd.DataFrame({
        "id_venta": [1, 2, 2, None],
        "fecha": ["2026-01-05"] * 4,
        "monto": ["100.5", "-20", "-20", "50"],
    })


def test_sin_duplicados_ni_nulos():
    """
    Valida que tras la transformación no existan duplicados ni nulos en id_venta.
    """
    df = transformar(datos_crudos())
    assert df["id_venta"].is_unique, "Existen identificadores duplicados en id_venta"
    assert df["id_venta"].notna().all(), "Existen valores nulos en id_venta"


def test_montos_positivos():
    """
    Valida que tras la transformación todos los montos sean estrictamente positivos (> 0).
    """
    df = transformar(datos_crudos())
    assert (df["monto"] > 0).all(), "Existen montos menores o iguales a cero"

