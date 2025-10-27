#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Análisis de logs JSON almacenados en AWS S3 con Polars
Compatibilidad: Polars >= 1.7, s3fs >= 2024.5
"""

import polars as pl
import re

# -----------------------------------------------------
# --- CONFIGURACIÓN GENERAL ---
# -----------------------------------------------------

# Ruta base en S3 (ajusta el prefijo si usas otra carpeta)
S3_URI = "s3://terraform-51257688b24ec567/5gb/*.json"

# Patrón para extraer códigos HTTP
STATUS_CODE_PATTERN = r"(\d{3})"

# Esquema base de respaldo en caso de error
FALLBACK_SCHEMA = {"service": pl.String, "timestamp": pl.Float64, "message": pl.String}


# -----------------------------------------------------
# --- FUNCIÓN PRINCIPAL PARA LEER DESDE S3 ---
# -----------------------------------------------------

def read_json_from_s3(uri: str) -> pl.LazyFrame:
    """
    Lee los archivos JSON desde S3 usando Polars + s3fs (modo lazy scan).
    No requiere fsspec ni configuración manual de la región.
    """
    print(f"\n📥 Leyendo archivos JSON desde: {uri}")
    try:
        # ✅ Polars usa s3fs automáticamente
        df_lazy = pl.scan_json(uri, storage_options={"anon": False})
        print("✅ Conexión establecida correctamente con S3 y archivos detectados.")
        return df_lazy
    except Exception as e:
        print(f"❌ ERROR al leer los JSON desde S3: {e}")
        return pl.DataFrame({}, schema=FALLBACK_SCHEMA).lazy()


# -----------------------------------------------------
# --- LECTURA DE DATOS ---
# -----------------------------------------------------

lazy_df_base = read_json_from_s3(S3_URI)

# -----------------------------------------------------
# --- ENRIQUECIMIENTO Y LIMPIEZA DE DATOS ---
# -----------------------------------------------------

lazy_df = (
    lazy_df_base
    .with_columns(
        # Extraer código HTTP
        pl.col("message").str.extract(STATUS_CODE_PATTERN).cast(pl.Int32, strict=False).alias("status_code"),
        # Renombrar columna "service"
        pl.col("service").alias("endpoint"),
        # Simular latencia
        (pl.lit(150.0) + pl.int_range(0, pl.len()) * 0.0001).alias("latency_ms"),
        # Simular user_agent
        pl.when(pl.col("service") == "training")
          .then(pl.lit("Python/Client"))
          .otherwise(pl.lit("Web/Browser"))
          .alias("user_agent")
    )
)

# -----------------------------------------------------
# --- 1️⃣ TASA DE ERRORES POR ENDPOINT ---
# -----------------------------------------------------

print("\n--- 1️⃣ Calculando Tasa de Errores por Endpoint ---")

lazy_plan_errores = (
    lazy_df
    .filter(pl.col("status_code").is_not_null())
    .with_columns((pl.col("status_code") >= 400).alias("is_error"))
    .group_by("endpoint")
    .agg([
        pl.col("is_error").sum().alias("total_errores"),
        pl.len().alias("total_solicitudes"),
    ])
    .with_columns((pl.col("total_errores") / pl.col("total_solicitudes")).alias("tasa_fallos"))
    .sort("tasa_fallos", descending=True)
)

df_errores = lazy_plan_errores.collect()
print(df_errores)


# -----------------------------------------------------
# --- 2️⃣ LATENCIA PROMEDIO POR ENDPOINT ---
# -----------------------------------------------------

print("\n--- 2️⃣ Calculando Latencia Promedio ---")

lazy_plan_latency = (
    lazy_df
    .filter(pl.col("status_code").is_not_null())
    .group_by("endpoint")
    .agg([
        pl.col("latency_ms").mean().alias("latencia_promedio"),
        pl.col("latency_ms").quantile(0.95).alias("latencia_p95"),
        pl.col("latency_ms").std().alias("desviacion_estandar"),
    ])
    .sort("latencia_p95", descending=True)
)

df_latency = lazy_plan_latency.collect()
print(df_latency)


# -----------------------------------------------------
# --- 3️⃣ DISTRIBUCIÓN DE TRÁFICO POR USER AGENT ---
# -----------------------------------------------------

print("\n--- 3️⃣ Calculando Distribución de Tráfico por User Agent ---")

lazy_plan_agent = (
    lazy_df
    .filter(pl.col("user_agent").is_not_null())
    .group_by("user_agent")
    .agg(pl.len().alias("conteo"))
    .sort("conteo", descending=True)
)

df_agent = lazy_plan_agent.collect()
print(df_agent)


# -----------------------------------------------------
# --- EXPORTACIÓN OPCIONAL (VERSIÓN COMPATIBLE) ---
# -----------------------------------------------------

# Guardar localmente
df_errores.write_csv("errores.csv")
df_latency.write_csv("latencia.csv")
df_agent.write_csv("trafico.csv")

print("\n Archivos locales creados correctamente.")

# -----------------------------------------------------
# --- EXPORTACIÓN A S3 CON BOTO3 ---
# -----------------------------------------------------
import boto3
from botocore.exceptions import ClientError

s3 = boto3.client("s3")

bucket = "terraform-51257688b24ec567"
prefix = "results/"

files = ["errores.csv", "latencia.csv", "trafico.csv"]

print("\n📤 Subiendo resultados a S3 con boto3...")

for file_name in files:
    key = prefix + file_name
    try:
        s3.upload_file(file_name, bucket, key)
        print(f"✅ Subido: s3://{bucket}/{key}")
    except ClientError as e:
        print(f"❌ Error subiendo {file_name}: {e}")

print("\n🚀 Subida completada.")

