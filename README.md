# udacity-data-streaming
Code for Project 2 of Udacity Data Streaming Nanodegree

Throughput and latency can be improved by using following SparkSession configs:
#### 1. spark.executor.cores
This is the number of concurrent tasks that can be run in an executor. Each task can be run on 1 partition of RDD and kafka partitions are matched 1:1 with the number of partitions in the input RDD. Thus, increasing total number of partitions, we can process more data from kafka
   
#### 2. spark.dynamicAllocation.enabled
Setting this to "true" allocates executors on need basis depending on the load. If more data is generated in Kafka, we can spin up more executors on-demand which results in increased partitions


I have used below config which seems to be optimal for me

spark.executor.cores=4
spark.dynamicAllocation.enabled=True
spark.driver.memory=16g
spark.executor.memory=16g
