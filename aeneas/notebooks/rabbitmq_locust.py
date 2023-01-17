from rabbitmq import get_client
from locust import User, TaskSet, events, task, between,constant_pacing
from locust import Locust, TaskSet, task, events

class RabbitTaskSet(TaskSet):
    @task
    def publish(self):
        get_client().publish()

class MyLocust(User):
    tasks = {RabbitTaskSet}
    wait_time = constant_pacing(4)    
  #  wait_time = between(1, 10)

def on_locust_stop_hatching():
    get_client().disconnect()

#events.test_stop += on_locust_stop_hatching