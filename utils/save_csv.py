import csv
import os
from datetime import datetime


# Canonical column order that matches the keys produced by scrap() in main.py
FIELDNAMES = [
    "Codigo Materia",
    "Materia",
    "Tipo",
    "Paralelo",
    "Profesor",
    "Cupo Maximo",
    "Cupo Disponible",
    "Planificada Quincenalmente",
    "Examen Parcial",
    "Aula Examen Parcial",
    "Examen Final",
    "Aula Examen Final",
    "Mejoramiento",
    "Aula Mejoramiento",
    "Paralelos Asociados",
    "Dia",
    "Hora Inicio",
    "Hora Fin",
    "Aula",
    "Bloque",
]


def save_csv(
    list_of_subjects: list,
    output_path: str = None,
    encoding: str = "utf-8-sig",
) -> str:
    """Export *list_of_subjects* to a CSV file.

    Parameters
    ----------
    list_of_subjects:
        The list of subject dictionaries collected by ``scrap()`` in main.py.
    output_path:
        Destination file path.  When *None* a timestamped file is created in
        the current working directory (e.g. ``subjects_20260529_123045.csv``).
    encoding:
        File encoding.  Defaults to ``utf-8-sig`` so that Excel opens the
        file correctly without needing an explicit import step.

    Returns
    -------
    str
        The absolute path of the file that was written.
    """
    if not list_of_subjects:
        raise ValueError("list_of_subjects is empty – nothing to export.")

    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(os.getcwd(), f"subjects_{timestamp}.csv")

    output_path = os.path.abspath(output_path)

    with open(output_path, mode="w", newline="", encoding=encoding) as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=FIELDNAMES,
            extrasaction="ignore",   # silently skip any unexpected keys
        )
        writer.writeheader()
        writer.writerows(list_of_subjects)

    print(f"[save_csv] Exported {len(list_of_subjects)} rows → {output_path}")
    return output_path
