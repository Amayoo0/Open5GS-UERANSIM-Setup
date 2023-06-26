#!/usr/bin/python3
import time
from prometheus_client import start_http_server, Gauge
import iperf3, argparse, subprocess, re
from ping3 import ping


# Crear un contador de metricas de uso de CPU
iperf3_throughput    = Gauge('iperf3_throughput', 'Throughput of iperf3 (bps)')
iperf3_duration      = Gauge('iperf3_duration', 'Duration of iperf3 (seg)')
iperf3_data_received = Gauge('iperf3_data_received', 'Data received with iperf3 (bytes)')
iperf3_data_sent     = Gauge('iperf3_data_sent', 'Data sent with iperf3 (bytes)')
ping3_latency        = Gauge('ping3_latency', 'Latency with ping3 (ms)')
ping3_jitter         = Gauge('ping3_jitter', 'Jitter with ping3 (ms)')

server_port = 5201  # Puerto del servidor de iperf
duration = 5        # Duración de la prueba en segundos
bind_name = 'uesimtun0'

def get_interface_ip(interface):
    command = f"ip addr show dev {interface}"
    result = subprocess.run(command.split(), capture_output=True, text=True)
    
    output_lines = result.stdout.strip().split('\n')
    for line in output_lines:
        if 'inet ' in line:
            ip = line.split()[1].split('/')[0]
            return ip
    
    return None 

def run_ping_client(server_host):
    num_pings = 4
    
    try:
        result = []
        for _ in range(num_pings):
            # response = ping(server_host, unit='ms', interface=bind_name)
            response = ping(server_host, unit='ms')
            if response == False:
                raise Exception("Server not found")
            result.append(response)
        # Filtrar valores no nulos
        result = [response for response in result if response is not None]
        if len(result) > 0:
            # Calcular el jitter
            jitter = max(result) - min(result)

            # Calcular la latencia promedio
            latency_sum = sum(float(value) for value in result)
            latency_avg = latency_sum / len(result)

            print(f"  Latency: {latency_avg} ms")
            print(f"  Jitter: {jitter} ms")

            ping3_latency.set(latency_avg)
            ping3_jitter.set(jitter)
        else: 
            raise Exception("No hay tiempos de respuesta para calcular el jitter")
    except Exception as e:
        print("[-] ERROR (ping3):", str(e))

def run_iperf_client(server_host, server_port, duration):
    client = iperf3.Client()
    client.server_hostname = server_host
    #client.bind_address = bind_ip
    client.blksize = 100
    client.port = server_port
    client.duration = duration

    print(f"Connecting to {client.server_hostname}:{client.port} Binding:{bind_ip}")
    result = client.run()

    if result.error:
        print(f"[-] ERROR (iperf3): {result.error}")
    else:
        print(f"Test completed:")
        print(f"  Duration: {result.duration}")
        print(f"  Sent data: {result.sent_bytes} bytes")
        print(f"  Received data: {result.received_bytes} bytes")
        print(f"  Throughput: {result.sent_bps} bps")

        # Actualizamos las métricas en los gauge de prometheus
        iperf3_throughput.set(result.sent_bps)
        iperf3_duration.set(result.duration)
        iperf3_data_received.set(result.received_bytes)
        iperf3_data_sent.set((result.sent_bytes))


if __name__ == "__main__":
    # Iniciar el servidor HTTP de Prometheus en el puerto 8000
    start_http_server(8000)    

    parser = argparse.ArgumentParser()
    parser.add_argument("server_host", help="IP del servidor iperf3")
    args = parser.parse_args()

    bind_ip = get_interface_ip(bind_name)
    server_host = args.server_host

    if bind_ip == None:
        print(f"[-] ERROR: Invalid bind address")
        exit(-1)

    while True:
        # Ejecuta el cliente iperf y ping
        run_iperf_client(server_host, server_port, duration)
        run_ping_client(server_host)
        
        # Esperar 5 segundos antes de volver a obtener las metricas
        time.sleep(5)