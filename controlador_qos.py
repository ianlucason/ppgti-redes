import time
import os

# --- Configurações ---
arquivo_alerta = "latencia.alerta"
intervalo_verificacao = 2 # Segundos
porta_urllc = 8080
porta_embb = 5001 # Porta padrão do iperf

# Flag para saber se as regras de QoS já foram aplicadas
regras_qos_ativas = False

def aplicar_regras_qos(roteadores):
    """Aplica regras de QoS para priorizar tráfego uRLLC."""
    print(">>> Aplicando regras de QoS para priorizar uRLLC...")
    for roteador in roteadores:
        # A interface de saída é a que leva para o próximo salto em direção à nuvem
        # Ex: para r_trans1, é a r_trans1-eth1 que leva para r_trans3
        # Vamos aplicar em todas as interfaces de transporte para garantir
        interfaces = [iface for iface in roteador.intfList() if 'lo' not in str(iface)]
        for iface in interfaces:
            print(f"Aplicando regras em {roteador.name}-{iface.name}")
            # Apaga qdisc existente na interface
            roteador.cmd(f'tc qdisc del dev {iface.name} root')
            # Adiciona uma qdisc PRIO, que tem 3 bandas de prioridade por padrão
            roteador.cmd(f'tc qdisc add dev {iface.name} root handle 1: prio')
            # Filtros para direcionar o tráfego para as bandas corretas
            # Tráfego uRLLC (porta {porta_urllc}) para a banda 1 (prioridade mais alta)
            roteador.cmd(f'tc filter add dev {iface.name} protocol ip parent 1: prio 1 u32 match ip dport {porta_urllc} 0xffff flowid 1:1')
            # Tráfego eMBB (porta {porta_embb}) para a banda 2 (prioridade média)
            roteador.cmd(f'tc filter add dev {iface.name} protocol ip parent 1: prio 2 u32 match ip dport {porta_embb} 0xffff flowid 1:2')
            # Todo o resto do tráfego vai para a banda 3 (prioridade mais baixa) por defeito.
    return True

def remover_regras_qos(roteadores):
    """Remove as regras de QoS, voltando ao padrão."""
    print("<<< Removendo regras de QoS...")
    for roteador in roteadores:
        interfaces = [iface for iface in roteador.intfList() if 'lo' not in str(iface)]
        for iface in interfaces:
            print(f"Removendo regras de {roteador.name}-{iface.name}")
            # Apaga qdisc da interface, voltando para o padrão pfifo_fast do Linux
            roteador.cmd(f'tc qdisc del dev {iface.name} root')
    return False

def iniciar_loop_controle(roteadores_para_controlar):
    """Loop principal que monitoriza o alerta e aciona o controlo."""
    global regras_qos_ativas
    print("Iniciando loop de controlo de QoS...")
    try:
        while True:
            if os.path.exists(arquivo_alerta):
                # ALERTA DE LATÊNCIA ALTA
                if not regras_qos_ativas:
                    regras_qos_ativas = aplicar_regras_qos(roteadores_para_controlar)
            else:
                # LATÊNCIA NORMALIZADA
                if regras_qos_ativas:
                    regras_qos_ativas = remover_regras_qos(roteadores_para_controlar)
            
            time.sleep(intervalo_verificacao)
    except KeyboardInterrupt:
        print("\nParando loop de controlo.")
        # Garante que as regras sejam removidas ao sair
        if regras_qos_ativas:
            remover_regras_qos(roteadores_para_controlar)

if __name__ == '__main__':
    # Este script é projetado para ser importado e ter a função 
    # iniciar_loop_controle chamada pelo script principal do Mininet.
    # Se executado diretamente, não fará nada.
    print("Este script deve ser importado.")
