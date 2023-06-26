#!/usr/bin/python
import requests
import time
from prometheus_client import start_http_server, Gauge

# Endpoint de la API de Kubernetes que devuelve las metricas de los pods
url = "http://localhost:8001/apis/metrics.k8s.io/v1beta1/namespaces/default/pods"

# Crear un contador de metricas de uso de CPU
cpu_gauge = Gauge('cpu_usage', 'CPU usage by pod', ['pod_name', 'namespace'])

# Contenedor de metricas de uso de Memoria
memory_gauge = Gauge('memory_usage', 'Memory usage by pod', ['pod_name', 'namespace'])

def update_resource_gauge():
    response = requests.get(url)
    pods_metrics = response.json()['items']
    # Accedemos a las metricas de cada pod
    for pod in pods_metrics:
        # Obtenemos el el nombre y namespace
        pod_name = pod['metadata']['name']
        namespace = pod['metadata']['namespace']

        # Obtenemos el valor de uso de CPU del pod
        cpu_usage_value = pod['containers'][0]['usage']['cpu']
        if cpu_usage_value.endswith('u'):
            cpu_usage_value = float(cpu_usage_value.strip('u')*1000) #convertimos a nCPU
        elif cpu_usage_value.endswith('n'):
            cpu_usage_value = float(cpu_usage_value.strip('n'))

        # Obtenemos el valor de uso de Memoria del pod
        memory_usage = pod['containers'][0]['usage']['memory']
        if memory_usage.endswith('Mi'):
            memory_usage_value = float(memory_usage.strip('Mi')*1024) #convertimos a Ki
        elif memory_usage.endswith('Ki'):
            memory_usage_value = float(memory_usage.strip('Ki'))

        # Actualizamos el valor de la metrica en los gauge de prometheus
        cpu_gauge.labels(pod_name=pod_name, namespace=namespace).set(cpu_usage_value)
        memory_gauge.labels(pod_name=pod_name, namespace=namespace).set(memory_usage_value)

if __name__ == '__main__':
    # Iniciar el servidor HTTP de Prometheus en el puerto 8000
    start_http_server(8000)

    while True:
        # Obtener el nivel de Recursos utilizados y establecer las metricas
        update_resource_gauge()

        # Esperar 5 segundos antes de volver a obtener las metricas
        time.sleep(5)
