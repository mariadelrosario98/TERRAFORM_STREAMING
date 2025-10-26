import polars as pl
import os

INPUT_JSON_FILE = "0013392a-8b51-4640-9314-b81d84e64648.json"
BIG_PARQUET_FILE = "big_logs.parquet"
REPLICATION_FACTOR = 100  
SUCCESS_CODE = "HTTP Status Code: 200"


def prepare_big_parquet_file(input_file: str, output_file: str, factor: int):
        df_original = pl.read_json(input_file)
        print(f"   -> Tamaño original: {len(df_original.estimated_size('rows'))} filas.")
        
        bigger_df = pl.concat([df_original] * factor)
        
        bigger_df.write_parquet(output_file)
        
        print(f"   -> Archivo '{output_file}' creado con {len(bigger_df.estimated_size('rows'))} filas.")
        return True


def calculate_failure_rate_streaming(parquet_file: str):
    # El plan de ejecución Lazy (Streaming)
    q = (
        pl.scan_parquet(parquet_file) 
        .with_columns(
            # 1. Etiquetar como fallo (True si NO es un éxito 200)
            is_failure = pl.col("message").str.contains(SUCCESS_CODE).not_()
        )
        .group_by("service")  # 2. Agrupar por servicio
        .agg(
            # 3. Calcular la Tasa de Fallos (Media de 1s y 0s)
            pl.col("is_failure").mean().alias("failure_rate")
        )
        .sort("failure_rate", descending=True)
    )

    result = q.collect(streaming=True)
    
    print("\n--- Resultado de Tasa de Fallos por Servicio (Streaming) ---")
    print(result)


if __name__ == "__main__":
    
    if prepare_big_parquet_file(INPUT_JSON_FILE, BIG_PARQUET_FILE, REPLICATION_FACTOR):
        calculate_failure_rate_streaming(BIG_PARQUET_FILE)
    