import network
import utime
from machine import UART, Pin
from umqtt.simple import MQTTClient
import ujson as json

# Configurações do WiFi
SSID = "SSID"
PASSWORD = "PASSWORD"

# Configurações do MQTT
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "v1/devices/me/telemetry"
MQTT_CLIENT_ID = "trash_truck"
MQTT_USER = "trash_truck"
MQTT_PASSWORD = "trash_truck_porto"

# Configurações do GPS
GPS_TX_PIN = 17
GPS_RX_PIN = 16

# Conectando ao WiFi
def connect_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    
    while not wlan.isconnected():
        utime.sleep(1)
    
    print('Conexão WiFi estabelecida. IP:', wlan.ifconfig()[0])

# Inicializando o GPS
def init_gps(tx_pin, rx_pin):
    uart = UART(2, baudrate=9600, tx=tx_pin, rx=rx_pin)
    return uart

# Lendo dados do GPS
def read_gps_data(uart):
    buffer = uart.readline()
    if buffer is not None:
        try:
            data = buffer.decode('utf-8')
            if '$GPGGA' in data:
                parts = data.split(',')
                latitude = convert_to_decimal_degrees(parts[2], parts[3])
                longitude = convert_to_decimal_degrees(parts[4], parts[5])
                return latitude, longitude, parts[1]  # Latitude, Longitude, Hora UTC
        except Exception as e:
            print("Erro ao ler dados do GPS:", e)
    return None, None, None

# Convertendo coordenadas do GPS para graus decimais
def convert_to_decimal_degrees(value, direction):
    degrees = float(value[:2])
    minutes = float(value[2:])
    result = degrees + minutes / 60
    if direction == 'S' or direction == 'W':
        result = -result
    return result

# Conectando ao MQTT
def connect_mqtt():
    client = MQTTClient(client_id=MQTT_CLIENT_ID, server=MQTT_BROKER, port=MQTT_PORT, user=MQTT_USER, password=MQTT_PASSWORD)
    try:
        client.connect()
        print("Conectado ao broker MQTT")
        return client
    except OSError as e:
        print("Erro ao conectar ao broker MQTT:", e)
        return None

# Função principal
def main():
    connect_wifi(SSID, PASSWORD)
    
    uart = init_gps(GPS_TX_PIN, GPS_RX_PIN)
    client = connect_mqtt()
    
    while True:
        latitude, longitude, utc_time = read_gps_data(uart)
        
        if latitude is not None and longitude is not None:
            payload = {
                "latitude": latitude,
                "longitude": longitude,
                "timestamp": utc_time
            }
            
            client.publish(MQTT_TOPIC, json.dumps(payload))
            print("Dados enviados:", payload)
        
        utime.sleep(10)

if __name__ == "__main__":
    main()
