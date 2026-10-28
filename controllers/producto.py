
from datetime import date
from decimal import Decimal, InvalidOperation

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for
)
from models.producto import (
    listar_productos,
    listar_categorias,
    listar_categorias_conservacion,
    listar_nombres_productos_conservacion,
    listar_productos_conservacion,
    listar_vidas_utiles,
    registrar_producto,
    modificar_producto,
    eliminar_producto,
    configurar_vida_util
)

productos_bp = Blueprint("productos", __name__)
ESTADOS_CONSERVACION = (
    "En seguimiento",
    "Próximo a revisión",
    "Requiere revisión",
    "Sin duración configurada"
)


@productos_bp.before_request
def verificar_permisos():
    if "id_usuario" not in session:
        return redirect(url_for("usuarios.login"))

    if (
        request.endpoint in (
            "productos.consultar",
            "productos.informe_conservacion"
        )
        and request.method == "GET"
    ):
        return None

    if session.get("rol", "").strip().lower() != "administrador":
        flash("No tienes permisos para realizar esta acción.", "error")
        return redirect(url_for("inventario"))

    return None


@productos_bp.route("/productos", methods=["GET"])
def consultar():
    return renderizar_inventario()


@productos_bp.route("/productos/informe-conservacion", methods=["GET"])
def informe_conservacion():
    nombre = request.args.get("nombre", "").strip()
    id_categoria = request.args.get("categoria", "").strip()
    estado = request.args.get("estado", "").strip()

    if id_categoria:
        try:
            id_categoria = str(int(id_categoria))
            if int(id_categoria) <= 0:
                raise ValueError
        except ValueError:
            flash("La categoría seleccionada no es válida.", "error")
            id_categoria = ""

    if estado and estado not in ESTADOS_CONSERVACION:
        flash("El estado seleccionado no es válido.", "error")
        estado = ""

    return renderizar_inventario(
        seccion_activa="informe",
        informe_nombre=nombre,
        informe_categoria=id_categoria,
        informe_estado=estado,
        resultados_informe=listar_productos_conservacion(
            nombre,
            id_categoria,
            estado
        )
    )


def renderizar_inventario(
    seccion_activa="consultar",
    informe_nombre="",
    informe_categoria="",
    informe_estado="",
    resultados_informe=None
):
    productos = listar_productos()
    categorias = listar_categorias()
    informe_productos = (
        listar_productos_conservacion()
        if resultados_informe is None
        else resultados_informe
    )

    return render_template(
        "index.html",
        productos=productos,
        categorias=categorias,
        seccion_activa=seccion_activa,
        informe_productos=informe_productos,
        informe_categorias=listar_categorias_conservacion(),
        informe_nombres=listar_nombres_productos_conservacion(),
        informe_nombre=informe_nombre,
        informe_categoria=informe_categoria,
        informe_estado=informe_estado,
        vidas_utiles=listar_vidas_utiles(),
        fecha_hoy=date.today().isoformat()
    )


@productos_bp.route("/productos/registrar", methods=["POST"])
def registrar():
    nombre = request.form.get("nombre", "").strip()
    descripcion = request.form.get("descripcion", "").strip()
    id_categoria = request.form.get("id_categoria", "").strip()
    cantidad = request.form.get("cantidad", "").strip()
    unidad = request.form.get("unidad", "").strip()

    if not nombre or not id_categoria or not cantidad or not unidad:
        flash("Completa los campos obligatorios.", "error")
        return redirect(url_for("inventario"))

    try:
        id_categoria = int(id_categoria)
        cantidad = float(cantidad)

        if cantidad < 0:
            flash("La cantidad no puede ser negativa.", "error")
            return redirect(url_for("inventario"))

    except ValueError:
        flash("La categoría o la cantidad no son válidas.", "error")
        return redirect(url_for("inventario"))

    exito, mensaje = registrar_producto(
        nombre,
        descripcion,
        id_categoria,
        cantidad,
        unidad
    )

    flash(mensaje, "success" if exito else "error")
    return redirect(url_for("inventario"))


@productos_bp.route("/productos/modificar", methods=["POST"])
def modificar():
    id_producto = request.form.get("id_producto", "").strip()
    nombre = request.form.get("nombre", "").strip()
    descripcion = request.form.get("descripcion", "").strip()
    id_categoria = request.form.get("id_categoria", "").strip()
    cantidad = request.form.get("cantidad", "").strip()
    unidad = request.form.get("unidad", "").strip()
    fecha_vencimiento = request.form.get("fecha_vencimiento", "").strip()

    if not all((id_producto, nombre, id_categoria, cantidad, unidad)):
        flash("Completa los campos obligatorios.", "error")
        return redirect(url_for("inventario"))

    try:
        id_producto = int(id_producto)
        id_categoria = int(id_categoria)
        cantidad = Decimal(cantidad)

        if id_producto <= 0 or id_categoria <= 0:
            raise ValueError
        if not cantidad.is_finite() or cantidad < 0:
            raise ValueError
        if cantidad > Decimal("9999999.999") or cantidad.as_tuple().exponent < -3:
            raise ValueError
    except (ValueError, InvalidOperation):
        flash("El producto, la categoría o la cantidad no son válidos.", "error")
        return redirect(url_for("inventario"))

    exito, mensaje = modificar_producto(
        id_producto,
        nombre,
        descripcion,
        id_categoria,
        cantidad,
        unidad,
        fecha_vencimiento
    )

    flash(mensaje, "success" if exito else "error")
    return redirect(url_for("inventario"))


@productos_bp.route("/productos/configurar-vida-util", methods=["POST"])
def configurar_duracion():
    nombre = request.form.get("nombre_producto", "").strip()
    dias = request.form.get("dias_vida_util", "").strip()

    if not nombre or not dias:
        flash("Indica el nombre del producto y los días de vida útil.", "error")
        return redirect(url_for("inventario"))

    try:
        dias = int(dias)
        if not 1 <= dias <= 3650:
            raise ValueError
    except ValueError:
        flash("Los días deben ser un número entero entre 1 y 3650.", "error")
        return redirect(url_for("inventario"))

    exito, mensaje = configurar_vida_util(nombre, dias)
    flash(mensaje, "success" if exito else "error")
    return redirect(url_for("inventario"))


@productos_bp.route("/productos/eliminar", methods=["POST"])
def eliminar():
    id_producto = request.form.get("id_producto", "").strip()

    try:
        id_producto = int(id_producto)
        if id_producto <= 0:
            raise ValueError
    except ValueError:
        flash("Selecciona un producto válido para eliminar.", "error")
        return redirect(url_for("inventario"))

    exito, mensaje = eliminar_producto(id_producto)
    flash(mensaje, "success" if exito else "error")
    return redirect(url_for("inventario"))
