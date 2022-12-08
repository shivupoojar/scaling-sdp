import gym
from gym import error, spaces, utils
from gym.utils import seeding
import numpy as np
import requests
import os
import kubernetes
from kubernetes import client, config
import json
import subprocess
import pint
import time
import yaml
from pprint import pprint
import math
import datetime
from gym.envs.toy_text import discrete

ten = 1
twenty = 2
thirty = 3
forty = 4
fifty = 5
sixty = 6
seventy = 7
eighty = 8
ninety = 9
hundrend_fifty = 10
two_hundrend = 11

class K8sEnvDiscreteStateDiscreteActionV0(discrete.DiscreteEnv):
  metadata = {'render.modes': ['human']}

  def __init__(self, app_name, sla_latency, prometheus_host,prometheus_latency_metric_name):
      # General variables defining the environment
      # Get following info from k8s
      num_states = 12000
      num_actions = 9
      P = {state: {action: [] for action in range(num_actions)} for state in range(num_states)}
      initial_state_distrib = np.zeros(num_states)
      self.done = False
      self.MAX_PODS = 10
      self.MIN_PODS = 1
      self.app_name = app_name
      self.sla_latency = float(sla_latency)
      self.prometheus_host = prometheus_host
      self.prometheus_latency_metric_name = prometheus_latency_metric_name
      self.observation_space = spaces.Tuple((
        spaces.Discrete(10), #pod_cpu_percent
        spaces.Discrete(10), #pod_memory_percent
        spaces.Discrete(10), #pod_numer_percent
        spaces.Discrete(12))) #latency_percent

      #self.action_space = spaces.Tuple((
        #spaces.Discrete(3), # cpu_hpa
        #spaces.Discrete(3))) #memory_hpa
      self.action_space = spaces.MultiDiscrete([3,3])
      #print(self.action_space.sample())
      discrete.DiscreteEnv.__init__(self, num_states, num_actions, P, initial_state_distrib)

  def step(self, action):
      '''
        Returns
        -------
        ob, reward, episode_over, info : tuple
            ob : List[int]
                an environment-specific object representing your observation of
                the environment.
            reward : float
                amount of reward achieved by the previous action. The scale
                varies between environments, but the goal is always to increase
                your total reward.
            info : Dict
                 diagnostic information useful for debugging. It can sometimes
                 be useful for learning (for example, it might contain the raw
                 probabilities behind the environment's last state change).
                 However, official evaluations of your agent are not allowed to
                 use this for learning.
      '''
      # create hpa
      self._take_action(action)
      # wait 2 minute for the hpa to take effect
      if action in [2,5,6,7,8]:
          time.sleep(480) # 8 minutes
      else:
          time.sleep(300) # 5 minutes
      ob = self._get_state()
      # calculate reward
      reward = self._get_reward(ob)
      now= datetime.datetime.now()
      dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
      return ob, reward, self.done, {'datetime':dt_string}

  def reset(self):
      return self._get_state()

  def render(self, mode='human'):
      return None

  def close(self):
      pass

  def _take_action(self,discrete_action):
      # see if there are any existing hpa
      #msg1 = subprocess.getoutput('kubectl get hpa '+ self.app_name + '-o json')
      #print(msg1)
      v2 = client.AutoscalingV2beta2Api()
      action = ACTIONS_LIST[discrete_action]
      if (action[0]==1 and action[1]==1):
          return

      ob_hpa =  self._get_existing_app_hpa()
      if ob_hpa[0] == 1:
          self.done = True
      else:
          self.done = False
      my_metrics = []
      new_cpu_hpa_threashold = int(ob_hpa[2])
      new_memory_hpa_threashold = ob_hpa[4]
      if ob_hpa[2] !=0 or ob_hpa[4] !=0:
          #delete the hpa
          api_response = v2.delete_namespaced_horizontal_pod_autoscaler(name = self.app_name, namespace='default', pretty='true')
          #pprint(api_response)
      if action[0] == 0 and new_cpu_hpa_threashold >10:
          new_cpu_hpa_threashold = new_cpu_hpa_threashold - 10
      if action[0] == 2 and new_cpu_hpa_threashold <100:
          new_cpu_hpa_threashold = int(new_cpu_hpa_threashold) + 10
      my_metrics.append(client.V2beta2MetricSpec(type='Resource', resource= client.V2beta2ResourceMetricSource(name='cpu', target=client.V2beta2MetricTarget(average_utilization= new_cpu_hpa_threashold,type='Utilization'))))

      if action[1] == 0 and new_memory_hpa_threashold >10:
          new_memory_hpa_threashold = new_memory_hpa_threashold - 10
      if action[1] == 2 and new_memory_hpa_threashold <100:
          new_memory_hpa_threashold = new_memory_hpa_threashold + 10
      my_metrics.append(client.V2beta2MetricSpec(type='Resource', resource= client.V2beta2ResourceMetricSource(name='memory', target=client.V2beta2MetricTarget(average_utilization= new_memory_hpa_threashold,type='Utilization'))))


      if  (len(my_metrics) >0):
          #print("my_metrics")
          #print(my_metrics)
          my_conditions = []
          my_conditions.append(client.V2beta2HorizontalPodAutoscalerCondition(status = "True", type = 'AbleToScale'))
          #print("my_conditions")
          #print(my_conditions)

          status = client.V2beta2HorizontalPodAutoscalerStatus(conditions = my_conditions, current_replicas = 1, desired_replicas = 1)

          body = client.V2beta2HorizontalPodAutoscaler(
              api_version='autoscaling/v2beta2',
              kind='HorizontalPodAutoscaler',
              metadata=client.V1ObjectMeta(name=self.app_name),
              spec= client.V2beta2HorizontalPodAutoscalerSpec(
                  max_replicas=self.MAX_PODS,
                  min_replicas=self.MIN_PODS,
                  metrics = my_metrics,
                  scale_target_ref = client.V2beta2CrossVersionObjectReference(kind = 'Deployment', name = self.app_name, api_version = 'apps/v1'),
              ),
              status = status)

          try:
              api_response = v2.create_namespaced_horizontal_pod_autoscaler(namespace='default', body=body, pretty=True)
              pprint(api_response)
          except Exception as e:
              #print("Exception when calling AutoscalingV2beta1Api->create_namespaced_horizontal_pod_autoscaler" )
              #print(e)
              print("new namespaced_horizontal_pod_autoscaler is created" )


  def _get_state(self):
      """
      Get the observation.
      pod_cpu: First number is the current pod cpu
      pod_memory: Second number is the current pod memory
      pods_number: Third number is the number of the current pods
      hpa_error: Fifth number informs whether there is some error with and enforced hpa (eg. wrong configuration of existing hpa)
      sla_throughput: Sixth number  refers to the average throughput by the set of deployed pods in requests/time_period. (if any. Default value is 0)
      sla_latency: Seventh number refers to the average latency by the set of deployed pods in seconds. (if any. Default value is 0)
      """
      config.load_kube_config()
      # get metrics from metrics-server API
      ob_hpa =  self._get_existing_app_hpa()

      pod_latency = 1000
      latency_response = requests.get(self.prometheus_host + '/api/v1/query', params={'query': self.prometheus_latency_metric_name})
      results = latency_response.json()['data']['result']
      for result in results:
          pod_latency = float(result['value'][1])

      pod_cpu_percent = ob_hpa[1]
      pod_memory_percent = ob_hpa[3]
      current_replicas_percent = 100*ob_hpa[5]/self.MAX_PODS
      ob_baseline = [pod_cpu_percent,pod_memory_percent,current_replicas_percent,100*pod_latency/self.sla_latency]
      print('ob_baseline')
      print(ob_baseline)
      ob = [self._get_discrete(ob_baseline[0]),
            self._get_discrete(ob_baseline[1]),
            self._get_discrete(ob_baseline[2]),
            self._get_discrete(ob_baseline[3])]
      print('----CURRENT STATE---')
      print(ob)
      return self.encode(self._get_discrete(ob_baseline[0]),
            self._get_discrete(ob_baseline[1]),
            self._get_discrete(ob_baseline[2]),
            self._get_discrete(ob_baseline[3]))

  def _get_reward(self, ob_encoded):
      """Reward is given depending on the
       Calculate reward value: The environment receives the current values of pod_number and cpu/memory metric values
       that correspond to the current state of the system s. The reward value r is calculated based on two criteria:
       (i) the amount of resources acquired, which directly determine the cost, and
       (ii) the number of pods needed to support the received load.
      """
      cpu, memory, pods, latency = self.decode(ob_encoded)
      reward_max = 100
      reward_min = 0
      reward = 0
      pod_number = pods * 0.1 * self.MAX_PODS # number of pods
      pod_latency = latency * self.sla_latency /100 # pod latency
      d = float(5) # this is a hyperparamter of the reward function

      if (pod_number ==1  and pod_latency<= 1):
          reward = reward_max
          return reward
      else :
          reward = -100/(self.MAX_PODS-1) * pod_number + 100*self.MAX_PODS/(self.MAX_PODS-1)

      ####latency
      if  (pod_latency < 0.95 ):
          reward += 100* pow(math.e, -d*pow(1-pod_latency,2))
      else:
          reward += 100* pow(math.e, -10*d*pow(1-pod_latency,2))

      reward = reward/2

      return reward

  def _get_discrete(self, number):
      """Get a number and return the discrete are it belongs
      """
      number = round(number,0)
      ten_range = range(-1, 10)
      twenty_range = range(10, 20)
      thirty_range = range(20, 30)
      forty_range = range(30, 40)
      fifty_range = range(40, 50)
      sixty_range = range(50, 60)
      seventy_range = range(60, 70)
      eighty_range = range(80, 90)
      ninety_range = range(90, 100)
      hundrend_fifty_range = range(100, 150)
      two_hundrend_range = range(150, 200)

      if number in ten_range:
          return ten
      elif number in twenty_range :
          return twenty
      elif number in thirty_range :
          return thirty
      elif number in forty_range :
          return forty
      elif number in fifty_range :
          return fifty
      elif number in sixty_range :
          return sixty
      elif number in seventy_range :
          return seventy
      elif number in eighty_range :
          return eighty
      elif number in ninety_range :
          return ninety
      elif number in hundrend_fifty_range :
          return hundrend_fifty
      elif (number in two_hundrend_range or  number > 200):
          return two_hundrend
      else:
          return 0


  def _get_existing_app_hpa(self):
      hpa_error = 0
      pod_cpu_current = 0
      pod_cpu_threshold = 0
      pod_memory_current = 0
      pod_memory_threshold = 0
      current_replicas = self.MAX_PODS
      # see if there are any existing hpa
      v2 = client.AutoscalingV2beta2Api()
      name = self.app_name # str | name of the HorizontalPodAutoscaler
      namespace = 'default' # str | object name and auth scope, such as for teams and projects
      pretty = 'true'

      try:
          item = v2.read_namespaced_horizontal_pod_autoscaler(name, namespace, pretty=pretty)
          #pprint(item)
          if(item.metadata.name == self.app_name) :
              #print("%s\t%s\t%s" % (item.spec.max_replicas, item.metadata.namespace, item.metadata.name))
              for metric in item.status.current_metrics:
                  if (metric.resource.name)  == 'cpu':
                      pod_cpu_current = metric.resource.current.average_utilization
                  if (metric.resource.name)  == 'memory':
                      pod_memory_current = metric.resource.current.average_utilization

              for condition in item.status.conditions:
                  #print("%s\t%s\t%s\t%s" % (condition.status, condition.reason, condition.type, condition.message))
                  if condition.reason !='DesiredWithinRange' and  condition.status == str(False):
                      hpa_error = 1
                      return [hpa_error,pod_cpu_threshold,pod_memory_threshold]
                  metrics = item.spec.metrics
                  for metric in metrics:
                      if metric.resource.name == 'cpu':
                          pod_cpu_threshold =  metric.resource.target.average_utilization
                      if metric.resource.name == 'memory':
                          pod_memory_threshold =  metric.resource.target.average_utilization

              current_replicas = item.status.current_replicas
              return [hpa_error,pod_cpu_current,pod_cpu_threshold,pod_memory_current,pod_memory_threshold,current_replicas]
      except Exception as e:
          print("Exception when calling AutoscalingV2beta2Api->read_namespaced_horizontal_pod_autoscaler:")
          #print(e)
          return [hpa_error,pod_cpu_current,pod_cpu_threshold,pod_memory_current,pod_memory_threshold,current_replicas]

  def encode(self, cpu, memory, pods, latency):
      # (10) 10, 10, 12
      i = cpu
      i *= 10
      i += memory
      i *= 10
      i += pods
      i *= 12
      i += latency
      return i

  def decode(self, i):
      out = []
      out.append(i % 12)
      i = i // 12
      out.append(i % 10)
      i = i // 10
      out.append(i % 10)
      i = i // 10
      out.append(i)
      assert 0 <= i < 10
      return reversed(out)



ACTIONS_LIST = {
    0 : [0,0],
    1 : [0,1],
    2 : [0,2],
    3 : [1,0],
    4 : [1,1],
    5 : [1,2],
    6 : [2,0],
    7 : [2,1],
    8 : [2,2],
}
