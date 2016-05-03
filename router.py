import sys
import os
import datetime
import time
import copy
from threading import Thread
from connection import *


class Router:
    def __init__(self, listen_port, neighbors):
        self.port = listen_port
        self.neighbors = neighbors
        self.addr = socket.gethostbyname(socket.gethostname())
        self.identifier = self.addr + ':' + str(self.port)

        self.nodes = {}
        self.nodes[self.identifier] = copy.deepcopy(neighbors)

    def start(self):
        send_socket = Connection.create_udp_socket()
        thread = Thread(target=self.listening_thread, args=())
        thread.daemon = True
        thread.start()

        while True:
            packet = self.create_packet()
            for identifier, node in self.neighbors.iteritems():
                destination_addr = node['addr']
                destination_port = node['port']
                Connection.udp_send(send_socket, packet, destination_addr, destination_port)
                # print 'Package has been sent to ' + destination_addr + ':' + str(destination_port) + '.'

            # print 'Now wait for 5 seconds...'
            # print ''
            time.sleep(5)

    def listening_thread(self):
        receive_socket = Connection.create_udp_socket()
        try:
            Connection.udp_bind(receive_socket, '', self.port)
        except Exception as e:
            print 'The port has been in use.'
            os._exit(1)
        while True:
            data_json = dict(Connection.receive(receive_socket))
            # print data_json
            updated = self.update_distance(data_json)
            if updated:
                self.print_table()

    def generate_identifier(self, addr, port):
        return addr + ':' + str(port)

    def create_packet(self):
        packet = {
            'addr': self.addr,
            'port': self.port,
            'table': self.nodes[self.identifier]
        }

        return packet

    def print_table(self):
        print_time = datetime.datetime.now()
        print 'Node ' + self.addr + ':' + str(self.port) + ' @ ' + str(print_time)
        print '{:<15} {:<5} {:<8} {:<9}'.format('host', 'port', 'distance', 'interface')
        for identifier, node in self.nodes[self.identifier].iteritems():
            print '{:<15} {:<5} {:<8} {:<9}'.format(node['addr'], node['port'], node['distance'], node['interface'])
        print ''

    def update_distance(self, data_json):
        updated = False

        source = data_json['addr']
        port = data_json['port']
        source_identifier = self.generate_identifier(source, port)
        source_interface = self.nodes[self.identifier][source_identifier]['interface']
        source_distance = self.nodes[self.identifier][source_identifier]['distance']

        self.nodes[source_identifier] = data_json['table']

        for identifier, node in data_json['table'].iteritems():
            if identifier == self.identifier:
                if self.nodes[self.identifier][source_identifier]['distance'] != node['distance']:
                    self.nodes[self.identifier][source_identifier]['distance'] = node['distance']

                    self.neighbors[source_identifier]['distance'] = node['distance']  # should update the distance for the neighbor

                    updated = True

            elif identifier not in self.nodes[self.identifier]:  # discover new node
                new_distance = source_distance + node['distance']
                self.nodes[self.identifier][identifier] = {
                    'addr': node['addr'],
                    'port': node['port'],
                    'distance': new_distance,
                    'interface': source_interface
                }
                updated = True

            else:  # existing node
                # new_distance = source_distance + node['distance']
                # if new_distance < self.nodes[identifier]['distance']:
                #     self.nodes[identifier]['distance'] = new_distance
                #     self.nodes[identifier]['interface'] = source_interface
                #     updated = True
                min_distance = sys.maxint
                # print 'identifier: ' + str(identifier)
                for neighbor_identifier, neighbor_node in self.neighbors.iteritems():
                    neighbor_cost = neighbor_node['distance']
                    # print 'neighbor_cost: ' + str(neighbor_cost)
                    # print 'neighbor_identifier: ' + str(neighbor_identifier)
                    if neighbor_identifier == identifier:  # e.g.: D_2002(2002)
                        new_distance = neighbor_cost
                        if new_distance < min_distance:
                            min_distance = new_distance
                    elif neighbor_identifier in self.nodes:
                        if identifier in self.nodes[neighbor_identifier]:
                            new_distance = neighbor_cost + self.nodes[neighbor_identifier][identifier]['distance']
                            if new_distance < min_distance:
                                min_distance = new_distance

                if min_distance != sys.maxint:
                    if min_distance != self.nodes[self.identifier][identifier]['distance']:
                        self.nodes[self.identifier][identifier]['distance'] = min_distance
                        self.nodes[self.identifier][identifier]['interface'] = source_interface

                        updated = True

        return updated



def main():
    try:
        if len(sys.argv) > 2:
            listen_port = int(sys.argv[1])
            neighbors = {}

            count = 2
            while count < len(sys.argv):
                string = sys.argv[count].split(':')

                addr = socket.gethostbyname(string[0])
                identifier = addr + ':' + string[1]  # e.g.: identifier = 128.59.16.1:2001
                neighbors[identifier] = {
                    'addr': addr,
                    'port': int(string[1]),
                    'distance': int(string[2]),
                    'interface': count-1
                }
                count += 1

            # print 'neighbors: ' + str(neighbors)

            router = Router(listen_port, neighbors)
            router.start()
        else:
            print """The command is invalid. Usage: python router.py listen_port interface1 interface2 [...]"""
    except KeyboardInterrupt:
        print 'Thanks for using the router. It is going to exit now.'
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)

if __name__ == "__main__":
    main()
