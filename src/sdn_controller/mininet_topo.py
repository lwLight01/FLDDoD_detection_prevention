from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController, OVSKernelSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel

class DDoSTopo(Topo):
    def build(self):
        # Create core switch
        s1 = self.addSwitch('s1', cls=OVSKernelSwitch, protocols='OpenFlow13')
        
        # Create edge nodes (simulating federated clients and targets)
        h1 = self.addHost('h1', ip='10.0.0.1')
        h2 = self.addHost('h2', ip='10.0.0.2')
        h3 = self.addHost('h3', ip='10.0.0.3')
        
        # Create attacker node
        h4 = self.addHost('h4', ip='10.0.0.4')
        
        # Connect hosts to switch
        self.addLink(h1, s1)
        self.addLink(h2, s1)
        self.addLink(h3, s1)
        self.addLink(h4, s1)

def run_mininet():
    setLogLevel('info')
    topo = DDoSTopo()
    # Ensure it connects to Ryu on default port 6653
    net = Mininet(topo=topo, controller=lambda name: RemoteController(name, ip='127.0.0.1', port=6653), switch=OVSKernelSwitch)
    net.start()
    CLI(net)
    net.stop()

if __name__ == '__main__':
    run_mininet()
