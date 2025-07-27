# Simulação de Rede 5G com Mininet para QoS de Tráfego eMBB e uRLLC

Este repositório contém uma simulação de rede 5G simplificada utilizando Mininet, focada na aplicação de políticas de Qualidade de Serviço (QoS) para diferenciar e priorizar tráfegos Enhanced Mobile Broadband (eMBB) e Ultra-Reliable Low-Latency Communication (uRLLC). A simulação monitora a latência do tráfego uRLLC e dinamicamente aplica regras de QoS (HTB + SFQ) nos roteadores de transporte para garantir os requisitos de baixa latência do uRLLC, enquanto gerencia o tráfego eMBB.

## Autores

* **[Talles Thomas Roodrigues Cavalcante]**
* **[Ian Lucas Oliveira Nunes]**

## Sumário
- [Visão Geral da Topologia](#visão-geral-da-topologia)
- [Funcionalidades Implementadas](#funcionalidades-implementadas)
- [Requisitos de Sistema](#requisitos-de-sistema)
- [Preparação do Ambiente](#preparação-do-ambiente)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Como Executar a Simulação](#como-executar-a-simulação)
- [Análise dos Resultados](#análise-dos-resultados)
- [Limpeza](#limpeza)
- [Licença](#licença)

## Visão Geral da Topologia

A topologia Mininet simula uma rede com os seguintes componentes:

- **Hosts de Usuário (uRLLC e eMBB):** `h_uRLLC1`, `h_eMBB1`, `h_uRLLC2`, `h_eMBB2` conectados a switches de acesso.
- **Switches de Acesso (OVSKernelSwitch):** `s_access1`, `s_access2`.
- **Roteadores da Rede de Transporte (LinuxRouter):** `r_trans1`, `r_trans2`, `r_trans3`, `r_trans4`. Estes roteadores atuam como a espinha dorsal da rede, onde as políticas de QoS são aplicadas.
- **Host de Nuvem (`h_cloud`):** Simula um servidor remoto que recebe ambos os tipos de tráfego (eMBB e uRLLC).

As configurações de largura de banda para os links são:
- Links de Acesso: 50 Mbps
- Links de Transporte: 100 Mbps
- Link para a Nuvem: 200 Mbps

<img src="./ppgti-redes/topology_diagram.png" alt="Diagrama da Topologia" width="700">

## Funcionalidades Implementadas

1.  **Geração de Tráfego:**
    * **uRLLC:** Tráfego UDP de baixa taxa de bits, mas com requisitos estritos de latência, simulado por `h_uRLLC2` para `h_cloud`.
    * **eMBB:** Tráfego UDP de alta largura de banda (45 Mbps), simulado por `h_eMBB1` para `h_cloud`.
2.  **Monitoramento de Latência uRLLC:** Um script (`gerador_monitor_uRLLC.py`) executa pings periódicos de `h_uRLLC1` para `h_cloud` e registra a latência. Se a latência exceder um limiar (5ms), um arquivo de alerta (`latencia.alerta`) é criado.
3.  **Controlador de QoS Dinâmico:** Um controlador (`controlador_qos.py`) monitora a existência do arquivo `latencia.alerta`.
    * **Ativação de QoS:** Se o arquivo de alerta é detectado, o controlador aplica regras de QoS bidirecionais (HTB - Hierarchical Token Bucket + SFQ - Stochastic Fairness Queueing) nas interfaces dos roteadores de transporte.
        * **Priorização:** Tráfego uRLLC (porta 5202) e ICMP (ping) são priorizados.
        * **Modelagem de Tráfego:** As classes HTB são configuradas para garantir largura de banda mínima e máxima para os diferentes tipos de tráfego, com SFQ para justa alocação dentro de cada classe, mitigando o bufferbloat.
    * **Desativação de QoS:** Se o arquivo de alerta não for mais detectado após um período de normalização (70 segundos), as regras de QoS são removidas, retornando a rede ao seu estado padrão.
4.  **Geração de Gráficos:** Um script (`grafico_monitor_urllc_v3.py`) gera automaticamente gráficos (PNG, GIF, MP4) da latência uRLLC ao longo do tempo, indicando os períodos em que o QoS esteve ativo.

## Requisitos de Sistema

* **Sistema Operacional:** Ubuntu 20.04 LTS (recomendado) ou ambiente Linux compatível com Mininet.
* **Mininet:** Versão 2.3.0d1 ou superior.
* **Python 3:** Com as bibliotecas `matplotlib`, `pandas`, `numpy`.
* **iperf3:** Ferramenta para geração de tráfego.
* **ffmpeg:** Para a geração de vídeos MP4 a partir dos gráficos (opcional, mas recomendado para os resultados visuais).

## Preparação do Ambiente

1.  **Atualizar o Sistema:**
    ```bash
    sudo apt update && sudo apt upgrade -y
    ```

2.  **Instalar Mininet:**
    ```bash
    git clone [https://github.com/mininet/mininet](https://github.com/mininet/mininet)
    mininet/util/install.sh -a # Instala tudo (Mininet, Open vSwitch, etc.)
    ```

3.  **Instalar iperf3:**
    ```bash
    sudo apt install iperf3 -y
    ```

4.  **Instalar dependências Python:**
    ```bash
    pip install matplotlib pandas numpy
    ```
    *Se `pip` não for encontrado, instale-o:* `sudo apt install python3-pip -y`

5.  **Instalar FFmpeg (para geração de vídeo MP4):**
    ```bash
    sudo apt install ffmpeg -y
    ```

## Estrutura do Projeto
