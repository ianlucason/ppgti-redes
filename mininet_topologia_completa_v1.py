#!/usr/bin/python

from mininet.net import Mininet
from mininet.node import Host, Node, OVSKernelSwitch
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel, info
import time
import os # Importar os para limpar o ficheiro de alerta
from threading import Thread # Importar Thread para o controlador

# Importar o nosso novo controlador
import controlador_qos

class LinuxRouter(Node):
    """Um Nó que se comporta como um roteador Linux."""
    def config(self, **params):
        super(LinuxRouter, self).config(**params)
        self.cmd('sysctl -w net.ipv4.ip_forward=1')
        info(f"*** Encaminhamento de IP habilitado em {self.name}\n")

    def terminate(self):
        self.cmd('sysctl -w net.ipv4.ip_forward=0')
        super(LinuxRouter, self).terminate()

def run_topology():
    # Limpa o ficheiro de alerta de uma execução anterior, se existir
    if os.path.exists("latencia.alerta"):
        os.remove("latencia.alerta")
        
    net = Mininet(switch=OVSKernelSwitch, link=TCLink, controller=None)

    info('*** Adicionando Roteadores da Rede de Transporte...\n')
    r_trans1 = net.addHost('r_trans1', cls=LinuxRouter, ip=None)
    r_trans2 = net.addHost('r_trans2', cls=LinuxRouter, ip=None)
    r_trans3 = net.addHost('r_trans3', cls=LinuxRouter, ip=None)
    r_trans4 = net.addHost('r_trans4', cls=LinuxRouter, ip=None)
    
    roteadores = [r_trans1, r_trans2, r_trans3, r_trans4]

    info('*** Adicionando Switches de Acesso...\n')
    s_access1 = net.addSwitch('s_access1')
    s_access2 = net.addSwitch('s_access2')

    info('*** Adicionando Hosts de Usuário e Nuvem...\n')
    h_uRLLC1 = net.addHost('h_uRLLC1', ip='172.18.1.10/24', defaultRoute='via 172.18.1.1')
    h_eMBB1 = net.addHost('h_eMBB1', ip='172.18.1.20/24', defaultRoute='via 172.18.1.1')
    h_uRLLC2 = net.addHost('h_uRLLC2', ip='172.18.2.10/24', defaultRoute='via 172.18.2.1')
    h_eMBB2 = net.addHost('h_eMBB2', ip='172.18.2.20/24', defaultRoute='via 172.18.2.1')
    h_cloud = net.addHost('h_cloud', ip='172.19.40.100/24', defaultRoute='via 172.19.40.4')
    
    link_params_access = {'bw': 50, 'delay': '1ms'}
    link_params_transport = {'bw': 100, 'delay': '1ms'}
    link_params_cloud = {'bw': 200, 'delay': '1ms'}

    info('*** Criando Links...\n')
    net.addLink(h_uRLLC1, s_access1, **link_params_access)
    net.addLink(h_eMBB1, s_access1, **link_params_access)
    net.addLink(h_uRLLC2, s_access2, **link_params_access)
    net.addLink(h_eMBB2, s_access2, **link_params_access)
    net.addLink(s_access1, r_trans1, intfName2='r_trans1-eth0', **link_params_access)
    net.addLink(s_access2, r_trans2, intfName2='r_trans2-eth0', **link_params_access)
    net.addLink(r_trans1, r_trans3, intfName1='r_trans1-eth1', intfName2='r_trans3-eth0', **link_params_transport)
    net.addLink(r_trans2, r_trans3, intfName1='r_trans2-eth1', intfName2='r_trans3-eth1', **link_params_transport)
    net.addLink(r_trans3, r_trans4, intfName1='r_trans3-eth2', intfName2='r_trans4-eth0', **link_params_transport)
    net.addLink(r_trans4, h_cloud, intfName1='r_trans4-eth1', **link_params_cloud)

    info('*** Iniciando a rede...\n')
    net.start()

    info('*** Configurando modo standalone para switches OVS...\n')
    for sw in net.switches:
        # Este comando diz ao switch para agir como um switch L2 de aprendizado
        # se ele não conseguir se conectar a um controlador. É crucial para o ARP funcionar.
        sw.cmd('ovs-vsctl set-fail-mode', sw.name, 'standalone')

    info('*** Configurando IPs e Rotas nos Roteadores...\n')
    r_trans1.cmd('ip addr add 172.18.1.1/24 dev r_trans1-eth0'); r_trans1.cmd('ip link set r_trans1-eth0 up')
    r_trans1.cmd('ip addr add 172.19.13.1/24 dev r_trans1-eth1'); r_trans1.cmd('ip link set r_trans1-eth1 up')
    r_trans2.cmd('ip addr add 172.18.2.1/24 dev r_trans2-eth0'); r_trans2.cmd('ip link set r_trans2-eth0 up')
    r_trans2.cmd('ip addr add 172.19.23.2/24 dev r_trans2-eth1'); r_trans2.cmd('ip link set r_trans2-eth1 up')
    r_trans3.cmd('ip addr add 172.19.13.3/24 dev r_trans3-eth0'); r_trans3.cmd('ip link set r_trans3-eth0 up')
    r_trans3.cmd('ip addr add 172.19.23.3/24 dev r_trans3-eth1'); r_trans3.cmd('ip link set r_trans3-eth1 up')
    r_trans3.cmd('ip addr add 172.19.34.3/24 dev r_trans3-eth2'); r_trans3.cmd('ip link set r_trans3-eth2 up')
    r_trans4.cmd('ip addr add 172.19.34.4/24 dev r_trans4-eth0'); r_trans4.cmd('ip link set r_trans4-eth0 up')
    r_trans4.cmd('ip addr add 172.19.40.4/24 dev r_trans4-eth1'); r_trans4.cmd('ip link set r_trans4-eth1 up')
    r_trans1.cmd('ip route add 172.18.2.0/24 via 172.19.13.3'); r_trans1.cmd('ip route add 172.19.23.0/24 via 172.19.13.3'); r_trans1.cmd('ip route add 172.19.34.0/24 via 172.19.13.3'); r_trans1.cmd('ip route add 172.19.40.0/24 via 172.19.13.3')
    r_trans2.cmd('ip route add 172.18.1.0/24 via 172.19.23.3'); r_trans2.cmd('ip route add 172.19.13.0/24 via 172.19.23.3'); r_trans2.cmd('ip route add 172.19.34.0/24 via 172.19.23.3'); r_trans2.cmd('ip route add 172.19.40.0/24 via 172.19.23.3')
    r_trans3.cmd('ip route add 172.18.1.0/24 via 172.19.13.1'); r_trans3.cmd('ip route add 172.18.2.0/24 via 172.19.23.2'); r_trans3.cmd('ip route add 172.19.40.0/24 via 172.19.34.4')
    r_trans4.cmd('ip route add 172.18.1.0/24 via 172.19.34.3'); r_trans4.cmd('ip route add 172.18.2.0/24 via 172.19.34.3'); r_trans4.cmd('ip route add 172.19.13.0/24 via 172.19.34.3'); r_trans4.cmd('ip route add 172.19.23.0/24 via 172.19.34.3')

    info('*** Aguardando para estabilização da rede...\n')
    time.sleep(2)
    
    info('*** Iniciando o Controlador de QoS em uma thread separada...\n')
    controller_thread = Thread(target=controlador_qos.iniciar_loop_controle, args=(roteadores,))
    controller_thread.daemon = True
    controller_thread.start()
    
    info('*** Iniciando o Monitor de Latência uRLLC...\n')
    h_uRLLC1.cmd('sudo python3 gerador_monitor_uRLLC.py > urllc_log.txt &')
    
    info('*** Iniciando Servidor iperf para tráfego eMBB...\n')
    h_cloud.cmd('iperf -s &')

    info('*** Topologia pronta. Teste a conectividade no CLI.\n')
    CLI(net)

    info('*** Parando a rede...\n')
    net.stop()
    if os.path.exists("latencia.alerta"):
        os.remove("latencia.alerta")

if __name__ == '__main__':
    setLogLevel('info')
    run_topology()
