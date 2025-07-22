from scapy.all import IP, TCP, sr1
import time
import os

# --- Configurações ---
ip_destino = "172.19.40.100"  # IP do h_cloud
porta_destino = 8080         # Porta TCP de destino para uRLLC
intervalo_segundos = 1     # Intervalo entre envio de pacotes
arquivo_alerta = "latencia.alerta" # Nome do ficheiro de alerta

# --- ALTERAÇÃO PRINCIPAL ---
# Ajustar o limiar para um valor realista para o ambiente de simulação.
limiar_latencia_ms = 80.0

# --- LÓGICA DE CONTROLO AVANÇADA ---
# Período de calma: A latência deve permanecer abaixo do limiar por este
# número de segundos antes de as regras de QoS serem removidas.
# Aumentado para 70s para ser maior que a duração do teste iperf (60s).
periodo_normalizacao_segundos = 70.0
# Variável para rastrear o início do período de calma.
tempo_primeira_latencia_ok = 0

print(f"Iniciando gerador/monitor uRLLC para {ip_destino}:{porta_destino} (Limiar: {limiar_latencia_ms} ms)")
try:
    while True:
        pacote = IP(dst=ip_destino) / TCP(dport=porta_destino, flags="S")
        tempo_envio = time.time()
        resposta = sr1(pacote, timeout=1, verbose=0)
        
        latencia_ms = (time.time() - tempo_envio) * 1000 if resposta else -1

        if resposta:
            print(f"Latência uRLLC: {latencia_ms:.2f} ms")
            
            if latencia_ms > limiar_latencia_ms:
                # Se a latência exceder o limiar, cria o ficheiro de alerta
                if not os.path.exists(arquivo_alerta):
                    print(f"ALERTA: Latência ({latencia_ms:.2f} ms) excedeu {limiar_latencia_ms}ms! Criando ficheiro de alerta.")
                    with open(arquivo_alerta, 'w') as f:
                        f.write(str(latencia_ms))
                # Reinicia o temporizador do período de calma, pois a rede está instável.
                tempo_primeira_latencia_ok = 0
            else:
                # Se a latência está OK, verifica se o período de calma já passou.
                if os.path.exists(arquivo_alerta):
                    if tempo_primeira_latencia_ok == 0:
                        # Inicia o temporizador do período de calma.
                        print(f"Latência abaixo do limiar. Iniciando período de calma de {periodo_normalizacao_segundos}s...")
                        tempo_primeira_latencia_ok = time.time()
                    
                    # Verifica se o tempo decorrido é maior que o período de calma.
                    elif (time.time() - tempo_primeira_latencia_ok) > periodo_normalizacao_segundos:
                        print("Período de calma concluído. Latência estável. Removendo ficheiro de alerta.")
                        os.remove(arquivo_alerta)
                        tempo_primeira_latencia_ok = 0 # Reinicia o temporizador
        else:
            print("Timeout no pacote uRLLC.")
            # Reinicia o temporizador se houver perda de pacotes.
            tempo_primeira_latencia_ok = 0

        time.sleep(intervalo_segundos)

except KeyboardInterrupt:
    print("\nParando gerador uRLLC.")
    if os.path.exists(arquivo_alerta):
        os.remove(arquivo_alerta)
