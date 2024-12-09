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
# META       "default_lakehouse_workspace_id": "fe4d85d6-cd7f-43cf-9d88-32cec9d8090e",
# META       "known_lakehouses": [
# META         {
# META           "id": "4af02871-d3fa-46ab-b79d-0635c9fec3a3"
# META         },
# META         {
# META           "id": "8b2de38e-896a-4cd1-8c47-64ca3e0d8d86"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

from pyspark.sql.functions import col
import requests
import json

# Read the JSON data
logs_df = spark.read.option("multiline", "true").json("Files/mask_pass_json.json")

# Collect the necessary information to driver
download_info = logs_df.select("objectID", "Results", "Logs").collect()

# Process files on driver
for row in download_info:
    try:
        # Download config file
        results_response = requests.get(row.Results)
        if results_response.status_code == 200:
            config_data = [(f"{row.objectID}_config.json", results_response.text)]
            spark.createDataFrame(config_data, ["filename", "content"]) \
                .write.mode("append").format("delta").save("abfss://JumpStart_Project@onelake.dfs.fabric.microsoft.com/Bronze.Lakehouse/Files/configs")
        
        # Download log file
        logs_response = requests.get(row.Logs)
        if logs_response.status_code == 200:
            log_data = [(f"{row.objectID}_logs.txt", logs_response.text)]
            spark.createDataFrame(log_data, ["filename", "content"]) \
                .write.mode("append").format("delta").save("abfss://JumpStart_Project@onelake.dfs.fabric.microsoft.com/Bronze.Lakehouse/Files/logs")
            
        print(f"Successfully processed files for objectID: {row.objectID}")
    except Exception as e:
        print(f"Failed to process files for objectID {row.objectID}: {str(e)}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

from pyspark.sql.functions import col
from pyspark.sql.types import StructType, StructField, StringType, TimestampType
import requests
import json
from datetime import datetime

# Read the JSON data
logs_df = spark.read.option("multiline", "true").json("Files/mask_pass_json.json")

# Define schema for the output DataFrame
schema = StructType([
    StructField("object_id", StringType(), True),
    StructField("config", StringType(), True),
    StructField("masking_log", StringType(), True),
    StructField("load_date", TimestampType(), True)
])

# Collect the necessary information to driver
download_info = logs_df.select("objectID", "Results", "Logs").collect()

# Process files on driver
records = []
for row in download_info:
    try:
        # Download both files
        results_response = requests.get(row.Results)
        logs_response = requests.get(row.Logs)
        
        if results_response.status_code == 200 and logs_response.status_code == 200:
            records.append({
                "object_id": row.objectID,
                "config": results_response.text,
                "masking_log": logs_response.text,
                "load_date": datetime.now()
            })
            print(f"Successfully processed files for objectID: {row.objectID}")
    except Exception as e:
        print(f"Failed to process files for objectID {row.objectID}: {str(e)}")

# Create and write the combined DataFrame
if records:
    combined_df = spark.createDataFrame(records, schema)
    combined_df.write.mode("append").format("delta").save("abfss://JumpStart_Project@onelake.dfs.fabric.microsoft.com/Bronze.Lakehouse/Tables/masking_data")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

masking_df = spark.read.format("delta").load("abfss://JumpStart_Project@onelake.dfs.fabric.microsoft.com/Bronze.Lakehouse/Tables/masking_data")

display(masking_df)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
