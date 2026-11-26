# LookFirst MVP

Simulación de cortes y tintes sobre el rostro real del cliente, por catálogo, texto o voz, para alinear expectativas entre estilista y cliente antes del servicio.

## Cómo ejecutarlo

**0. PostgreSQL** (una sola vez). Pon la contraseña de tu usuario `postgres` (la misma de pgAdmin) en `backend/.env`:

```
DATABASE_URL=postgresql+psycopg://postgres:TU_CONTRASEÑA@localhost:5432/lookfirst
```

No hace falta crear nada en pgAdmin: al arrancar, el backend crea la base `lookfirst`, los esquemas, las tablas, el catálogo inicial y el primer administrador (`ADMIN_EMAIL` / `ADMIN_PASSWORD` del `.env`). Si la contraseña tiene `@`, `:`, `/` o `#`, escríbela codificada (`@` → `%40`, `#` → `%23`).

**1. Google Colab (IA generativa).** Entorno de ejecución → Cambiar tipo → **GPU T4**. Pega [colab/servidor_inpainting.py](colab/servidor_inpainting.py) en una celda y ejecútala. Copia la URL que imprime en `COLAB_URL` del `.env` (cambia en cada ejecución). Sin Colab la app funciona igual en *modo respaldo* (solo color).

**2. Backend** (terminal 1):

```powershell
cd backend
py -m venv venv                      # solo la primera vez
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt      # solo la primera vez o si cambian dependencias
copy _.env.example .env              # solo la primera vez, luego complétalo
uvicorn main:app --reload --port 8000
```

Comprueba en http://localhost:8000/health (`"base_datos": true`) y explora la API en http://localhost:8000/docs.

**3. Frontend Angular** (terminal 2). Requiere Node 20.19 o superior (probado con Node 24):

```powershell
cd frontend
npm install          # solo la primera vez o si cambian dependencias
npm start            # abre en http://localhost:4200
```

Pantallas: **Consulta** e **Indicadores** para todo el personal (el estilista ve solo sus propias consultas); **Catálogo** y **Equipo** solo para el administrador.

Para desplegar: `npm run build` genera `frontend/dist/`. Si el backend no está en `localhost:8000`, define en `index.html` `<script>window.LOOKFIRST_API_URL = "https://tu-backend"</script>` y añade ese dominio a `CORS_ORIGINS` del backend.

**Pruebas:** backend `.\venv\Scripts\python.exe -m pytest -q` · frontend `npm test -- --watch=false`

---

## Arquitectura

Monolito modular con **Clean Architecture** y **DDD**: un módulo por *bounded context*, cada uno con las capas `domain → application → infrastructure → api/presentation`. Las dependencias siempre apuntan hacia el dominio; solo el *composition root* ([backend/app/bootstrap.py](backend/app/bootstrap.py) y [frontend/src/app/app.config.ts](frontend/src/app/app.config.ts)) conoce las implementaciones concretas.

### Bounded contexts

| BC | Tipo | Responsabilidad | Persistencia |
|---|---|---|---|
| **IAM** | Genérico | Cuentas del personal (admin / estilista), login, roles. Los clientes no tienen cuenta. | `iam.usuarios` |
| **Consulta** | Core | Agregado *Consulta*: consentimiento, ciclo de vida, looks probados, look elegido, satisfacción, borrado de la foto. Orquesta Catálogo y Simulación. | `consulta.consultas`, `consulta.simulaciones` |
| **Simulación** | Core | Motor de IA: análisis facial y segmentación (MediaPipe/CNN), intérprete de lenguaje natural (LLM + respaldo), inpainting (Colab) y tinte local. | Ninguna (solo memoria) |
| **Catálogo** | Soporte | Servicios que el salón ofrece (REQ-10) y reglas de visagismo (REQ-07). | `catalogo.estilos`, `catalogo.estilo_formas_rostro` |
| **Analítica** | Soporte | KPIs del OE4 y REQ-04. Modelo de **solo lectura** sobre las tablas de Consulta: no tiene tablas propias. | — |

Mapa de contextos: *Consulta* es cliente de *Catálogo* (a través de una capa anticorrupción, `ProveedorEstilosCatalogo`) y de *Simulación* (usa su servicio de aplicación). Todos dependen de *IAM* para autenticar. `shared/kernel.py` es el kernel compartido (`FormaRostro`, `TipoCorte`).

