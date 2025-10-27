import datetime
import json
import pathlib

from src import domain
from src.task_3 import compute


def test_task_3(tmp_path: pathlib.Path) -> None:
    # Crear carpeta temporal simulando el stream
    source = tmp_path / "source"
    source.mkdir(parents=True, exist_ok=True)

    # Tiempo base
    basetime = datetime.datetime.now()

    # Crear archivo con varios eventos
    events = [
        {"service": "api", "timestamp": basetime.timestamp(), "message": "HTTP Status Code: 200"},
        {"service": "auth", "timestamp": basetime.timestamp(), "message": "HTTP Status Code: 404"},
        {"service": "monitoring", "timestamp": basetime.timestamp(), "message": "HTTP Status Code: 500"},
        {"service": "auth", "timestamp": basetime.timestamp(), "message": "HTTP Status Code: 404"},
    ]

    # Guardar archivo JSON
    with open(source / "batch_1.json", "w") as f:
        json.dump(events, f)

    # Ejecutar la función compute()
    generator = compute(str(source), k=10)

    # Obtener el primer resultado del muestreo
    result = next(generator)

    # Validar el tipo y el contenido general
    assert isinstance(result, domain.Result)
    assert result.value in (200.0, 404.0, 500.0)

    # Verificar que las fechas sean razonables
    assert result.newest_considered >= basetime
    assert result.oldest_considered <= datetime.datetime.now()
# ----------------------------------------------
import datetime 