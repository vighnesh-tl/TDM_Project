CREATE TABLE [LogsAndConfigs].[masking_logs_results] (

	[cycle] int NULL, 
	[schema] varchar(8000) NULL, 
	[table] varchar(8000) NULL, 
	[row_count] real NULL, 
	[distinct_row_count] real NULL, 
	[column] varchar(8000) NULL, 
	[status] varchar(8000) NULL, 
	[start_time] varchar(8000) NULL, 
	[end_time] varchar(8000) NULL, 
	[duration_secs] real NULL, 
	[duration_mins] real NULL, 
	[error] varchar(8000) NULL, 
	[object_id] int NULL, 
	[processed_time] varchar(8000) NULL, 
	[processed_by] varchar(8000) NULL
);