```
backend/app/
  shared/        config, BD, errores de dominio, kernel compartido
  iam/           domain/ application/ infrastructure/ api/
  catalogo/      domain/ application/ infrastructure/ api/
  simulacion/    domain/ application/ infrastructure/        (sin API propia)
  consulta/      domain/ application/ infrastructure/ api/
  analitica/     domain/ application/ infrastructure/ api/
  bootstrap.py   composition root
frontend/src/app/                     Angular 21 · standalone · signals · zoneless
  core/          configuración, cliente HTTP, interceptor de autenticación, errores
  shared/ui/     sistema de diseño: íconos, toasts, diálogos, logo
  layout/        barra de navegación (shell)
  iam/           domain/ application/ infrastructure/ presentation/   (login, equipo, guards)
  catalogo/      domain/ application/ infrastructure/ presentation/   (catálogo, tarjeta de estilo)
  consulta/      domain/ application/ infrastructure/ presentation/   (consulta, cámara, voz, comparador)
  analitica/     domain/ application/ infrastructure/ presentation/   (indicadores)
  app.config.ts  composition root: une cada puerto con su adaptador
```

En el frontend, los **puertos** son clases abstractas en `application/` (`ConsultaRepository`, `Camara`, `ReconocedorVoz`, `IamRepository`…), y los **adaptadores** viven en `infrastructure/` (HTTP, WebRTC, Web Speech API). Los componentes solo hablan con los *stores* y servicios de `application/`, nunca con `HttpClient` ni con las APIs del navegador. Así, los tests reemplazan el backend por un repositorio falso sin tocar la UI.

**Diseño:** sistema propio y minimalista en [frontend/src/styles.scss](frontend/src/styles.scss): tokens de color, tipografía Inter, bordes de 1 px, un solo color de acento y componentes base (botones, campos, tarjetas, insignias, tablas, diálogos nativos). La consulta guía al estilista con un indicador de pasos (consentimiento → foto → explorar looks → decisión), una guía en óvalo para encuadrar el rostro, un comparador antes/después y un historial de looks.

## Base de datos

PostgreSQL con **un esquema por bounded context** (`iam`, `catalogo`, `consulta`), visibles por separado en pgAdmin. El DDL completo está en [backend/db/schema.sql](backend/db/schema.sql) (generado desde los modelos ORM).

Cada tabla existe porque responde a un requisito, no porque haya un formulario:

| Tabla | Por qué existe |
|---|---|
| `iam.usuarios` | Autenticar y separar permisos (el dueño gestiona el catálogo; el estilista atiende). |
| `catalogo.estilos` | REQ-10: solo se recomiendan y simulan servicios que el salón realmente vende. |
| `catalogo.estilo_formas_rostro` | REQ-07: un estilo sirve para varias formas de rostro (relación N:M). |
| `consulta.consultas` | REQ-09: constancia del consentimiento y del borrado. OE4: duración y satisfacción. |
| `consulta.simulaciones` | REQ-04: latencia de cada simulación. OE4: cuánto tardó el cliente en elegir. |

**Lo que no se guarda nunca** (Ley N.° 29733): fotos, máscaras, landmarks, métricas faciales, forma del rostro ni datos que identifiquen al cliente. La foto vive solo en memoria RAM y se borra al finalizar la consulta, al retirar el consentimiento, al cerrar la pestaña o, como máximo, a los `TTL_FOTO_MIN` minutos. Cada cierre deja una constancia en `datos_eliminados_en`.

**Reglas que la base hace cumplir** (además del dominio):
- un tinte siempre conserva la silueta y tiene color;
- toda consulta cerrada tiene constancia de borrado;
- la satisfacción va de 1 a 10 y solo existe en consultas finalizadas;
- hay como máximo un look elegido por consulta (índice único parcial);
- las simulaciones de catálogo referencian un estilo y las de texto o voz guardan la instrucción.

Decisiones de diseño:
- Los **estilos no se borran, se desactivan**, porque las simulaciones históricas los referencian.
- Los **roles y estados son ENUM**, no tablas, porque son conjuntos fijos que el código usa en sus reglas.
- **No hay tabla de salones** porque el piloto es un solo salón. Se añadiría (con `salon_id` en usuarios, estilos y consultas) al pasar a varios.
