# 1. Apagar qdisc existente na interface de saída (ex: r_trans1-eth1)
tc qdisc del dev r_trans1-eth1 root

# 2. Adicionar uma qdisc PRIO, que tem bandas de prioridade
tc qdisc add dev r_trans1-eth1 root handle 1: prio bands 3

# 3. Criar filtros para direcionar o tráfego para as bandas corretas
# Tráfego uRLLC (ex: da porta 8080) para a banda 0 (prioridade mais alta)
tc filter add dev r_trans1-eth1 protocol ip parent 1: prio 1 u32 match ip dport 8080 0xffff flowid 1:1

# Tráfego eMBB (ex: da porta 5001) para a banda 1 (prioridade média)
tc filter add dev r_trans1-eth1 protocol ip parent 1: prio 2 u32 match ip dport 5001 0xffff flowid 1:2

# Todo o resto do tráfego vai para a banda 2 (prioridade mais baixa) por defeito