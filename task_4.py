import pathlib
import json
import time
import hashlib
import datetime
import re
from bitarray import bitarray
from src import domain


class BloomFilter:
    """Bloom Filter básico, inicializado con patrones de error dinámicos."""

    def __init__(self, size: int = 100000, hash_count: int = 5):
        self.size = size
        self.hash_count = hash_count
        self.bit_array = bitarray(size)
        self.bit_array.setall(False)

    def _hashes(self, item: str):
        """Genera múltiples hashes para un elemento."""
        for i in range(self.hash_count):
            digest = hashlib.sha256((item + str(i)).encode("utf-8")).hexdigest()
            yield int(digest, 16) % self.size

    def add(self, item: str):
        for index in self._hashes(item):
            self.bit_array[index] = True

    def __contains__(self, item: str):
        return all(self.bit_array[index] for index in self._hashes(item))


def load_dynamic_bloom_filter() -> BloomFilter:
    """
    Crea un Bloom Filter con patrones representativos de errores HTTP.
    Esto permite cubrir 4xx, 5xx y errores comunes sin lista externa.
    """
    bf = BloomFilter(size=100000, hash_count=5)

    # Cargar patrones representativos de errores HTTP y del sistema
    interest_messages = [
        "HTTP Status Code: 400", "HTTP Status Code: 401", "HTTP Status Code: 403",
        "HTTP Status Code: 404", "HTTP Status Code: 408", "HTTP Status Code: 429",
        "HTTP Status Code: 500", "HTTP Status Code: 502", "HTTP Status Code: 503",
        "HTTP Status Code: 504", "Database Error", "Connection refused", "Timeout Error"
    ]
    for msg in interest_messages:
        bf.add(msg)

    print(f"📦 Bloom Filter dinámico cargado con {len(interest_messages)} patrones de error.\n")
    return bf


def is_http_error(message: str) -> bool:
    """
    Detecta dinámicamente si el mensaje contiene un error HTTP 4xx o 5xx.
    """
    match = re.search(r"HTTP Status Code:\s*(\d{3})", message)
    if match:
        code = int(match.group(1))
        return 400 <= code < 600
    return False


def compute(source: str, max_batches: int | None = None):
    """
    Filtra mensajes de error y genera resultados en modo streaming.
    Si max_batches está definido, el procesamiento se detiene tras esa cantidad de archivos (modo test).
    """
    bloom = load_dynamic_bloom_filter()
    processed_files = set()

    total_events = 0
    detected_events = 0
    start_time = time.time()

    while True:
        new_files = [f for f in pathlib.Path(source).glob("*.json") if f.name not in processed_files]
        if not new_files:
            time.sleep(1)
            continue

        for file in new_files:
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    events = data if isinstance(data, list) else [data]
            except Exception as e:
                print(f"⚠️ Error leyendo {file}: {e}")
                continue

            for event in events:
                total_events += 1
                message = event.get("message", "")
                ts = event.get("timestamp", time.time())
                now = datetime.datetime.fromtimestamp(ts)

                # Detectar dinámicamente errores o coincidencias del Bloom Filter
                if message in bloom or is_http_error(message):
                    detected_events += 1
                    avg_detection = detected_events / total_events
                    yield domain.Result(
                        value=avg_detection,
                        newest_considered=now,
                        oldest_considered=now,
                    )
                    print(f"✅ #{detected_events} | {message} | Promedio: {round(avg_detection*100, 2)}%")

            processed_files.add(file.name)

        # Modo test: detener el bucle si se alcanzó el número de lotes
        if max_batches and len(processed_files) >= max_batches:
            break

        # Métricas en tiempo real (solo cuando no es test)
        elapsed = time.time() - start_time
        if total_events > 0 and not max_batches:
            ratio = detected_events / total_events
            print(f"📊 Tiempo: {round(elapsed, 1)}s | Total: {total_events} | Detectados: {detected_events} | Ratio: {round(ratio*100, 2)}%")

        time.sleep(1)


# --- Ejecución directa ---
if __name__ == "__main__":
    log_dir = r"C:\Users\Santiago\Documents\EAFIT\Grandes Volumenes de Datos\Taller_5_streaming\data"

    print(f"🔍 Monitoreando logs en tiempo real desde: {log_dir}\n")

    for result in compute(log_dir):
        pass  # Los prints ya muestran la información en tiempo real
