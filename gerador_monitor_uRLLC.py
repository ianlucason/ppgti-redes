from scapy.all import IP, TCP, sr1
import time
import os

# --- Configurações ---
ip_destino = "172.19.40.100"  # IP do h_cloud
porta_destino = 8080         # Porta TCP de destino para uRLLC
intervalo_segundos = 1     # Intervalo entre envio de pacotes
arquivo_alerta = "latencia.alerta" # Nome do ficheiro de alerta

print(f"Iniciando gerador/monitor uRLLC para {ip_destino}:{porta_destino}")
try:
    while True:
        pacote = IP(dst=ip_destino) / TCP(dport=porta_destino, flags="S")
        tempo_envio = time.time()
        resposta = sr1(pacote, timeout=1, verbose=0)
        
        latencia_ms = (time.time() - tempo_envio) * 1000 if resposta else -1

        if resposta:
            print(f"Latência uRLLC: {latencia_ms:.2f} ms")
            
            if latencia_ms > 5.0:
                # Se a latência exceder 5ms, cria o ficheiro de alerta se ele não existir
                if not os.path.exists(arquivo_alerta):
                    print(f"ALERTA: Latência ({latencia_ms:.2f} ms) excedeu 5ms! Criando ficheiro de alerta.")
                    with open(arquivo_alerta, 'w') as f:
                        f.write(str(latencia_ms))
            else:
                # Se a latência está OK, apaga o ficheiro de alerta se ele existir
                if os.path.exists(arquivo_alerta):
                    print("Latência normalizada. Removendo ficheiro de alerta.")
                    os.remove(arquivo_alerta)
        else:
            print("Timeout no pacote uRLLC.")

        time.sleep(intervalo_segundos)

except KeyboardInterrupt:
    print("\nParando gerador uRLLC.")
    # Garante que o ficheiro de alerta seja removido ao sair
    if os.path.exists(arquivo_alerta):
        os.remove(arquivo_alerta)
