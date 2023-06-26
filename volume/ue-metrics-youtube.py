#!/usr/bin/python
from prometheus_client import start_http_server, Gauge
import json, time

# Ruta del archivo JSON
json_path = "/youtube/results/default.json"

# Crear un contador de metricas de MOS
mos_gauge = Gauge('mos', 'Mean Opinion Score')

# Contenedores de metricas de resolución de video
resolutions_gauge = {
    "144p": Gauge("Resolution_displayed_percentage_144p", "Resolution displayed percentage for 144p"),
    "240p": Gauge("Resolution_displayed_percentage_240p", "Resolution displayed percentage for 240p"),
    "360p": Gauge("Resolution_displayed_percentage_360p", "Resolution displayed percentage for 360p"),
    "480p": Gauge("Resolution_displayed_percentage_480p", "Resolution displayed percentage for 480p"),
    "720p": Gauge("Resolution_displayed_percentage_720p", "Resolution displayed percentage for 720p"),
    "1080p": Gauge("Resolution_displayed_percentage_1080p", "Resolution displayed percentage for 1080p"),
    "2K": Gauge("Resolution_displayed_percentage_2K", "Resolution displayed percentage for 2K"),
    "4K": Gauge("Resolution_displayed_percentage_4K", "Resolution displayed percentage for 4K"),
    "8K": Gauge("Resolution_displayed_percentage_8K", "Resolution displayed percentage for 8K"),
    "0": Gauge("Resolution_displayed_percentage_0", "Resolution displayed percentage for 0")
}

def update_qoe_gauge():
    with open(json_path, 'r') as json_file:
        data = json.load(json_file)
        mos_value = data['metrics'][0]['mos']
        mos_gauge.set(mos_value)
    for resolution, value in data['metrics'][0]['Resolution_displayed_percentage'].items():
        resolutions_gauge[resolution].set(value)

if __name__ == '__main__':
    # Iniciar el servidor HTTP de Prometheus en el puerto 8000
    start_http_server(8000)

    while True:
        update_qoe_gauge() # Actualiza métricas QoE
        time.sleep(5)      # Espera 5s