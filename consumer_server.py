from kafka import KafkaConsumer
import json


def run_kafka_consumer_server():
    consumer = KafkaConsumer("police-dept-calls",
                             bootstrap_servers=['localhost:9092'],
                             auto_offset_reset='earliest',
                             enable_auto_commit=True,
                             group_id='my-group'
                            )
    for message in consumer:
        print(json.loads(message.value))

if __name__ == "__main__":
    run_kafka_consumer_server()
