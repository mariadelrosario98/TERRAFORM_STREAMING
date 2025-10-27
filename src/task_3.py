import datetime
import json
import pathlib
import random
import time
from collections import Counter
from src import domain  # ✅ Import correcto para pytest y ejecución directa


def _extract_status_code(message: str) -> int | None:
    """Extrae el código HTTP del mensaje."""
    if "HTTP Status Code:" in message:
        try:
            return int(message.split(":")[1].strip())
        except ValueError:
            return None
    return None


def compute(source: str, k: int = 1000):
    """Aplica Reservoir Sampling para encontrar el código HTTP más común."""
    reservoir = []
    total_seen = 0
    oldest_timestamp = datetime.datetime.now()
    processed_files = set()

    while True:
        for file in pathlib.Path(source).glob("*.json"):
            if file.name in processed_files:
                continue

            print(f"🔍 Detectado archivo: {file}")  # 👈 Diagnóstico visible

            try:
                with open(file, "r") as f:
                    data = json.load(f)
                    events = data if isinstance(data, list) else [data]
            except Exception as e:
                print(f"⚠️ Error leyendo {file}: {e}")
                continue

            for event in events:
                message = event.get("message", "")
                timestamp = datetime.datetime.fromtimestamp(
                    event.get("timestamp", time.time())
                )
                code = _extract_status_code(message)
                if code is None:
                    continue

                total_seen += 1
                if len(reservoir) < k:
                    reservoir.append(code)
                else:
                    j = random.randint(0, total_seen - 1)
                    if j < k:
                        reservoir[j] = code

                counter = Counter(reservoir)
                most_common_code, _ = counter.most_common(1)[0]

                yield domain.Result(
                    value=float(most_common_code),
                    newest_considered=timestamp,
                    oldest_considered=oldest_timestamp,
                )

            processed_files.add(file.name)

        time.sleep(1)


# --- Ejecución directa ---
if __name__ == "__main__":
    # ⚙️ Ruta absoluta para evitar errores
    log_dir = pathlib.Path(
        r"C:\Users\Santiago\Documents\EAFIT\Grandes Volumenes de Datos\Taller_5_streaming\data"
    )
    print(f"📡 Leyendo archivos desde: {log_dir}\n")

    ultimo_valor = None
    for result in compute(str(log_dir)):
        codigo_actual = int(result.value)
        if codigo_actual != ultimo_valor:
            print(f"✅ Código HTTP más común: {codigo_actual}")
            ultimo_valor = codigo_actual
# ------------------------------------------------- qué hacer para cuando hay más eventos > k 
# ---------------------------------------------- un threaed en un Q y otro thread que lea el Q y procese
