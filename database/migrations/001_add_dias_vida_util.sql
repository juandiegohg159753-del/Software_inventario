ALTER TABLE productos
    ADD COLUMN IF NOT EXISTS dias_vida_util INT UNSIGNED NULL
    AFTER fecha_vencimiento;

CREATE TABLE IF NOT EXISTS vida_util_productos (
    id_vida_util INT UNSIGNED NOT NULL AUTO_INCREMENT,
    nombre_producto VARCHAR(150) NOT NULL,
    dias_vida_util INT UNSIGNED NOT NULL,
    PRIMARY KEY (id_vida_util),
    UNIQUE KEY uq_vida_util_nombre_producto (nombre_producto)
);
