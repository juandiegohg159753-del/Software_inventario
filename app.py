from flask import Flask, redirect, session, url_for
from controllers.usuario import usuarios_bp
from controllers.producto import productos_bp

app = Flask(__name__)
app.secret_key = "cambia-esta-clave-por-una-clave-privada-larga"

app.register_blueprint(usuarios_bp)
app.register_blueprint(productos_bp)

@app.route("/inventario")
def inventario():
    if "id_usuario" not in session:
        return redirect(url_for("usuarios.login"))

    return redirect(url_for("productos.consultar"))


if __name__ == "__main__":
    app.run(debug=True)
