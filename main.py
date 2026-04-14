from mqtt_as import MQTTClient
from mqtt_local import config
import uasyncio as asyncio
import dht, machine
from machine import Pin
import network
import ubinascii


device_id=ubinascii.hexlify(machine.unique_id()).decode()
print(device_id)
# Configuración de Hardware
d = dht.DHT22(machine.Pin(15))
led_board = Pin("LED", Pin.OUT)
rele_control = machine.Pin(16, machine.Pin.OUT)
rele_control.value(1) # Iniciamos relé apagado (depende de tu relé)

# Variables de control
mensajes_recibidos = []
evento_mensaje = asyncio.Event()
modo = "manual"  # Asegúrate de que sea minúscula para coincidir con la evaluación
setpoint= 25

# Función de destello corregida para no bloquear el sistema
async def destello():
    print("LED destellando...")
    led_board.on()
    await asyncio.sleep(1) # Usamos asyncio.sleep en lugar de time.sleep
    led_board.off()
    print("Listo")

def sub_cb(topic, msg, retained):
    mensajes_recibidos.append((topic.decode(), msg.decode()))
    evento_mensaje.set()

async def wifi_han(state):
    print('Wifi is ', 'up' if state else 'down')
    await asyncio.sleep(1)

async def conn_han(client):
    # Suscripciones
    await client.subscribe('ID_DEL_DISPOSITIVO_BRAIAN/control', 1)

# TAREA 1: Procesar mensajes de MQTTX (Lectura)
async def procesar_mensajes():
    global modo
    while True:
        await evento_mensaje.wait()
        while mensajes_recibidos:
            topic, msg = mensajes_recibidos.pop(0)
            msg = msg.lower().strip() # Limpiamos el mensaje
            
            print('Comando recibido:', msg)
            
            if msg == 'destello':
                await destello() # Llamamos a la función asíncrona
            
            elif msg == 'relé' and modo == "manual":
                rele_control.toggle()
                print("Relé cambiado a:", rele_control.value())
                
            elif msg == 'auto':
                modo = "auto"
                print("Modo cambiado a AUTOMÁTICO")
                
            elif msg == 'manual':
                modo = "manual"
                print("Modo cambiado a MANUAL")

        evento_mensaje.clear()

# TAREA 2: Leer sensores y enviar datos (Escritura)
async def enviar_sensores(client):
    while True:
        try:
            d.measure()
            t = d.temperature()
            h = d.humidity()
            
            if modo == "auto":
                if t > setpoint:
                    rele_control.value(0) # Apaga si sobrepasa
                    print("   [AUTO] Temperatura ALTA: Relé en 0")
                else:
                    rele_control.value(1) # Enciende si está por debajo
                    print("   [AUTO] Temperatura OK/BAJA: Relé en 1")

            print("Publicando: T:{}°C, H:{}%".format(t, h))
            
            # Publicamos en los tópicos correspondientes
            await client.publish('ID_DEL_DISPOSITIVO_BRAIAN/temperatura', str(t), qos=1)
            await client.publish('ID_DEL_DISPOSITIVO_BRAIAN/humedad', str(h), qos=1)
            
        except OSError:
            print("Error leyendo el sensor DHT22")
            
        # Espera 30 segundos antes de la siguiente lectura
        await asyncio.sleep(30)

async def main(client):
    await client.connect()
    # Ejecutamos ambas tareas al mismo tiempo
    await asyncio.gather(procesar_mensajes(), enviar_sensores(client))

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