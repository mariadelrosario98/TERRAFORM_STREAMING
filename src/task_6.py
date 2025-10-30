from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, window, count, avg
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, LongType

# ==============================
# 1️⃣ Configuración de SparkSession
# ==============================
spark = (
    SparkSession.builder.appName("StructuredStreamingJSONLogs")
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    .config("spark.hadoop.fs.s3a.aws.credentials.provider", "com.amazonaws.auth.DefaultAWSCredentialsProviderChain")
    .config("spark.hadoop.fs.s3a.endpoint", "s3.us-east-1.amazonaws.com")
    .config("spark.sql.shuffle.partitions", "4")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

# ==============================
# 2️⃣ Esquema de los logs JSON
# ==============================
schema = StructType([
    StructField("service", StringType(), True),
    StructField("timestamp", DoubleType(), True),
    StructField("message", StringType(), True),
    StructField("response_time_ms", LongType(), True)
])

# ==============================
# 3️⃣ Lectura desde S3 (modo streaming)
# ==============================
input_path = "s3a://streaming-json-7436f3c559d99abb/logs/"

# Cada nuevo JSON será tratado como parte del stream
df_raw = (
    spark.readStream
    .schema(schema)
    .json(input_path)
)

# ==============================
# 4️⃣ Procesamiento: filtrar errores y calcular métricas
# ==============================
df_errors = (
    df_raw.filter(col("message").rlike("HTTP Status Code: (4|5)\\d{2}"))
)

# Ventana de tiempo de 1 minuto para contar errores por servicio
df_agg = (
    df_errors
    .withColumn("event_time", (col("timestamp") / 1000).cast("timestamp"))
    .groupBy(
        window(col("event_time"), "60 seconds"),
        col("service")
    )
    .agg(
        count("*").alias("error_count"),
        avg("response_time_ms").alias("avg_response_time_ms")
    )
)

# ==============================
# 5️⃣ Salida: consola (para debug)
# ==============================
query = (
    df_agg.writeStream
    .outputMode("update")
    .format("console")
    .option("truncate", "false")
    .trigger(processingTime="30 seconds")
    .start()
)

query.awaitTermination()
