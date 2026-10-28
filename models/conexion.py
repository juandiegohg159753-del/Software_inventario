import mysql.connector
from mysql.connector import Error

def obtener_conexion():
    try:
        conexion = mysql.connector.connect(
            host="localhost",
            port=3307,
            user="root",
            password="",
            database="fruver"
        )

        if conexion.is_connected():
            return conexion

    except Error as error:
        print(f"Error al conectar con la base de datos: {error}")

    return None
