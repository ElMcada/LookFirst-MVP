-- LookFirst · Esquema PostgreSQL (generado desde los modelos ORM; referencia para pgAdmin)
-- El backend lo crea solo al arrancar. Un esquema por bounded context.

CREATE SCHEMA IF NOT EXISTS iam;
CREATE SCHEMA IF NOT EXISTS catalogo;
CREATE SCHEMA IF NOT EXISTS consulta;

CREATE TYPE iam.rol_usuario AS ENUM ('admin', 'estilista');

CREATE TYPE catalogo.tipo_servicio AS ENUM ('corte', 'tinte');

CREATE TYPE catalogo.tipo_corte AS ENUM ('conservar', 'calvo', 'corto', 'medio', 'largo');

CREATE TYPE catalogo.forma_rostro AS ENUM ('ovalado', 'redondo', 'cuadrado', 'alargado');

CREATE TYPE consulta.estado_consulta AS ENUM ('activa', 'finalizada', 'cancelada', 'expirada');

CREATE TYPE consulta.origen_solicitud AS ENUM ('catalogo', 'texto', 'voz');

CREATE TYPE consulta.tipo_corte AS ENUM ('conservar', 'calvo', 'corto', 'medio', 'largo');

CREATE TYPE consulta.fuente_prompt AS ENUM ('catalogo', 'llm', 'palabras_clave');

CREATE TYPE consulta.modo_simulacion AS ENUM ('ia_generativa', 'respaldo_local');

CREATE TABLE iam.usuarios (
	id UUID NOT NULL, 
	nombre VARCHAR(120) NOT NULL, 
	email VARCHAR(254) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	rol iam.rol_usuario NOT NULL, 
	activo BOOLEAN NOT NULL, 
	creado_en TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (email)
);

COMMENT ON TABLE iam.usuarios IS 'Personal del salón (administrador y estilistas)';

COMMENT ON COLUMN iam.usuarios.email IS 'Siempre en minúsculas';

COMMENT ON COLUMN iam.usuarios.password_hash IS 'scrypt; nunca la contraseña en claro';

CREATE TABLE catalogo.estilos (
	id UUID NOT NULL, 
	codigo VARCHAR(60) NOT NULL, 
	nombre VARCHAR(80) NOT NULL, 
	tipo catalogo.tipo_servicio NOT NULL, 
	descripcion TEXT NOT NULL, 
	prompt_en VARCHAR(400) NOT NULL, 
	tipo_corte catalogo.tipo_corte NOT NULL, 
	color_hex VARCHAR(7), 
	degradado BOOLEAN NOT NULL, 
	activo BOOLEAN NOT NULL, 
	creado_en TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	actualizado_en TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_estilos_color_hex CHECK (color_hex IS NULL OR color_hex ~ '^#[0-9A-F]{6}$'), 
	CONSTRAINT ck_estilos_tinte_conserva CHECK ((tipo = 'tinte') = (tipo_corte = 'conservar')), 
	CONSTRAINT ck_estilos_tinte_color CHECK (tipo <> 'tinte' OR color_hex IS NOT NULL), 
	UNIQUE (codigo)
);

COMMENT ON TABLE catalogo.estilos IS 'Servicios de corte y tinte que el salón ofrece (REQ-10)';

COMMENT ON COLUMN catalogo.estilos.prompt_en IS 'Descripción técnica para el modelo de inpainting';

COMMENT ON COLUMN catalogo.estilos.degradado IS 'Balayage/ombré: color más intenso en puntas';

COMMENT ON COLUMN catalogo.estilos.activo IS 'Se desactiva en vez de borrar';

CREATE TABLE catalogo.estilo_formas_rostro (
	estilo_id UUID NOT NULL, 
	forma catalogo.forma_rostro NOT NULL, 
	PRIMARY KEY (estilo_id, forma), 
	FOREIGN KEY(estilo_id) REFERENCES catalogo.estilos (id) ON DELETE CASCADE
);

CREATE TABLE consulta.consultas (
	id UUID NOT NULL, 
	estilista_id UUID NOT NULL, 
	estado consulta.estado_consulta NOT NULL, 
	consentimiento_version VARCHAR(20) NOT NULL, 
	consentimiento_otorgado_en TIMESTAMP WITH TIME ZONE NOT NULL, 
	iniciada_en TIMESTAMP WITH TIME ZONE NOT NULL, 
	finalizada_en TIMESTAMP WITH TIME ZONE, 
	datos_eliminados_en TIMESTAMP WITH TIME ZONE, 
	satisfaccion SMALLINT, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_consultas_satisfaccion CHECK (satisfaccion BETWEEN 1 AND 10), 
	CONSTRAINT ck_consultas_cierre CHECK ((estado = 'activa') = (finalizada_en IS NULL)), 
	CONSTRAINT ck_consultas_borrado CHECK (finalizada_en IS NULL OR datos_eliminados_en IS NOT NULL), 
	CONSTRAINT ck_consultas_satisfaccion_estado CHECK (satisfaccion IS NULL OR estado = 'finalizada'), 
	FOREIGN KEY(estilista_id) REFERENCES iam.usuarios (id) ON DELETE RESTRICT
);

CREATE INDEX ix_consultas_activas ON consulta.consultas (iniciada_en) WHERE estado = 'activa';

CREATE INDEX ix_consultas_estilista_fecha ON consulta.consultas (estilista_id, iniciada_en);

COMMENT ON TABLE consulta.consultas IS 'Consultas de asesoría (anónimas, sin datos biométricos)';

COMMENT ON COLUMN consulta.consultas.consentimiento_version IS 'Versión del texto legal aceptado';

COMMENT ON COLUMN consulta.consultas.datos_eliminados_en IS 'Constancia de borrado de la foto (REQ-09)';

COMMENT ON COLUMN consulta.consultas.satisfaccion IS '1-10, KPI OE4 (> 8)';

CREATE TABLE consulta.simulaciones (
	id UUID NOT NULL, 
	consulta_id UUID NOT NULL, 
	origen consulta.origen_solicitud NOT NULL, 
	estilo_id UUID, 
	instruccion VARCHAR(300), 
	tipo_corte consulta.tipo_corte NOT NULL, 
	fuente_prompt consulta.fuente_prompt NOT NULL, 
	modo consulta.modo_simulacion NOT NULL, 
	latencia_ms INTEGER NOT NULL, 
	creada_en TIMESTAMP WITH TIME ZONE NOT NULL, 
	elegida_en TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_simulaciones_latencia CHECK (latencia_ms >= 0), 
	CONSTRAINT ck_simulaciones_estilo CHECK ((origen = 'catalogo') = (estilo_id IS NOT NULL)), 
	CONSTRAINT ck_simulaciones_instruccion CHECK (origen = 'catalogo' OR instruccion IS NOT NULL), 
	FOREIGN KEY(consulta_id) REFERENCES consulta.consultas (id) ON DELETE CASCADE, 
	FOREIGN KEY(estilo_id) REFERENCES catalogo.estilos (id) ON DELETE RESTRICT
);

CREATE UNIQUE INDEX uq_simulaciones_elegida ON consulta.simulaciones (consulta_id) WHERE elegida_en IS NOT NULL;

CREATE INDEX ix_simulaciones_creada ON consulta.simulaciones (creada_en);

CREATE INDEX ix_consulta_simulaciones_consulta_id ON consulta.simulaciones (consulta_id);

COMMENT ON COLUMN consulta.simulaciones.instruccion IS 'Texto o voz transcrita del pedido';

COMMENT ON COLUMN consulta.simulaciones.elegida_en IS 'Momento en que el cliente decidió';
