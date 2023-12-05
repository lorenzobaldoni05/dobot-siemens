from opcua import Client, ua


class Opcua:
    def __init__(self, url, username='', password='', timeout_ms=30000):
        self.client = Client(url)
        self.client.session_timeout = timeout_ms
        # self.client.set_user(username)
        # self.client.set_password(password)

    # connect opcua client
    def client_connect(self):
        try:
            self.client.connect()
        except:
            raise Exception('Failed to connect opcua client')

    # disconnect opcua client
    def client_disconnect(self):
        self.client.disconnect()

    # read value via opcua
    def read_value(self, node_id):
        client_node = self.client.get_node(node_id)  # get node
        client_node_value = client_node.get_value()  # read node value
        client_node_data_type = client_node.get_data_type()
        print("Value of : " + str(client_node) + ' : ' + str(client_node_value))
        return client_node_data_type, client_node_value

    # write value via opcua
    def write_value(self, node_id, data_type, value):
        client_node = self.client.get_node(node_id)  # get node
        client_node_dv = ua.DataValue(ua.Variant(value, ua.VariantType[data_type]))
        client_node.set_value(client_node_dv)
        print("Value of : " + str(client_node) + ' : ' + str(value))
