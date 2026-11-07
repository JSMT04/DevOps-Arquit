import logging
import sqlite3
import pandas as pd
import pytest
from etl import extraer, transformar, cargar


def test_sin_duplicados_ni_nulos_en_id_venta():
    """Valida que no existan duplicados ni nulos en id_venta tras la transformación."""
    df_crudo = pd.DataFrame({
        "id_venta": [1, 2, 2, None, 3],
        "fecha": ["2026-01-01"] * 5,
        "monto": [100.0, 200.0, 200.0, 300.0, 400.0],
    })
    resultado = transformar(df_crudo)
    assert resultado["id_venta"].is_unique, "Existen identificadores duplicados en id_venta"
    assert resultado["id_venta"].notna().all(), "Existen valores nulos en id_venta"
    assert set(resultado["id_venta"]) == {1, 2, 3}


def test_todos_los_montos_son_positivos():
    """Valida que todos los montos finales sean estrictamente mayores a 0."""
    df_crudo = pd.DataFrame({
        "id_venta": [1, 2, 3],
        "fecha": ["2026-01-01"] * 3,
        "monto": [150.5, 0.0, -45.0],
    })
    resultado = transformar(df_crudo)
    assert (resultado["monto"] > 0).all(), "Existen montos menores o iguales a 0"
    assert len(resultado) == 1
    assert resultado.iloc[0]["id_venta"] == 1


def test_sin_fechas_futuras():
    """Valida que los registros con fechas futuras sean rechazados."""
    fecha_futura = (pd.Timestamp.now() + pd.Timedelta(days=30)).strftime("%Y-%m-%d")
    df_crudo = pd.DataFrame({
        "id_venta": [1, 2],
        "fecha": ["2026-01-01", fecha_futura],
        "monto": [100.0, 200.0],
    })
    resultado = transformar(df_crudo)
    assert (resultado["fecha"] <= pd.Timestamp.now()).all(), "Existen registros con fecha futura"
    assert len(resultado) == 1
    assert resultado.iloc[0]["id_venta"] == 1


def test_descarta_montos_cero_y_negativos():
    """Valida que montos iguales a cero o negativos sean descartados explícitamente."""
    df_crudo = pd.DataFrame({
        "id_venta": [1, 2, 3, 4],
        "fecha": ["2026-01-01"] * 4,
        "monto": [0, -100, -0.01, 50],
    })
    resultado = transformar(df_crudo)
    assert len(resultado) == 1
    assert resultado.iloc[0]["monto"] == 50.0


def test_descarta_fechas_invalidas_y_montos_no_numericos():
    """Valida que fechas no parseables o montos alfanuméricos se descarten."""
    df_crudo = pd.DataFrame({
        "id_venta": [1, 2, 3, 4],
        "fecha": ["2026-01-01", "fecha_invalida", "2026-01-02", "2026-01-03"],
        "monto": ["100.0", "50.0", "monto_invalido", "75.5"],
    })
    resultado = transformar(df_crudo)
    assert len(resultado) == 2
    assert set(resultado["id_venta"]) == {1, 4}


def test_convierte_fecha_y_monto_a_tipos_correctos():
    """Valida el casteo de tipos a datetime para fecha y float para monto."""
    df_crudo = pd.DataFrame({
        "id_venta": [1],
        "fecha": ["2026-01-05"],
        "monto": ["120.75"],
    })
    resultado = transformar(df_crudo)
    assert pd.api.types.is_datetime64_any_dtype(resultado["fecha"])
    assert pd.api.types.is_float_dtype(resultado["monto"])


def test_transformar_no_modifica_dataframe_original():
    """Garantiza la inmutabilidad del DataFrame original al procesarse."""
    df_crudo = pd.DataFrame({
        "id_venta": [1, 1, None],
        "fecha": ["2026-01-05"] * 3,
        "monto": ["100.5", "-20", "50"],
    })
    df_original = df_crudo.copy(deep=True)
    _ = transformar(df_crudo)
    pd.testing.assert_frame_equal(df_crudo, df_original)


def test_registra_conteo_de_filas_en_log(caplog):
    """Verifica que el logger registre métricas de volumen para observabilidad."""
    with caplog.at_level(logging.INFO):
        df_crudo = pd.DataFrame({
            "id_venta": [1, 2],
            "fecha": ["2026-01-01", "2026-01-02"],
            "monto": [10.0, 20.0],
        })
        transformar(df_crudo)
        assert any("Filas" in record.message for record in caplog.records)


def test_extraer_lee_csv(tmp_path):
    """Valida que la función extraer lea correctamente un archivo CSV."""
    csv_file = tmp_path / "test_ventas.csv"
    csv_file.write_text("id_venta,fecha,monto\n1,2026-01-01,50.0\n", encoding="utf-8")
    df = extraer(str(csv_file))
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == ["id_venta", "fecha", "monto"]
    assert len(df) == 1


def test_cargar_reemplaza_tabla_y_no_guarda_indice(tmp_path):
    """Valida que cargar sea idempotente (reemplace la tabla) y no incluya columna de índice."""
    db_path = str(tmp_path / "test_ventas.db")
    df1 = pd.DataFrame({
        "id_venta": [1, 2],
        "fecha": [pd.Timestamp("2026-01-01"), pd.Timestamp("2026-01-02")],
        "monto": [100.0, 200.0],
    })
    cargar(df1, db_path)

    # Carga de reemplazo para probar idempotencia
    df2 = pd.DataFrame({
        "id_venta": [3],
        "fecha": [pd.Timestamp("2026-01-03")],
        "monto": [300.0],
    })
    cargar(df2, db_path)

    with sqlite3.connect(db_path) as con:
        columnas = [row[1] for row in con.execute("PRAGMA table_info(ventas)").fetchall()]
        df_db = pd.read_sql("SELECT * FROM ventas", con)

    assert "index" not in columnas
    assert "level_0" not in columnas
    assert columnas == ["id_venta", "fecha", "monto"]
    assert len(df_db) == 1
    assert df_db.iloc[0]["id_venta"] == 3
