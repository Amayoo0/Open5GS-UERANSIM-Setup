FROM ubuntu:22.10

WORKDIR /etc/config

COPY ./volume/pod-metrics.py .

RUN apt update
RUN apt install -y python3
RUN apt install -y python3-pip
RUN pip3 install prometheus_client
RUN pip3 install requests

RUN apt install -y curl 
RUN curl -LO 'https://dl.k8s.io/release/v1.26.2/bin/linux/amd64/kubectl'
RUN install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

CMD ["echo", "[+] Proxy has been configued!"]
CMD ["tail", "-f", "/dev/null"]