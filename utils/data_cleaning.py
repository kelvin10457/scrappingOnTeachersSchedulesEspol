import pandas as pd
import numpy as np
import warnings


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

    # ── 6. Mapear `codigo_materia` a `nivel` usando la malla curricular ───────
    # Si la materia no existe en `malla_curricular`, `.map()` devuelve NaN.
    # Avisamos y reemplazamos esos NaN por 'SIN NIVEL' para mantener consistencia.
    malla_curricular = {
    # NIVEL 100 - I
    'MATG1045': 'NIVEL 100 - I',
    'FISG1005': 'NIVEL 100 - I',
    'QUIG1032': 'NIVEL 100 - I',
    'INDG1033': 'NIVEL 100 - I',
    'IDIG1006': 'NIVEL 100 - I',

    # NIVEL 100 - II
    'MATG1049': 'NIVEL 100 - II',
    'MATG1046': 'NIVEL 100 - II',
    'FISG1006': 'NIVEL 100 - II',
    'CCPG1043': 'NIVEL 100 - II',
    'IDIG1007': 'NIVEL 100 - II',

    # NIVEL 200 - I
    'MATG1050': 'NIVEL 200 - I',
    'IDIG2012': 'NIVEL 200 - I',
    'ESTG1034': 'NIVEL 200 - I',
    'ELEG1030': 'NIVEL 200 - I',
    'EYAG1044': 'NIVEL 200 - I',
    'IDIG1008': 'NIVEL 200 - I',

    # NIVEL 200 - II
    'MATG1052': 'NIVEL 200 - II',
    'EYAG1040': 'NIVEL 200 - II',
    'ELEG1028': 'NIVEL 200 - II',
    'EYAG1043': 'NIVEL 200 - II',
    'ELEG1051': 'NIVEL 200 - II',
    'IDIG1009': 'NIVEL 200 - II',

    # NIVEL 300 - I
    'ADMG1005': 'NIVEL 300 - I',
    'ELEG1049': 'NIVEL 300 - I',
    'ELEG1038': 'NIVEL 300 - I',
    'ELEG1040': 'NIVEL 300 - I',
    'IDIG1010': 'NIVEL 300 - I',

    # NIVEL 300 - II
    'EYAG1035': 'NIVEL 300 - II',
    'ELEG1050': 'NIVEL 300 - II',
    'ELEG1041': 'NIVEL 300 - II',
    'ADSG1026': 'NIVEL 300 - II',

    # NIVEL 400 - I
    'MATG1054': 'NIVEL 400 - I',
    'ELEG1044': 'NIVEL 400 - I',
    'ELEG1032': 'NIVEL 400 - I',
    'ELEG1035': 'NIVEL 400 - I',
    'ELEG1029': 'NIVEL 400 - I',
    'ELEG1031': 'NIVEL 400 - I',

    # NIVEL 400 - II
    'ELEG1047': 'NIVEL 400 - II',
    'ELEG1046': 'NIVEL 400 - II',
    'ELEG1033': 'NIVEL 400 - II',
    'ELEG1036': 'NIVEL 400 - II',
    'ELEG1039': 'NIVEL 400 - II',

    # NIVEL 500 - I
    'ELEG1037': 'NIVEL 500 - I',
    'ELEG1042': 'NIVEL 500 - I',
}

    if "codigo_materia" in df.columns:
        df["nivel"] = df["codigo_materia"].map(malla_curricular)
        unmapped = df.loc[df["nivel"].isna(), "codigo_materia"].dropna().unique()
        if len(unmapped) > 0:
            sample = list(unmapped[:10])
            warnings.warn(
                f"{len(unmapped)} códigos de `codigo_materia` no están en malla_curricular. "
                f"Ejemplos: {sample}. Se rellenará 'SIN NIVEL' en esos casos."
            )
        df["nivel"] = df["nivel"].fillna("SIN NIVEL")
    else:
        # No existe la columna esperada; creamos `nivel` con valor por defecto.
        df["nivel"] = "SIN NIVEL"

    return df
