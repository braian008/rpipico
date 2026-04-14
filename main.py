# (C) Copyright Peter Hinch 2017-2019.
# Released under the MIT licence.

from mqtt_as import MQTTClient
from mqtt_local import config
import uasyncio as asyncio
import dht, machine

# Configuración del sensor y del LED integrado de la Pico W / Pico 2W
d = dht.DHT22(machine.Pin(15))

mensajes_recibidos = []
evento_mensaje = asyncio.Event()

# Esta es la función que RECIBE los mensajes de MQTTX
def sub_cb(topic, msg, retained):
    # Decodificamos los bytes a texto para poder compararlos
    """topic_str = topic.decode()
    msg_str = msg.decode()"""
    mensajes_recibidos.append((topic.decode(), msg.decode()))
    evento_mensaje.set()
    #print('Mensaje recibido - Topic: {} -> Valor: {}'.format(topic_str, msg_str))
    
async def wifi_han(state):
    print('Wifi is ', 'up' if state else 'down')
    await asyncio.sleep(1)

# Al conectar, nos suscribimos a los tópicos que queremos escuchar
async def conn_han(client):
    # Mantenemos las suscripciones anteriores (opcional si solo publicas ahí)
    #await client.subscribe('ID_DEL_DISPOSITIVO_BRAIAN/temperatura', 1)
    #await client.subscribe('ID_DEL_DISPOSITIVO_BRAIAN/humedad', 1)
    
    # NUEVO: Nos suscribimos al tópico de control para recibir comandos
    await client.subscribe('ID_DEL_DISPOSITIVO_BRAIAN/control', 1)

async def main(client):
    await client.connect()
    await asyncio.sleep(2)  # Damos tiempo al broker
    
    while True:
        # El programa se queda aquí esperando a que el evento se active
        await evento_mensaje.wait()
        
        # Como el evento se activó, procesamos todos los mensajes en la lista
        while mensajes_recibidos:
            # Sacamos el primer mensaje que llegó a la lista
            topic, msg = mensajes_recibidos.pop(0)
            
            print('Procesando en el main - Tópico: {} -> Valor: {}'.format(topic, msg))
            
            # ¡Tu código secuencial va aquí!
            if msg == 'ON':
                print("Ejecutando ON...")
                await asyncio.sleep(1) # Puedes usar sleep sin problemas
                
            elif msg == 'OFF':
                print("Ejecutando OFF...")
        
        # Una vez que procesamos todo, limpiamos el evento para volver a dormir y esperar
        evento_mensaje.clear()


    """await client.connect()
    await asyncio.sleep(2)  # Damos tiempo al broker
    
    while True:
        try:
            d.measure()
            try:
                temperatura = d.temperature()
                await client.publish('ID_DEL_DISPOSITIVO_BRAIAN/temperatura', '{}'.format(temperatura), qos = 1)
            except OSError as e:
                print("Error: sin sensor temperatura")
                
            try:
                humedad = d.humidity()
                await client.publish('ID_DEL_DISPOSITIVO_BRAIAN/humedad', '{}'.format(humedad), qos = 1)
            except OSError as e:
                print("Error: sin sensor humedad")
                
        except OSError as e:
            print("Error: sin sensor")
            
        await asyncio.sleep(20)  # Publicamos cada 20 segundos
"""
# Define configuración
config['subs_cb'] = sub_cb
config['connect_coro'] = conn_han
config['wifi_coro'] = wifi_han
config['ssl'] = True

# Set up client
MQTTClient.DEBUG = True
client = MQTTClient(config)

try:
    asyncio.run(main(client))
finally:
    client.close()
    asyncio.new_event_loop()