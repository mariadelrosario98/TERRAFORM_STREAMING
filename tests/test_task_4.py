import datetime
import json
import pathlib

from src import domain
from src.task_4 import compute


def test_task_4(tmp_path: pathlib.Path) -> None:
    """
    Test para verificar que el sistema de filtrado con Bloom Filter
    detecta correctamente mensajes de error HTTP (4xx/5xx) y otros eventos críticos,
    y que genera resultados tipo streaming en tiempo real.
    """

    # Crear carpeta temporal simulando el stream de logs
    source = tmp_path / "source"
    source.mkdir(parents=True, exist_ok=True)

    # Tiempo base para los timestamps
    basetime = datetime.datetime.now()

    # Crear archivo con eventos mixtos (normales y de error)
    events = [
        {"service": "api", "timestamp": basetime.timestamp(), "message": "HTTP Status Code: 200"},
        {"service": "auth", "timestamp": basetime.timestamp(), "message": "HTTP Status Code: 404"},
        {"service": "monitoring", "timestamp": basetime.timestamp(), "message": "HTTP Status Code: 500"},
        {"service": "db", "timestamp": basetime.timestamp(), "message": "Database Error"},
        {"service": "auth", "timestamp": basetime.timestamp(), "message": "HTTP Status Code: 401"},
        {"service": "frontend", "timestamp": basetime.timestamp(), "message": "User login successful"},
    ]

    # Guardar archivo JSON simulado
    with open(source / "batch_1.json", "w") as f:
        json.dump(events, f)

    # Ejecutar la función compute() en modo test (solo 1 batch)
    generator = compute(str(source), max_batches=1)

    # Obtener el primer resultado del generador
    result = next(generator)

    # --- Validaciones básicas ---
    assert isinstance(result, domain.Result), "El resultado debe ser una instancia de domain.Result"
    assert isinstance(result.value, float), "El valor debe ser numérico (float)"
    assert 0.0 <= result.value <= 1.0, "El valor debe representar un promedio entre 0 y 1"

    # Validar coherencia temporal
    assert isinstance(result.newest_considered, datetime.datetime)
    assert isinstance(result.oldest_considered, datetime.datetime)
    assert result.newest_considered >= basetime
    assert result.oldest_considered <= datetime.datetime.now()

    # --- Verificar detecciones múltiples ---
    detections = 1  # ya obtuvimos la primera
    for _ in range(10):
        try:
            r = next(generator)
            if isinstance(r, domain.Result):
                detections += 1
        except StopIteration:
            break

    # Se esperan al menos 3 detecciones (404, 500, 401, Database Error)
    assert detections >= 3, f"Se esperaban >=3 detecciones, pero hubo {detections}"

    print(f"✅ Test completado correctamente: {detections} detecciones encontradas.")
