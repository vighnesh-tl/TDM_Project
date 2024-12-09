# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "44fc53cc-3bdb-4863-b936-21909fc51257",
# META       "default_lakehouse_name": "Silver",
# META       "default_lakehouse_workspace_id": "fe4d85d6-cd7f-43cf-9d88-32cec9d8090e"
# META     }
# META   }
# META }

# CELL ********************

# Welcome to your new notebook
# Type here in the cell editor to add code!
from pyspark.sql import SparkSession
from pyspark.sql.functions import col

# Create Spark session
spark = SparkSession.builder \
    .appName("JoinTablesExample") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .getOrCreate()

# Read the masking_results table
masking_results_df = spark.read.format("delta").load("abfss://JumpStart_Project@onelake.dfs.fabric.microsoft.com/Silver.Lakehouse/Tables/masking_results")

# Read the masking_config_results table
masking_config_results_df = spark.read.format("delta").load("abfss://JumpStart_Project@onelake.dfs.fabric.microsoft.com/Silver.Lakehouse/Tables/masking_config_results")

# Perform the join operation on the object_id column
joined_df = masking_results_df.join(masking_config_results_df, on="object_id", how="inner")

# Define the schema for the joined DataFrame (optional, based on your requirements)
# joined_schema = StructType([...])

# Write the joined DataFrame to a new Delta table in the data warehouse
joined_df.write.mode("overwrite").format("delta").save("abfss://JumpStart_Project@onelake.dfs.fabric.microsoft.com/Silver.Lakehouse/Tables/joined_masking_results")

# Show the result
joined_df.show()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
