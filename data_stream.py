import logging
import json
from pyspark.sql import SparkSession
from pyspark.sql.types import *
import pyspark.sql.functions as psf

# Create a schema for incoming resources
schema = StructType([
    StructField("crime_id", StringType(), True),
    StructField("original_crime_type_name", StringType(), True),
    StructField("report_date", TimestampType(), True),
    StructField("call_date", TimestampType(), True),
    StructField("offense_date", TimestampType(), True),
    StructField("call_time", StringType(), True),
    StructField("call_date_time", TimestampType(), True),
    StructField("disposition", StringType(), True),
    StructField("address", StringType(), True),
    StructField("city", StringType(), True),
    StructField("state", StringType(), True),
    StructField("agency_id", StringType(), True),
    StructField("address_type", StringType(), True),
    StructField("common_location", StringType(), True),
])


def run_spark_job(spark):
    # Create Spark configurations with max offset of 200 per trigger
    # set up correct bootstrap server and port
    df = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "localhost:9092") \
        .option("subscribe", "police-dept-calls") \
        .option("startingOffsets", "earliest") \
        .option("maxOffsetsPerTrigger", 200) \
        .load()

    # Show schema for the incoming resources for checks
    df.printSchema()

    # Take only value and convert it to String
    kafka_df = df.selectExpr("CAST(value AS STRING)")

    service_table = kafka_df \
        .select(psf.from_json(psf.col('value'), schema).alias("DF")) \
        .select("DF.*")

    # Select report_date, original_crime_type_name, disposition
    # We need report_date for windowing
    reported_crime_table = service_table.select("original_crime_type_name", "report_date", "disposition")

    # count the number of crimes of each type reported in a window (2 minutes in this example)
    crimes_count_per_window_df = reported_crime_table \
        .withWatermark("report_date", "5 minutes") \
        .groupBy("original_crime_type_name",
                 psf.window("report_date", "2 minutes")) \
        .count()

    # write output stream
    query = crimes_count_per_window_df \
        .writeStream \
        .format("console") \
        .outputMode("update") \
        .option("truncate", "false") \
        .start()

    # attach a ProgressReporter
    query.awaitTermination()

    # get the right radio code json path
    radio_code_json_filepath = "/home/workspace/radio_code.json"
    radio_code_df = spark.read.json(radio_code_json_filepath)

    # rename disposition_code column to disposition
    radio_code_df = radio_code_df.withColumnRenamed("disposition_code", "disposition")

    # join on disposition column
    join_query = reported_crime_table \
        .join(radio_code_df, "disposition", "inner") \
        .writeStream \
        .format("console") \
        .outputMode("update") \
        .option("truncate", "false") \
        .start()

    join_query.awaitTermination()


if __name__ == "__main__":
    logger = logging.getLogger(__name__)

    # TODO Create Spark in Standalone mode
    spark = SparkSession \
        .builder \
        .master("local[*]") \
        .appName("KafkaSparkStructuredStreaming") \
        .config("spark.executor.cores", "4") \
        .config("spark.dynamicAllocation.enabled", "true") \
        .config("spark.driver.memory", "8g") \
        .config("spark.executor.memory", "8g") \
        .getOrCreate()

    logger.info("Spark started")

    run_spark_job(spark)

    spark.stop()
