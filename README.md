# IMPACT OF THE USE OF HARDWARE RESOURCES IN 5G NETWORKS
This describes a very simple configuration that uses Open5GS and UERANSIM for monitoring the metrics with Prometheus. It will implement Grafana to represent this metrics and a custom evaluation tool of this system.

## Features
- Open5GS and UERANSIM implementation
- Prometheus and Grafana connection
- Collect real-time resource utilization & application metrics
![Grafana Dashboard](https://github.com/Amayoo0/Open5GS-UERANSIM-Setup/blob/d89230c537efaf65c7d4a62f8f6919a906b322e0/Monitoring/GrafanaDashboard/grafana-dashboard.png)

# Getting Started
## Requirements 

- Ubuntu v22.04
- Minikube: v1.29.0
- Docker v20.10.23
- Kubectl 
  - Client Version: v1.26.2
  - Kustomize Version: v4.5.7
  - Server Version: v1.26.1
- Helm v3.11.2
  - OPEN5GS v2.0.8
  - UERANSIM v0.2.5
  - Prometheus v20.0.0
  - Grafana 6.52.4
- Python >= 3.10
- Pip3

## Configure minikube cluster
```bash
# Delete existing cluster
minikube delete
# Create cluster with specific confinguration
minikube start --cpus=4 --memory=3200mb --disk-size='20000mb' --driver=docker
# Enable Metrics-Server addons
minikube addons enable metrics-server
```

## OPEN5GS
```bash
# Add the repository to your local machine
helm repo add openverso https://gradiant.github.io/openverso-charts/
# Install open5gs with some values
helm install open5gs openverso/open5gs --version 2.0.8 --values ./helm-values/5gSA-values.yaml 
```

The use of hardware resources is limited to the UPF network element in order to perform stress tests and study the behavior of this element at the resource limit.

| Tipo de recursos | Componente | UPF           |
|------------------|------------|---------------|
|   Request        | CPU        |     3mC     |
|                  | Memory     |     60MiB     |
|                                               |
|   Limits         | CPU        |     3mC     |
|                  | Memory     |     120MiB    |

 
## UERANSIM

```bash
# Install UERANSIM with some values
helm install ueransim-gnb openverso/ueransim-gnb --version 0.2.2 --values ./helm-values/gnb-ues-values.yaml
# Get a UE interactive console
kubectl exec -it deployments/ueransim-gnb-ues -- /bin/bash
# Check UE Connection
ip a
```
If the tunnel interfaces uesimtun0 and uesimtun1 have not been created in the UE at this point, it will be necessary to run the `./entrypoint.sh ue` script in an auxiliary terminal.

# Configure listener to K8's API for PodMonitoring 
To monitor the resource usage metrics exposed by the metrics-server service in the kubernetes API, we need a pod capable of obtaining and formatting these metrics so that prometheus can understand them.

Update the script in ./volume/pod-metrics.py

## Create an image in Docker Hub
The image will have the aplication ./volume/pod-metrics.py and all the dependencies. 
We upload the image to Docker Hub with the following commands:
```bash
docker login
  docker build -t amayo01/pod-metrics:latest .
  docker push amayo01/pod-metrics:latest
```

## Pod permissions
For the pod to have permission to view metrics in the kubernetes API is required:

```bash
kubectl apply -f ./config/pod-reader-role.yaml
kubectl apply -f ./config/pod-reader-rolebinding.yaml
```

## Create a deployment for pod-metrics
The deployment will raise a pod with a 'pod-metrics' container and a service associated to it that will be used to obtain the metrics from prometheus.

```bash
kubectl apply -f ./config/pod-metrics-deployment.yaml
``` 

## UE service that will export metrics.
Create a service that will export user experience metrics.
```bash
kubectl apply -f ./config/ue-metrics-service.yaml
```

# Prometheus & Grafana configuration
```bash
# Add the Helm repository
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
# Download the default values from the repository
helm show values prometheus-community/prometheus > ./helm-values/prometheus-values.yaml
```
It is necessary to add the targets that export metrics to the prometheus server indicating their IP and port
```yaml
serverFiles:
  prometheus.yml:
    scrape_configs:
      - job_name: prometheus
        static_configs:
          - targets:
            - localhost:9090
          
      - job_name: open5gs-amf-metrics
        static_configs:
          - targets:
            - 10.110.237.12:9090

      - job_name: open5gs-smf-metrics
        static_configs:
          - targets:
            - 10.110.202.209:9090

      - job_name: pod-metrics
        static_configs:
          - targets:
            - 10.109.13.143:8000
```

```bash
# Install prometheus
helm install prometheus prometheus-community/prometheus --values ./helm-values/prometheus-values.yaml

# The service is exposed to make it accessible.
kubectl expose service prometheus-server --type=NodePort --target-port=9090 --name=prometheus-ext
```

Grafana is now initialized. You will need to install it with helm and then configure it from the web interface. Run the following script and log in with the credentials reported by console. Then, configure Prometheus as a data source.
```bash
# Add the Helm repository
helm repo add grafana https://grafana.github.io/helm-charts 
# Install Grafana 
helm install grafana grafana/grafana --version 6.52.4
# The service is exposed to make it accessible.
kubectl expose service grafana --type=NodePort --target-port=3000 --name=grafana-ext

# Grafana credentials
pass=$(kubectl get secret --namespace default grafana -o yaml | grep admin-password | awk -F ": " '{print $2}' | openssl base64 -d ; echo)

# Access Grafana 
grafanaUrl=$(minikube service grafana-ext --url)
# Accessing Grafana credentials
echo -e "\n\n\nLogin to $grafanaUrl with admin:$pass "
# Add prometheus as data source 
echo "Go to Grafana Configuration > Data source > Add data source > Prometheus and provide the service URL generated: $prometheusUrl"
```

## Grafana Dashboard
Import ./Monitoring/GrafanaDashboard/OPEN5GS_UERANSIM-v14.json which incorporates resource usage graphs interesting for evaluation.

One of the graphs represents an estimation of quality of experience based on service metrics, weighting with higher value those metrics considered critical in certain services, such as jitter, network latency or throughput.

The query performed for the calculation of this quality metric is as follows:
```
R = R0 - Ie - Ae
R is the estimated MOS (Mean Opinion Score).
R0 is the basic MOS value without degradation.
Ie is the packet loss impairment factor.
Ae is the delay impairment factor.
```



# UE experience metrics
## Servidor iperf3 en UPF
```bash
# Get a UPF interactive console
kubectl -n default exec -ti deployment.apps/open5gs-upf -- /bin/bash
# To access the Internet from a pod it is necessary to change the DNS.
echo "nameserver 8.8.8.8" > /etc/resolv.conf

# Install dependencies 
apt update && apt install iperf3 -y
# Run Iperf3 server
iperf3 -s
```

## Iperf3 client in EU
```bash
# Get a UE interactive console
kubectl -n default exec -ti deployment.apps/ueransim-gnb-ues -- /bin/bash
# Install dependencies
apk add nano
# Use nano to create setup-iperf3 file and Copy/Paste ./ue-metrics-setup/setup-iperf3
...
# run setup-iperf3 script
./setup-iperf3
python3 setup-iperf3 10.45.0.1
``` 
To configure the output interface uesimtun0 as the default interface, the following commands must be executed.
```bash
ip route del default
ip route add default via 10.45.0.4 dev uesimtun0

traceroute 8.8.8.8
```


# stress testing
Stress tests are performed on the UPF to see how this element behaves when working at the edge of the allocated resource limit.
```bash
apt install -y stress memtester
stress --cpu 100 --timeout 45s
memtester 100M 1 -t 30
```


# How CPU usage is calculated? [metrics-server reference | FAQ](https://github.com/kubernetes-sigs/metrics-server/blob/master/FAQ.md)
## How CPU usage is calculated?
This value is derived by taking a rate over a cumulative CPU counter provided by the kernel (in both Linux and Windows kernels). Time window used to calculate CPU is exposed under window field in Metrics API. 

## How often metrics are scraped?
Default 60 seconds, can be changed using metric-resolution flag. We are not recommending setting values below 15s, as this is the resolution of metrics calculated by Kubelet.

| App | often metrics scraped | Parameter
|----------------|------------|-----------
| Kubelet        | 15s        | depending on the container activity
| metrics-server | 15s        | metrics-resolution   
| metrics-scrape | 5s         | time.sleep(5)
| Prometheus     | 5s         | global.scrape-interval 
| Grafana        | 5s         | web interface10.100.212.54
