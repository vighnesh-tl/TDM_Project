# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "4af02871-d3fa-46ab-b79d-0635c9fec3a3",
# META       "default_lakehouse_name": "Landing",
# META       "default_lakehouse_workspace_id": "fe4d85d6-cd7f-43cf-9d88-32cec9d8090e"
# META     }
# META   }
# META }

# MARKDOWN ********************

# Landing to Bronze Conversion

# CELL ********************

# Step 1: Import necessary libraries
from pyspark.sql import SparkSession

# Step 2: Initialize SparkSession
spark = SparkSession.builder.appName("Lakehouse to Bronze").getOrCreate()

# Step 3: Read data from the Lakehouse table
input_table_path = "abfss://JumpStart_Project@onelake.dfs.fabric.microsoft.com/Landing.Lakehouse/Tables/TL_Consulting_Generate_Lead"
df = spark.read.format("delta").load(input_table_path)

# Step 4: Define the Bronze path where you want to save the Parquet file
bronze_path = "abfss://JumpStart_Project@onelake.dfs.fabric.microsoft.com/Bronze.Lakehouse/Files"  # Customize the path to your needs

# Step 5: Write data to the Bronze folder in Parquet format
df.write.mode("overwrite").parquet(f"abfss://JumpStart_Project@onelake.dfs.fabric.microsoft.com/Bronze.Lakehouse/Files/TL")

print("Data successfully written to Bronze in Parquet format.")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
