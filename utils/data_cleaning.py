import pandas as pd
import numpy as np


def _split_exam_column(df: pd.DataFrame, column_name: str, suffix: str) -> pd.DataFrame:
    """Divide una columna de examen en fecha, hora inicio y hora fin.

    Los valores originales tienen la forma::

        "2026-08-12 - 08:00 A 10:00"

    Se generan tres columnas nuevas:
        * ``fecha_examen_{suffix}``
        * ``inicio_examen_{suffix}``
        * ``fin_examen_{suffix}``

    La columna original NO se elimina aquí; eso lo hace :func:`clean_dataframe`.
    """
    # Normalizar nulos textuales que quedaron tras el str.upper() previo
    temp_col = df[column_name].astype(str).replace(["NAN", "NONE", ""], np.nan)

    # Separar "fecha" de "rango horario" por el separador " - "
    parts = temp_col.str.split(" - ", expand=True)
    df[f"fecha_examen_{suffix}"] = parts[0]

    if 1 in parts.columns:
        times = parts[1].str.split(" A ", expand=True)
        df[f"inicio_examen_{suffix}"] = times[0]
        df[f"fin_examen_{suffix}"] = times[1] if 1 in times.columns else np.nan
    else:
        df[f"inicio_examen_{suffix}"] = np.nan
        df[f"fin_examen_{suffix}"] = np.nan

    return df


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica las reglas de limpieza definidas en el análisis de cruces de horarios.

    Pasos que se ejecutan, en orden:

    1. **Normalización de strings** – todas las columnas de tipo ``object`` se
       convierten a mayúsculas y se les elimina el espacio en blanco sobrante.
    2. **Normalización de horas de clase** – ``Hora Inicio`` y ``Hora Fin`` se
       parsean como ``datetime.time`` con formato ``%H:%M:%S``.
    3. **Descomposición de columnas de examen** – ``Examen Parcial``,
       ``Examen Final`` y ``Mejoramiento`` se dividen en fecha, hora inicio y
       hora fin (tres columnas nuevas por cada una).
    4. **Eliminación de columnas originales de examen** – las tres columnas
       originales se descartan una vez que se han expandido.
    5. **Normalización de nombres de columnas** – todos los nombres pasan a
       minúsculas con guiones bajos en lugar de espacios.

    Parameters
    ----------
    df:
        DataFrame crudo producido por ``scrap()`` en ``main.py``.

    Returns
    -------
    pd.DataFrame
        DataFrame limpio listo para exportar.
    """
    df = df.copy()

    # ── 1. Normalizar strings ──────────────────────────────────────────────────
    columnas_object = df.select_dtypes(include=["object"]).columns
    for col in columnas_object:
        df[col] = df[col].astype(str).str.strip().str.upper()

    # ── 2. Normalizar horas de clase ───────────────────────────────────────────
    df["Hora Inicio"] = pd.to_datetime(df["Hora Inicio"], format="%H:%M:%S").dt.time
    df["Hora Fin"] = pd.to_datetime(df["Hora Fin"], format="%H:%M:%S").dt.time

    # ── 3. Descomponer columnas de examen ──────────────────────────────────────
    df = _split_exam_column(df, "Examen Parcial", "parcial")
    df = _split_exam_column(df, "Examen Final", "final")
    df = _split_exam_column(df, "Mejoramiento", "mejoramiento")

    # ── 4. Eliminar columnas originales de examen ──────────────────────────────
    columnas_a_eliminar = [
        "EXAMEN PARCIAL", "EXAMEN FINAL", "MEJORAMIENTO",
        "Examen Parcial", "Examen Final", "Mejoramiento",
    ]
    df = df.drop(columns=[c for c in columnas_a_eliminar if c in df.columns])

    # ── 5. Normalizar nombres de columnas ──────────────────────────────────────
    df.columns = [col.lower().replace(" ", "_") for col in df.columns]

    return df
