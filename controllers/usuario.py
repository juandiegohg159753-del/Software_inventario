from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models.usuario import registrar_usuario, verificar_usuario

usuarios_bp = Blueprint("usuarios", __name__)


@usuarios_bp.route("/registro", methods=["GET", "POST"])
def registro():
    if (
        "id_usuario" in session
        and session.get("rol", "").strip().lower() != "administrador"
    ):
        flash("Solo un administrador puede registrar usuarios.", "error")
        return redirect(url_for("inventario"))

    if request.method == "POST":
        correo = request.form.get("correo", "").strip().lower()
        contrasena = request.form.get("contrasena", "")
        confirmacion = request.form.get("confirm_password", "")
        rol_solicitado = request.form.get("rol", "empleado").strip().lower()

        if not correo or not contrasena:
            flash("Completa todos los campos obligatorios.", "error")
            return redirect(url_for("usuarios.registro"))

        if contrasena != confirmacion:
            flash("Las contraseñas no coinciden.", "error")
            return redirect(url_for("usuarios.registro"))

        if len(contrasena) < 8:
            flash("La contraseña debe tener al menos 8 caracteres.", "error")
            return redirect(url_for("usuarios.registro"))

        if rol_solicitado not in ("administrador", "empleado"):
            flash("Selecciona un rol válido.", "error")
            return redirect(url_for("usuarios.registro"))

        es_administrador = (
            "id_usuario" in session
            and session.get("rol", "").strip().lower() == "administrador"
        )
        rol = rol_solicitado if es_administrador else "empleado"

        exito, mensaje = registrar_usuario(correo, correo, contrasena, rol)
        flash(mensaje, "success" if exito else "error")

        if exito:
            if es_administrador:
                return redirect(url_for("inventario"))
            return redirect(url_for("usuarios.login"))

    return render_template("register.html")


@usuarios_bp.route("/", methods=["GET", "POST"])
@usuarios_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        correo = request.form.get("correo", "").strip().lower()
        contrasena = request.form.get("contrasena", "")

        if not correo or not contrasena:
            flash("Ingresa tu correo y contraseña.", "error")
            return redirect(url_for("usuarios.login"))

        usuario = verificar_usuario(correo, contrasena)

        if usuario:
            session.clear()
            session["id_usuario"] = usuario["id_usuario"]
            session["nombre"] = usuario["nombre"]
            session["rol"] = usuario["rol"]

            return redirect(url_for("inventario"))

        flash("Correo o contraseña incorrectos.", "error")

    return render_template("login.html")



@usuarios_bp.route("/cerrar-sesion")
def cerrar_sesion():
    session.clear()
    return redirect(url_for("usuarios.login"))
