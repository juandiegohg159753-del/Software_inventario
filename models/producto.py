
from models.conexion import obtener_conexion


def listar_productos():
    conexion = obtener_conexion()

    if conexion is None:
        return []

    cursor = None

    try:
        cursor = conexion.cursor(dictionary=True)
        sql = """
            SELECT
                p.id_producto,
                p.nombre,
                p.descripcion,
                p.id_categoria,
                c.nombre AS categoria,
                p.cantidad,
                p.unidad,
                p.fecha_vencimiento,
                p.fecha_registro,
                v.dias_vida_util,
                DATE_ADD(
                    DATE(p.fecha_registro),
                    INTERVAL v.dias_vida_util DAY
                ) AS fecha_vencimiento_estimada
            FROM productos p
            INNER JOIN categorias c
                ON p.id_categoria = c.id_categoria
            LEFT JOIN vida_util_productos v
                ON LOWER(TRIM(v.nombre_producto)) = LOWER(TRIM(p.nombre))
            ORDER BY p.id_producto DESC
        """
        cursor.execute(sql)
        return cursor.fetchall()

    except Exception as error:
        print(f"Error al consultar productos: {error}")
        return []

    finally:
        if cursor is not None:
            cursor.close()
        conexion.close()


def listar_categorias():
    conexion = obtener_conexion()

    if conexion is None:
        return []

    cursor = None

    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT id_categoria, nombre
            FROM categorias
            ORDER BY nombre
        """)
        return cursor.fetchall()

    except Exception as error:
        print(f"Error al consultar categorías: {error}")
        return []

    finally:
        if cursor is not None:
            cursor.close()
        conexion.close()


def listar_categorias_conservacion():
    conexion = obtener_conexion()

    if conexion is None:
        return []

    cursor = None

    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT DISTINCT c.id_categoria, c.nombre
            FROM categorias c
            INNER JOIN productos p
                ON p.id_categoria = c.id_categoria
            WHERE LOWER(c.nombre) LIKE '%fruta%'
               OR LOWER(c.nombre) LIKE '%verdura%'
            ORDER BY c.nombre
        """)
        return cursor.fetchall()

    except Exception as error:
        print(f"Error al consultar categorías de conservación: {error}")
        return []

    finally:
        if cursor is not None:
            cursor.close()
        conexion.close()


def listar_nombres_productos_conservacion():
    conexion = obtener_conexion()

    if conexion is None:
        return []

    cursor = None

    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT DISTINCT p.nombre
            FROM productos p
            INNER JOIN categorias c
                ON c.id_categoria = p.id_categoria
            WHERE LOWER(c.nombre) LIKE '%fruta%'
               OR LOWER(c.nombre) LIKE '%verdura%'
            ORDER BY p.nombre
        """)
        return cursor.fetchall()

    except Exception as error:
        print(f"Error al consultar productos de conservación: {error}")
        return []

    finally:
        if cursor is not None:
            cursor.close()
        conexion.close()


def listar_productos_conservacion(nombre="", id_categoria="", estado=""):
    conexion = obtener_conexion()

    if conexion is None:
        return []

    cursor = None

    try:
        cursor = conexion.cursor(dictionary=True)
        sql = """
            SELECT
                p.id_producto,
                p.nombre,
                c.nombre AS categoria,
                c.id_categoria,
                p.cantidad,
                p.unidad,
                DATE(p.fecha_registro) AS fecha_ingreso,
                DATEDIFF(CURRENT_DATE, DATE(p.fecha_registro)) AS dias_transcurridos,
                v.dias_vida_util,
                DATE_ADD(
                    DATE(p.fecha_registro),
                    INTERVAL v.dias_vida_util DAY
                ) AS fecha_estimada_revision,
                CASE
                    WHEN v.dias_vida_util IS NULL THEN 'Sin duración configurada'
                    WHEN DATEDIFF(CURRENT_DATE, DATE(p.fecha_registro))
                         >= v.dias_vida_util THEN 'Requiere revisión'
                    WHEN DATEDIFF(CURRENT_DATE, DATE(p.fecha_registro))
                         >= CEIL(v.dias_vida_util * 0.8) THEN 'Próximo a revisión'
                    ELSE 'En seguimiento'
                END AS estado
            FROM productos p
            INNER JOIN categorias c
                ON c.id_categoria = p.id_categoria
            LEFT JOIN vida_util_productos v
                ON LOWER(TRIM(v.nombre_producto)) = LOWER(TRIM(p.nombre))
            WHERE (
                LOWER(c.nombre) LIKE '%fruta%'
                OR LOWER(c.nombre) LIKE '%verdura%'
            )
        """
        parametros = []

        if nombre:
            sql += " AND p.nombre LIKE %s"
            parametros.append(f"%{nombre}%")

        if id_categoria:
            sql += " AND c.id_categoria = %s"
            parametros.append(id_categoria)

        if estado:
            sql += " HAVING estado = %s"
            parametros.append(estado)

        sql += " ORDER BY fecha_estimada_revision IS NULL, fecha_estimada_revision, p.nombre"
        cursor.execute(sql, tuple(parametros))
        return cursor.fetchall()

    except Exception as error:
        print(f"Error al consultar informe de conservación: {error}")
        return []

    finally:
        if cursor is not None:
            cursor.close()
        conexion.close()


def registrar_producto(nombre, descripcion, id_categoria, cantidad, unidad):
    conexion = obtener_conexion()

    if conexion is None:
        return False, "No se pudo conectar con la base de datos."

    cursor = None

    try:
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT dias_vida_util
            FROM vida_util_productos
            WHERE LOWER(TRIM(nombre_producto)) = LOWER(TRIM(%s))
            LIMIT 1
        """, (nombre,))
        vida_util = cursor.fetchone()
        vida_util_dias = vida_util[0] if vida_util else None

        sql = """
            INSERT INTO productos
                (nombre, descripcion, id_categoria, cantidad, unidad)
            VALUES (%s, %s, %s, %s, %s)
        """

        cursor.execute(sql, (
            nombre,
            descripcion or None,
            id_categoria,
            cantidad,
            unidad
        ))

        conexion.commit()
        if vida_util_dias is None:
            return True, (
                "Producto registrado. No tiene duración estimada configurada; "
                "agrégala en Informe de Vencimientos."
            )
        return True, "Producto registrado correctamente."

    except Exception as error:
        conexion.rollback()
        print(f"Error al registrar producto: {error}")
        return False, "No fue posible registrar el producto."

    finally:
        if cursor is not None:
            cursor.close()
        conexion.close()


