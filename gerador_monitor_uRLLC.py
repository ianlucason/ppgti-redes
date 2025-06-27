from scapy.all import IP, TCP, sr1
import time

ip_destino = "172.19.40.100"  # IP do h_cloud
porta_destino = 8080
intervalo_segundos = 1

print(f"Iniciando gerador/monitor uRLLC para {ip_destino}:{porta_destino}")
try:
    while True:
        pacote = IP(dst=ip_destino) / TCP(dport=porta_destino, flags="S")
        tempo_envio = time.time()
        resposta = sr1(pacote, timeout=1, verbose=0)
        if resposta:
            latencia_ms = (time.time() - tempo_envio) * 1000
            print(f"Latência uRLLC: {latencia_ms:.2f} ms")
            if latencia_ms > 5.0:
                print(f"ALERTA: Latência ({latencia_ms:.2f} ms) excedeu 5ms!")
        else:
            print("Timeout no pacote uRLLC.")
        time.sleep(intervalo_segundos)
except KeyboardInterrupt:
    print("\nParando gerador uRLLC.")
