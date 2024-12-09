# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "8b2de38e-896a-4cd1-8c47-64ca3e0d8d86",
# META       "default_lakehouse_name": "Bronze",
# META       "default_lakehouse_workspace_id": "fe4d85d6-cd7f-43cf-9d88-32cec9d8090e",
# META       "known_lakehouses": [
# META         {
# META           "id": "8b2de38e-896a-4cd1-8c47-64ca3e0d8d86"
# META         },
# META         {
# META           "id": "44fc53cc-3bdb-4863-b936-21909fc51257"
# META         }
# META       ]
# META     }
# META   }
# META }

# MARKDOWN ********************

# # Flattening the Log text data to a dataframe

# CELL ********************

# MAGIC %%sql
# MAGIC 
# MAGIC select * from masking_data;

# METADATA ********************

# META {
# META   "language": "sparksql",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# MAGIC %%sql
# MAGIC 
# MAGIC Drop table Silver.cycles;

# METADATA ********************

# META {
# META   "language": "sparksql",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# MAGIC %%sql 
# MAGIC 
# MAGIC select * from Silver.cycles;
# MAGIC 
# MAGIC 


# METADATA ********************

# META {
# META   "language": "sparksql",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************


# MARKDOWN ********************


# MARKDOWN ********************

# ## Working Version


# CELL ********************

from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, IntegerType, StringType, FloatType
import pandas as pd
from datetime import datetime
import re

# Create Spark session and read data
spark = SparkSession.builder \
    .appName("DeltaTableExample") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .getOrCreate()

df = spark.read.format("delta").load("abfss://JumpStart_Project@onelake.dfs.fabric.microsoft.com/Bronze.Lakehouse/Tables/masking_data")

# Convert Spark DataFrame to Pandas DataFrame for easier manipulation
pdf = df.toPandas()

# Function to parse EACH log line one by one
def parse_log_line(line):
    parts = line.split("::", 1)
    if len(parts) == 2:
        timestamp_str, message = parts
        try:
            timestamp = datetime.strptime(timestamp_str.strip(), "%d/%m/%Y %H:%M:%S")
            return timestamp, message.strip()
        except ValueError:
            return None, None
    else:
        return line, None

# Calculate Duration in Seconds for each Column
def calculate_duration(start_time, end_time):
    if start_time is not None and end_time is not None:
        duration_sec = (end_time - start_time).total_seconds()
    else:
        duration_sec = None
    return duration_sec

