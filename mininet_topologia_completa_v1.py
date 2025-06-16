#!/usr/bin/python

from mininet.net import Mininet
from mininet.node import Host, Node, OVSKernelSwitch
from mininet.link import TCLink # Necessário para parâmetros como bw, delay, loss
from mininet.cli import CLI
from mininet.log import setLogLevel, info
import time # Importar o módulo time para usar time.sleep()

class LinuxRouter(Node):
    """Um Nó que se comporta como um roteador Linux."""
    def config(self, **params):
        super(LinuxRouter, self).config(**params)
        # Habilitar o encaminhamento de IP
        self.cmd('sysctl -w net.ipv4.ip_forward=1')
        info(f"*** Encaminhamento de IP habilitado em {self.name}\n")

    def terminate(self):
        self.cmd('sysctl -w net.ipv4.ip_forward=0')
        super(LinuxRouter, self).terminate()

def run_topology():
    net = Mininet(switch=OVSKernelSwitch, link=TCLink, controller=None)

    info('*** Adicionando Roteadores da Rede de Transporte...\n')
    r_trans1 = net.addHost('r_trans1', cls=LinuxRouter, ip=None) # IPs serão configurados após net.start()
    r_trans2 = net.addHost('r_trans2', cls=LinuxRouter, ip=None)
    r_trans3 = net.addHost('r_trans3', cls=LinuxRouter, ip=None)
    r_trans4 = net.addHost('r_trans4', cls=LinuxRouter, ip=None)

    info('*** Adicionando Switches de Acesso...\n')
    s_access1 = net.addSwitch('s_access1')
    s_access2 = net.addSwitch('s_access2')

    info('*** Adicionando Hosts de Usuário e Nuvem...\n')
    # Segmento de Acesso 1: Rede 172.18.1.0/24
    h_uRLLC1 = net.addHost('h_uRLLC1', ip='172.18.1.10/24', defaultRoute='via 172.18.1.1')
    h_eMBB1 = net.addHost('h_eMBB1', ip='172.18.1.20/24', defaultRoute='via 172.18.1.1')

    # Segmento de Acesso 2: Rede 172.18.2.0/24
    h_uRLLC2 = net.addHost('h_uRLLC2', ip='172.18.2.10/24', defaultRoute='via 172.18.2.1')
    h_eMBB2 = net.addHost('h_eMBB2', ip='172.18.2.20/24', defaultRoute='via 172.18.2.1')

    # Host Nuvem/Core 5G: Rede 172.19.40.0/24
    h_cloud = net.addHost('h_cloud', ip='172.19.40.100/24', defaultRoute='via 172.19.40.4')

    # Parâmetros de Link (exemplo, pode ajustar conforme necessário)
    link_params_access = {'bw': 50, 'delay': '2ms'}
    link_params_transport = {'bw': 100, 'delay': '5ms'} # Links entre roteadores
    link_params_cloud = {'bw': 200, 'delay': '10ms'}
    
    info('*** Criando Links...\n')
    # Conexões aos Switches de Acesso
    net.addLink(h_uRLLC1, s_access1, **link_params_access)
    net.addLink(h_eMBB1, s_access1, **link_params_access)
    net.addLink(h_uRLLC2, s_access2, **link_params_access)
    net.addLink(h_eMBB2, s_access2, **link_params_access)

    # Conexões dos Switches de Acesso aos Roteadores de Entrada
    net.addLink(s_access1, r_trans1, intfName2='r_trans1-eth0', **link_params_access)
    net.addLink(s_access2, r_trans2, intfName2='r_trans2-eth0', **link_params_access)

    # Links entre Roteadores da Rede de Transporte
    net.addLink(r_trans1, r_trans3, intfName1='r_trans1-eth1', intfName2='r_trans3-eth0', **link_params_transport)
    net.addLink(r_trans2, r_trans3, intfName1='r_trans2-eth1', intfName2='r_trans3-eth1', **link_params_transport)
    net.addLink(r_trans3, r_trans4, intfName1='r_trans3-eth2', intfName2='r_trans4-eth0', **link_params_transport)

    # Link do Roteador de Saída para a Nuvem
    net.addLink(r_trans4, h_cloud, intfName1='r_trans4-eth1', **link_params_cloud)

    info('*** Iniciando a rede (sem IPs/rotas de roteador ainda)...\n')
    net.start() # Inicia os switches, hosts (com seus IPs/rotas padrão), e chama .config() dos nós (LinuxRouter)

    # =======================================================================
    # Configuração de IP e Rotas dos ROTEADORES - MOVIDO PARA DEPOIS DE net.start()
    # =======================================================================
    
    info('*** Configurando modo standalone para switches OVS...\n')
    for sw in net.switches:
        # Este comando diz ao switch para agir como um switch L2 de aprendizado
        # se ele não conseguir se conectar a um controlador.
        sw.cmd('ovs-vsctl set-fail-mode', sw.name, 'standalone')

    info('*** Configurando IPs das interfaces dos roteadores (APÓS net.start())...\n')
    # r_trans1
    r_trans1.cmd('ip addr add 172.18.1.1/24 dev r_trans1-eth0')
    r_trans1.cmd('ip link set r_trans1-eth0 up') # Descomentado
    r_trans1.cmd('ip addr add 172.19.13.1/24 dev r_trans1-eth1')
    r_trans1.cmd('ip link set r_trans1-eth1 up') # Descomentado

    # r_trans2
    r_trans2.cmd('ip addr add 172.18.2.1/24 dev r_trans2-eth0')
    r_trans2.cmd('ip link set r_trans2-eth0 up') # Descomentado
    r_trans2.cmd('ip addr add 172.19.23.2/24 dev r_trans2-eth1')
    r_trans2.cmd('ip link set r_trans2-eth1 up') # Descomentado

    # r_trans3
    r_trans3.cmd('ip addr add 172.19.13.3/24 dev r_trans3-eth0') # para r_trans1
    r_trans3.cmd('ip link set r_trans3-eth0 up') # Descomentado
    r_trans3.cmd('ip addr add 172.19.23.3/24 dev r_trans3-eth1') # para r_trans2
    r_trans3.cmd('ip link set r_trans3-eth1 up') # Descomentado
    r_trans3.cmd('ip addr add 172.19.34.3/24 dev r_trans3-eth2') # para r_trans4
    r_trans3.cmd('ip link set r_trans3-eth2 up') # Descomentado

    # r_trans4
    r_trans4.cmd('ip addr add 172.19.34.4/24 dev r_trans4-eth0') # para r_trans3
    r_trans4.cmd('ip link set r_trans4-eth0 up') # Descomentado
    r_trans4.cmd('ip addr add 172.19.40.4/24 dev r_trans4-eth1') # para h_cloud
    r_trans4.cmd('ip link set r_trans4-eth1 up') # Descomentado

    info('*** Configurando Rotas Estáticas nos Roteadores (APÓS net.start())...\n')
    # Rotas em r_trans1 (próximo salto é r_trans3 via IP 172.19.13.3)
    r_trans1.cmd('ip route add 172.18.2.0/24 via 172.19.13.3')
    r_trans1.cmd('ip route add 172.19.23.0/24 via 172.19.13.3')
    r_trans1.cmd('ip route add 172.19.34.0/24 via 172.19.13.3')
    r_trans1.cmd('ip route add 172.19.40.0/24 via 172.19.13.3')

    # Rotas em r_trans2 (próximo salto é r_trans3 via IP 172.19.23.3)
    r_trans2.cmd('ip route add 172.18.1.0/24 via 172.19.23.3')
    r_trans2.cmd('ip route add 172.19.13.0/24 via 172.19.23.3')
    r_trans2.cmd('ip route add 172.19.34.0/24 via 172.19.23.3')
    r_trans2.cmd('ip route add 172.19.40.0/24 via 172.19.23.3')

    # Rotas em r_trans3
    r_trans3.cmd('ip route add 172.18.1.0/24 via 172.19.13.1')
    r_trans3.cmd('ip route add 172.18.2.0/24 via 172.19.23.2')
    r_trans3.cmd('ip route add 172.19.40.0/24 via 172.19.34.4')

    # Rotas em r_trans4 (próximo salto é r_trans3 via IP 172.19.34.3)
    r_trans4.cmd('ip route add 172.18.1.0/24 via 172.19.34.3')
    r_trans4.cmd('ip route add 172.18.2.0/24 via 172.19.34.3')
    r_trans4.cmd('ip route add 172.19.13.0/24 via 172.19.34.3')
    r_trans4.cmd('ip route add 172.19.23.0/24 via 172.19.34.3')
    # =======================================================================

    info('*** Aguardando um momento para estabilização da rede e ARP...\n')
    time.sleep(3) # Adiciona um delay de 3 segundos

    # Opcional: Imprimir tabelas de roteamento para depuração
    info("--- Tabela de Roteamento h_uRLLC1 ---\n")
    info(h_uRLLC1.cmd('ip route'))
    info("--- Tabela ARP h_uRLLC1 (após delay) ---\n")
    info(h_uRLLC1.cmd('arp -n'))


    info("--- Tabela de Roteamento r_trans1 ---\n")
    info(r_trans1.cmd('ip route'))
    info("--- Tabela de Roteamento r_trans2 ---\n")
    info(r_trans2.cmd('ip route'))
    info("--- Tabela de Roteamento r_trans3 ---\n")
    info(r_trans3.cmd('ip route'))
    info("--- Tabela de Roteamento r_trans4 ---\n")
    info(r_trans4.cmd('ip route'))

    info('*** Topologia em execução. Use o CLI do Mininet para testar.\n')
    info('*** Exemplos de teste:\n')
    info('mininet> h_uRLLC1 ping 172.19.40.100 -c 3\n')
    info('mininet> h_uRLLC2 ping 172.18.1.10 -c 3\n')
    info('mininet> iperf h_eMBB1 h_cloud\n')
    CLI(net)

    info('*** Parando a rede...\n')
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    run_topology()
