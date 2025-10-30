import os
import json
import tempfile
from pyspark.sql import SparkSession
from pyspark.sql.functions import col

# =========================================================
# 🧱 Crear un entorno de prueba temporal
# =========================================================
def create_test_data(base_path):
    """Crea algunos JSON simulados con diferentes códigos HTTP"""
    os.makedirs(base_path, exist_ok=True)
    data = [
        {"service": "auth", "timestamp": 1730000000000, "message": "HTTP Status Code: 200", "response_time_ms": 120},
        {"service": "auth", "timestamp": 1730000060000, "message": "HTTP Status Code: 500", "response_time_ms": 240},
        {"service": "api", "timestamp": 1730000120000, "message": "HTTP Status Code: 404", "response_time_ms": 180},
        {"service": "api", "timestamp": 1730000180000, "message": "HTTP Status Code: 200", "response_time_ms": 130},
        {"service": "analytics", "timestamp": 1730000240000, "message": "HTTP Status Code: 503", "response_time_ms": 300},
    ]
    file_path = os.path.join(base_path, "batch_1.json")
    with open(file_path, "w") as f:
        json.dump(data, f)
    return file_path


# =========================================================
# 🚀 Test principal
# =========================================================
def test_spark_task6():
    # 1. Crear una sesión de Spark local
    spark = (
        SparkSession.builder.appName("TestSparkTask6")
        .master("local[2]")
        .config("spark.sql.shuffle.partitions", "2")
        .getOrCreate()
    )   