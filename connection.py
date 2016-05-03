import socket
import json
import ast


class Connection:
    @staticmethod
    def create_udp_socket():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            return s
        except Exception as e:
            print 'Failed to create the UDP connection: ' + e.message
            raise

    @staticmethod
    def udp_bind(s, host, port):
        try:
            s.bind((host, port))
        except Exception as e:
            print 'Failed to bind on port: ' + str(port)
            raise

    @staticmethod
    def receive(s):
        try:
            data = s.recvfrom(65535)[0]
            # data_json = json.loads(data)
            data_json = ast.literal_eval(data)
            return data_json
        except:
            print 'Failed to receive data.'
            raise

    @staticmethod
    def udp_send(s, data, host, port):
        # data_json = json.dumps(data)
        data_json  = str(data)
        s.sendto(data_json, (host, port))