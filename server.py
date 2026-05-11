import socket
import threading
import mysql.connector
from pymongo import MongoClient
from datetime import datetime

HOST = '0.0.0.0'
PORT = 5000
clientes = []

# Conexion MySQL
db_mysql = mysql.connector.connect(
    host='localhost', user='root', password='1234567', database='practica'
)
cursor = db_mysql.cursor()

# Conexion MongoDB
mongo_client = MongoClient('mongodb://localhost:27017/')
db_mongo = mongo_client['practica']

def guardar_mensaje(nombre, contenido):
    # Guardar en MySQL
    cursor.execute('SELECT id FROM usuarios WHERE nombre = %s', (nombre,))
    usuario = cursor.fetchone()
    if usuario:
        id_usuario = usuario[0]
        cursor.execute(
            'INSERT INTO mensajes (id_usuario, contenido) VALUES (%s, %s)',
            (id_usuario, f'{nombre}: {contenido}')
        )
        db_mysql.commit()
    # Guardar en MongoDB
    db_mongo.usuarios.update_one(
        {'nombre': nombre},
        {'$push': {'mensajes': {'contenido': contenido, 'fecha': datetime.now()}}}
    )

def manejar_cliente(conn, addr):
    print(f'Nuevo cliente conectado: {addr}')
    nombre = conn.recv(1024).decode()
    clientes.append((conn, nombre))
    while True:
        try:
            data = conn.recv(1024).decode()
            if not data or data == 'salir':
                break
            mensaje = f'{nombre}: {data}'
            guardar_mensaje(nombre, data)
            print(f'({addr}): {mensaje}')
            for c, n in clientes:
                if c != conn:
                    c.sendall(mensaje.encode())
        except:
            break
    clientes.remove((conn, nombre))
    conn.close()

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()
print('Servidor multiusuario escuchando...')
while True:
    conn, addr = server.accept()
    t = threading.Thread(target=manejar_cliente, args=(conn, addr))
    t.daemon = True
    t.start()