def modificar_producto(id_producto, nombre, descripcion, id_categoria,
                       cantidad, unidad, fecha_vencimiento):
    conexion = obtener_conexion()

    if conexion is None:
        return False, "No se pudo conectar con la base de datos."

    cursor = None

    try:
        cursor = conexion.cursor()
        cursor.execute("""
            UPDATE productos
            SET nombre = %s,
                descripcion = %s,
                id_categoria = %s,
                cantidad = %s,
                unidad = %s,
                fecha_vencimiento = %s
            WHERE id_producto = %s
        """, (
            nombre,
            descripcion or None,
            id_categoria,
            cantidad,
            unidad,
            fecha_vencimiento or None,
            id_producto
        ))

        if cursor.rowcount == 0:
            cursor.execute(
                "SELECT 1 FROM productos WHERE id_producto = %s",
                (id_producto,)
            )
            if cursor.fetchone() is None:
                conexion.rollback()
                return False, "El producto seleccionado no existe."

        conexion.commit()
        return True, "Producto modificado correctamente."

    except Exception as error:
        conexion.rollback()
        print(f"Error al modificar producto: {error}")
        return False, "No fue posible modificar el producto."

    finally:
        if cursor is not None:
            cursor.close()
        conexion.close()


def listar_vidas_utiles():
    conexion = obtener_conexion()

    if conexion is None:
        return []

    cursor = None

    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT DISTINCT v.nombre_producto, v.dias_vida_util
            FROM vida_util_productos v
            INNER JOIN productos p
                ON LOWER(TRIM(p.nombre)) = LOWER(TRIM(v.nombre_producto))
            INNER JOIN categorias c
                ON c.id_categoria = p.id_categoria
            WHERE LOWER(c.nombre) LIKE '%fruta%'
               OR LOWER(c.nombre) LIKE '%verdura%'
            ORDER BY v.nombre_producto
        """)
        return cursor.fetchall()

    except Exception as error:
        print(f"Error al consultar vidas útiles: {error}")
        return []

    finally:
        if cursor is not None:
            cursor.close()
        conexion.close()


def configurar_vida_util(nombre_producto, dias_vida_util):
    conexion = obtener_conexion()

    if conexion is None:
        return False, "No se pudo conectar con la base de datos."

    cursor = None

    try:
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT 1
            FROM productos p
            INNER JOIN categorias c
                ON c.id_categoria = p.id_categoria
            WHERE LOWER(TRIM(p.nombre)) = LOWER(TRIM(%s))
              AND (
                  LOWER(c.nombre) LIKE '%fruta%'
                  OR LOWER(c.nombre) LIKE '%verdura%'
              )
            LIMIT 1
        """, (nombre_producto,))
        if cursor.fetchone() is None:
            conexion.rollback()
            return False, "Solo puedes configurar productos registrados de frutas y verduras."

        cursor.execute("""
            INSERT INTO vida_util_productos (nombre_producto, dias_vida_util)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE dias_vida_util = VALUES(dias_vida_util)
        """, (nombre_producto, dias_vida_util))
        conexion.commit()
        return True, "Duración predeterminada guardada para este producto."

    except Exception as error:
        conexion.rollback()
        print(f"Error al configurar vida útil: {error}")
        return False, "No fue posible guardar la duración predeterminada."

    finally:
        if cursor is not None:
            cursor.close()
        conexion.close()


def eliminar_producto(id_producto):
    conexion = obtener_conexion()

    if conexion is None:
        return False, "No se pudo conectar con la base de datos."

    cursor = None

    try:
        cursor = conexion.cursor()
        cursor.execute(
            "DELETE FROM productos WHERE id_producto = %s",
            (id_producto,)
        )

        if cursor.rowcount == 0:
            conexion.rollback()
            return False, "El producto seleccionado no existe."

        conexion.commit()
        return True, "Producto eliminado correctamente."

    except Exception as error:
        conexion.rollback()
        print(f"Error al eliminar producto: {error}")
        return False, "No fue posible eliminar el producto."

    finally:
        if cursor is not None:
            cursor.close()
        conexion.close()