def log_analytics_from_df(pdf):
    mask_operations = []

    for index, row in pdf.iterrows():
        object_id = row['object_id']
        masking_log = row['masking_log']
        
        current_rows = None
        current_distinct_rows = None
        current_schema = None
        current_table = None
        current_column = None
        live_column = False
        start_time = None
        end_time = None
        cycle_num = None
        duration_sec = None
        duration_min = None
        status = None
        error = None
        column_failures = []
        post_mask_operations = False

        lines = masking_log.split('\n')
        for line_num, line in enumerate(lines):
            timestamp, message = parse_log_line(line)

            if timestamp is not None and message is not None:
                timestamp = datetime.strptime(str(timestamp), "%Y-%m-%d %H:%M:%S")
                message_array = message.split()

                if "MASKING" in message and "HAS" in message and "STARTED" in message:
                    cycle_num = 1

                if "CONNECTED" in message and "Schema:" in message:
                    current_schema = message_array[4]

                if "TABLE" in message and "Mask Started" in message:
                    current_table = message_array[2]

                if "COLUMN" in message and "Mask Started" in message:
                    if post_mask_operations:
                        current_column = None
                    current_column = message_array[2]
                    live_column = True
                    start_time = timestamp

                if "CALCULATED" in message and "Row" in message and "Count" and "for" in message and "=" in message:
                    current_rows = message_array[8]

                if "NO Data" in message or "No Data" in message:
                    error = message
                    current_distinct_rows = 0
                    column_failures.append({
                        'status': 'No Data',
                        'column': current_column,
                        'table': current_table,
                        'error': message
                    })

                if "CALCULATED" in message and "Distinct" in message and "Row" and "Count" in message and "=" in message:
                    current_distinct_rows = message_array[5]

                if (("Could" in message and "not" in message) or ("Could" in message and "Not" in message and "Mask" in message and "Column" in message)) and ("Could Not Enable" not in message):
                    error = message
                    column_failures.append({
                        'status': 'Exception',
                        'column': current_column,
                        'table': current_table,
                        'error': message
                    })

                if "ERROR" in message and "Could Not Enable" not in message:
                    error = message
                    column_failures.append({
                        'status': 'Exception',
                        'column': current_column,
                        'table': current_table,
                        'error': message
                    })

                if ("pymysql.err" in message):
                    error = message
                    column_failures.append({
                        'status': 'Exception',
                        'column': current_column,
                        'table': current_table,
                        'error': message
                    })

                if ("NOT FOUND" in message or ".php" in message or ".py" in message):
                    error = message
                    column_failures.append({
                        'status': 'Exception',
                        'column': current_column,
                        'table': current_table,
                        'error': message
                    })

                if "Post-mask" in message:
                    post_mask_operations = True

                if "COLUMN" in message and "Mask Finished" in message:
                    end_time = timestamp
                    duration_sec = calculate_duration(start_time, end_time)
                    duration_min = round(duration_sec / 60, 2) if duration_sec else None

                    if len(column_failures) > 0:
                        last_error_column = column_failures[-1]
                        if last_error_column['status'] == 'Failed' or last_error_column['status'] == 'Exception':
                            error_column = last_error_column['column']
                            error_table = last_error_column['table']
                            if current_column == error_column and current_table == error_table:
                                status = last_error_column['status']
                            else:
                                status = "Passed"

                        mask_operations.append({
                            'cycle': cycle_num,
                            'schema': current_schema,
                            'table': current_table,
                            'row_count': current_rows,
                            'distinct_row_count': current_distinct_rows,
                            'column': current_column,
                            'status': status,
                            'start_time': start_time,
                            'end_time': end_time,
                            'duration_secs': duration_sec,
                            'duration_mins': duration_min,
                            'error': error,
                            'object_id': object_id,
                            'processed_time': datetime.now(),
                            'processed_by': 'YourName'
                        })
                        column_failures.clear()
                    else:
                        if current_column is not None:
                            status = 'Passed'
                            mask_operations.append({
                                'cycle': cycle_num,
                                'schema': current_schema,
                                'table': current_table,
                                'row_count': current_rows,
                                'distinct_row_count': current_distinct_rows,
                                'column': current_column,
                                'status': status,
                                'start_time': start_time,
                                'end_time': end_time,
                                'duration_secs': duration_sec,
                                'duration_mins': duration_min,
                                'error': error,
                                'object_id': object_id,
                                'processed_time': datetime.now(),
                                'processed_by': 'YourName'
                            })
                            column_failures.clear()

                    live_column = False
                    current_rows = None
                    current_distinct_rows = None
                    error = None

                if (live_column and "TABLE" in message and "Mask" in message and "Ended" in message) or (live_column and "MASKING" in message and "HAS" in message and "STARTED" in message):
                    status = 'Failed'
                    end_time = timestamp
                    duration_sec = calculate_duration(start_time, end_time)
                    duration_min = round(duration_sec / 60, 2) if duration_sec else None

                    mask_operations.append({
                        'cycle': cycle_num,
                        'schema': current_schema,
                        'table': current_table,
                        'row_count': current_rows,
                        'distinct_row_count': current_distinct_rows,
                        'column': current_column,
                        'status': status,
                        'start_time': start_time,
                        'end_time': end_time,
                        'duration_secs': duration_sec,
                        'duration_mins': duration_min,
                        'error': error,
                        'object_id': object_id,
                        'processed_time': datetime.now(),
                        'processed_by': 'YourName'
                    })
                    live_column = False
                    current_rows = None
                    current_distinct_rows = None
                    error = None

    # Create DataFrame
    if len(mask_operations) > 0:
        df = pd.DataFrame(mask_operations)
    else:
        df = None

    return df

# Process the DataFrame
result_df = log_analytics_from_df(pdf)

# Fill None values with appropriate defaults before type conversion
result_df['cycle'] = result_df['cycle'].fillna(0).astype(int)
result_df['row_count'] = result_df['row_count'].fillna(0).astype(float)
result_df['distinct_row_count'] = result_df['distinct_row_count'].fillna(0).astype(float)
result_df['duration_secs'] = result_df['duration_secs'].fillna(0).astype(float)
result_df['duration_mins'] = result_df['duration_mins'].fillna(0).astype(float)
result_df['object_id'] = result_df['object_id'].fillna(0).astype(int)

# Convert datetime columns to strings
result_df['start_time'] = result_df['start_time'].fillna('').astype(str)
result_df['end_time'] = result_df['end_time'].fillna('').astype(str)
result_df['processed_time'] = result_df['processed_time'].fillna('').astype(str)

# Define the schema explicitly
schema = StructType([
    StructField("cycle", IntegerType(), True),
    StructField("schema", StringType(), True),
    StructField("table", StringType(), True),
    StructField("row_count", FloatType(), True),
    StructField("distinct_row_count", FloatType(), True),
    StructField("column", StringType(), True),
    StructField("status", StringType(), True),
    StructField("start_time", StringType(), True),
    StructField("end_time", StringType(), True),
    StructField("duration_secs", FloatType(), True),
    StructField("duration_mins", FloatType(), True),
    StructField("error", StringType(), True),
    StructField("object_id", IntegerType(), True),
    StructField("processed_time", StringType(), True),
    StructField("processed_by", StringType(), True)
])

# Convert the result back to a Spark DataFrame if needed
if result_df is not None:
    spark_result_df = spark.createDataFrame(result_df, schema=schema)
    
    # Write the DataFrame as a Delta table
    spark_result_df.write.mode("append").format("delta").save("abfss://JumpStart_Project@onelake.dfs.fabric.microsoft.com/Silver.Lakehouse/Tables/masking_logs_results")
    
    # Show the result
    spark_result_df.show()
else:
    print("No data to display.")

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
