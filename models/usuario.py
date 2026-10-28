from werkzeug.security import generate_password_hash, check_password_hash
from models.conexion import obtener_conexion


def registrar_usuario(nombre, correo, contrasena, rol="empleado"):
    if rol not in ("administrador", "empleado"):
        return False, "El rol seleccionado no es válido."

    conexion = obtener_conexion()

    if conexion is None:
        return False, "No se pudo conectar con la base de datos."

    cursor = None

    try:
        cursor = conexion.cursor()

        contrasena_hash = generate_password_hash(contrasena)

        sql = """
            INSERT INTO usuarios (nombre, correo, contrasena, rol)
            VALUES (%s, %s, %s, %s)
        """

        cursor.execute(sql, (nombre, correo, contrasena_hash, rol))
        conexion.commit()

        return True, "Usuario registrado correctamente."

    except Exception as error:
        conexion.rollback()

        if getattr(error, "errno", None) == 1062:
            return False, "Este correo ya está registrado."

        print(f"Error al registrar usuario: {error}")
        return False, "No fue posible registrar el usuario."

    finally:
        if cursor is not None:
            cursor.close()
        conexion.close()


def verificar_usuario(correo, contrasena):
    conexion = obtener_conexion()

    if conexion is None:
        return None

    cursor = None

    try:
        cursor = conexion.cursor(dictionary=True)

        sql = """
            SELECT id_usuario, nombre, correo, contrasena, rol
            FROM usuarios
            WHERE correo = %s
        """

        cursor.execute(sql, (correo,))
        usuario = cursor.fetchone()
        

        if usuario and check_password_hash(
            usuario["contrasena"], contrasena
        ):
            usuario.pop("contrasena")
            return usuario

        return None

    except Exception as error:
        print(f"Error al verificar usuario: {error}")
        return None

    finally:
        if cursor is not None:
            cursor.close()
        conexion.close()
