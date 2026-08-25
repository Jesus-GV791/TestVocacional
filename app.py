from flask import Flask, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from collections import defaultdict
from datetime import datetime
from markupsafe import escape
import random

app = Flask(__name__)

app.secret_key = "clave-secreta-test-vocacional"


# =========================================================
# CONFIGURACIÓN MYSQL
# =========================================================

app.config["SQLALCHEMY_DATABASE_URI"] = (
    "mysql+pymysql://root:@localhost/test_vocacional"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# =========================================================
# MODELOS
# =========================================================

class AreaVocacional(db.Model):

    __tablename__ = "areas_vocacionales"

    id = db.Column(db.Integer, primary_key=True)

    nombre = db.Column(
        db.String(100),
        nullable=False
    )

    descripcion = db.Column(db.Text)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


class Carrera(db.Model):

    __tablename__ = "carreras"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    nombre = db.Column(
        db.String(150),
        nullable=False
    )

    descripcion = db.Column(db.Text)

    area_id = db.Column(
        db.Integer,
        db.ForeignKey("areas_vocacionales.id")
    )


class Pregunta(db.Model):

    __tablename__ = "preguntas"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    texto = db.Column(
        db.Text,
        nullable=False
    )

    area_id = db.Column(
        db.Integer,
        db.ForeignKey("areas_vocacionales.id")
    )


class Usuario(db.Model):

    __tablename__ = "usuarios"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    nombre = db.Column(
        db.String(100)
    )

    email = db.Column(
        db.String(100)
    )

    edad = db.Column(
        db.Integer
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


class Respuesta(db.Model):

    __tablename__ = "respuestas"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id")
    )

    pregunta_id = db.Column(
        db.Integer,
        db.ForeignKey("preguntas.id")
    )

    puntuacion = db.Column(
        db.Integer
    )


class Resultado(db.Model):

    __tablename__ = "resultados"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id")
    )

    area_id = db.Column(
        db.Integer,
        db.ForeignKey("areas_vocacionales.id")
    )

    puntuacion_total = db.Column(
        db.Integer
    )

    porcentaje = db.Column(
        db.Numeric(5, 2)
    )


# =========================================================
# ESTILOS RESPONSIVE
# =========================================================

def estilos():

    return """

    <style>

        :root {
            --primary: #2563eb;
            --primary-dark: #1d4ed8;
            --secondary: #0f172a;
            --success: #16a34a;
            --background: #f4f7fb;
            --card: #ffffff;
            --text: #172033;
            --muted: #64748b;
            --border: #e2e8f0;
        }


        * {
            box-sizing: border-box;
        }


        html {
            scroll-behavior: smooth;
        }


        body {

            margin: 0;

            min-height: 100vh;

            background:
                radial-gradient(
                    circle at top right,
                    rgba(37, 99, 235, .10),
                    transparent 30%
                ),
                linear-gradient(
                    135deg,
                    #f8fafc,
                    #eef4ff
                );

            color: var(--text);

            font-family:
                system-ui,
                -apple-system,
                BlinkMacSystemFont,
                "Segoe UI",
                sans-serif;
        }


        .app-container {

            width: min(
                calc(100% - 32px),
                1050px
            );

            margin: 0 auto;

            padding:
                24px
                0
                40px;
        }


        .logo-wrapper {

            display: flex;

            justify-content: center;

            align-items: center;

            margin-bottom: 18px;
        }


        .logo {

            width:
                clamp(
                    100px,
                    22vw,
                    170px
                );

            height:
                clamp(
                    100px,
                    22vw,
                    170px
                );

            object-fit: contain;

            object-position: center;

            display: block;

            border-radius: 20px;

            background: white;

            padding: 8px;

            box-shadow:
                0 12px 30px
                rgba(15, 23, 42, .12);

            transition:
                transform .25s ease,
                box-shadow .25s ease;
        }


        .logo:hover {

            transform:
                translateY(-3px)
                scale(1.02);

            box-shadow:
                0 16px 36px
                rgba(15, 23, 42, .16);
        }


        .hero {

            text-align: center;

            margin-bottom: 24px;
        }


        .hero h1 {

            font-size:
                clamp(
                    1.65rem,
                    5vw,
                    2.6rem
                );

            font-weight: 800;

            margin:
                0
                0
                8px;

            color:
                var(--secondary);
        }


        .hero p {

            color:
                var(--muted);

            font-size:
                clamp(
                    .95rem,
                    2.5vw,
                    1.1rem
                );

            margin:
                0 auto;

            max-width: 650px;

            line-height: 1.6;
        }


        .card-custom {

            background:
                rgba(
                    255,
                    255,
                    255,
                    .96
                );

            border:
                1px solid
                rgba(
                    226,
                    232,
                    240,
                    .9
                );

            border-radius: 24px;

            padding:
                clamp(
                    20px,
                    5vw,
                    38px
                );

            box-shadow:
                0 18px 50px
                rgba(
                    15,
                    23,
                    42,
                    .10
                );

            animation:
                aparecer .45s ease;
        }


        .form-label {

            display: block;

            font-weight: 700;

            margin-bottom: 8px;
        }


        .form-control {

            width: 100%;

            min-height: 50px;

            border:
                1px solid
                var(--border);

            border-radius: 14px;

            padding:
                12px 15px;

            font-size: 1rem;

            outline: none;

            transition: .2s ease;

            background: #fff;
        }


        .form-control:focus {

            border-color:
                var(--primary);

            box-shadow:
                0 0 0 4px
                rgba(
                    37,
                    99,
                    235,
                    .10
                );
        }


        .field {

            margin-bottom: 18px;
        }


        .btn-main {

            width: 100%;

            min-height: 52px;

            border: 0;

            border-radius: 14px;

            background:
                linear-gradient(
                    135deg,
                    var(--primary),
                    #3b82f6
                );

            color: white;

            font-size: 1rem;

            font-weight: 750;

            cursor: pointer;

            transition:
                transform .2s ease,
                box-shadow .2s ease;
        }


        .btn-main:hover {

            transform:
                translateY(-2px);

            box-shadow:
                0 10px 24px
                rgba(
                    37,
                    99,
                    235,
                    .25
                );
        }


        .progress-area {

            margin:
                18px
                0
                26px;
        }


        .progress-info {

            display: flex;

            justify-content:
                space-between;

            gap: 12px;

            color:
                var(--muted);

            font-size: .9rem;

            margin-bottom: 8px;
        }


        .progress {

            width: 100%;

            height: 12px;

            overflow: hidden;

            background: #e5e7eb;

            border-radius: 50px;
        }


        .progress-bar {

            height: 100%;

            border-radius: 50px;

            background:
                linear-gradient(
                    90deg,
                    var(--primary),
                    #60a5fa
                );

            transition:
                width .45s ease;
        }


        .question {

            font-size:
                clamp(
                    1.15rem,
                    3.8vw,
                    1.55rem
                );

            line-height: 1.45;

            font-weight: 750;

            margin:
                0
                0
                20px;
        }


        .option {

            display: flex;

            align-items: center;

            gap: 12px;

            width: 100%;

            padding:
                14px
                15px;

            margin-bottom: 10px;

            border:
                2px solid
                var(--border);

            border-radius: 14px;

            background: #fff;

            cursor: pointer;

            transition: .2s ease;

            font-size: 1rem;
        }


        .option:hover {

            border-color:
                #93c5fd;

            background:
                #eff6ff;

            transform:
                translateX(2px);
        }


        .option input {

            width: 20px;

            height: 20px;

            flex-shrink: 0;

            accent-color:
                var(--primary);
        }


        .option:has(
            input:checked
        ) {

            border-color:
                var(--primary);

            background:
                #eff6ff;
        }


        .result-header {

            text-align: center;

            margin-bottom: 28px;
        }


        .result-header h1 {

            font-size:
                clamp(
                    1.5rem,
                    5vw,
                    2.3rem
                );

            margin-bottom: 8px;
        }


        .result-card {

            border:
                1px solid
                var(--border);

            border-radius: 18px;

            padding: 25px;

            margin-bottom: 18px;

            background: #fff;
        }


        .percentage {

            font-size: 1.35rem;

            font-weight: 800;

            color:
                var(--primary);
        }


        .career-description {

            padding:
                16px;

            border-radius: 14px;

            background:
                #f8fafc;

            color:
                #475569;

            line-height: 1.6;

            margin-top: 15px;
        }


        .area-result {

            margin-top: 18px;

            padding:
                14px;

            border-radius: 14px;

            background:
                #eff6ff;

            color:
                #1e3a8a;
        }


        .trophy {

            font-size: 3.5rem;

            margin-bottom: 8px;
        }


        .btn-secondary {

            display: inline-flex;

            justify-content: center;

            align-items: center;

            width: 100%;

            min-height: 50px;

            border-radius: 14px;

            background:
                #e2e8f0;

            color:
                #1e293b;

            text-decoration: none;

            font-weight: 700;

            transition: .2s ease;
        }


        .btn-secondary:hover {

            background:
                #cbd5e1;

            transform:
                translateY(-2px);
        }


        .welcome-icon {

            font-size: 3rem;

            text-align: center;

            margin-bottom: 10px;
        }


        @keyframes aparecer {

            from {

                opacity: 0;

                transform:
                    translateY(12px);
            }

            to {

                opacity: 1;

                transform:
                    translateY(0);
            }
        }


        @media (max-width: 576px) {

            .app-container {

                width:
                    calc(100% - 20px);

                padding-top: 14px;
            }


            .card-custom {

                border-radius: 18px;

                padding:
                    18px 15px;
            }


            .logo {

                border-radius: 18px;
            }


            .option {

                padding:
                    13px 12px;
            }


            .question {

                font-size:
                    1.15rem;
            }


            .result-card {

                padding:
                    18px;
            }
        }


        @media (min-width: 768px) {

            .form-grid {

                display: grid;

                grid-template-columns:
                    2fr 1fr;

                gap: 16px;
            }
        }

    </style>

    """


# =========================================================
# PÁGINA BASE
# =========================================================

def pagina_base(titulo, contenido):

    return f"""

    <!DOCTYPE html>

    <html lang="es">

    <head>

        <meta charset="UTF-8">

        <meta
            name="viewport"
            content="width=device-width,
                     initial-scale=1.0,
                     viewport-fit=cover"
        >

        <meta
            name="theme-color"
            content="#2563eb"
        >

        <title>
            {escape(titulo)}
        </title>

        {estilos()}

    </head>

    <body>

        {contenido}

    </body>

    </html>

    """


# =========================================================
# RUTA PRINCIPAL
# =========================================================

@app.route("/")
def index():

    contenido = """

    <main class="app-container">

        <div class="logo-wrapper">

            <img
                src="/static/logo.jpeg"
                alt="Logo del Instituto"
                class="logo"
                onerror="
                    this.style.display='none'
                "
            >

        </div>


        <header class="hero">

            <h1>
                Test Vocacional
            </h1>

            <p>
                Descubre qué carrera se adapta mejor
                a tus intereses, habilidades y preferencias.
            </p>

        </header>


        <section class="card-custom">

            <div class="welcome-icon">
                🎓
            </div>

            <h2
                style="
                    text-align:center;
                    margin-top:0;
                "
            >
                Comencemos
            </h2>

            <p
                style="
                    text-align:center;
                    color:#64748b;
                    line-height:1.6;
                "
            >
                Completa tus datos para iniciar
                el test vocacional.
            </p>


            <form
                method="POST"
                action="/iniciar_test"
            >

                <div class="field">

                    <label
                        class="form-label"
                        for="nombre"
                    >
                        Nombre
                    </label>

                    <input
                        id="nombre"
                        type="text"
                        name="nombre"
                        class="form-control"
                        placeholder="Escribe tu nombre"
                        autocomplete="name"
                        required
                    >

                </div>


                <div class="field">

                    <label
                        class="form-label"
                        for="email"
                    >
                        Correo electrónico
                    </label>

                    <input
                        id="email"
                        type="email"
                        name="email"
                        class="form-control"
                        placeholder="ejemplo@correo.com"
                        autocomplete="email"
                        required
                    >

                </div>


                <div class="field">

                    <label
                        class="form-label"
                        for="edad"
                    >
                        Edad
                    </label>

                    <input
                        id="edad"
                        type="number"
                        name="edad"
                        class="form-control"
                        placeholder="Tu edad"
                        min="15"
                        max="100"
                        inputmode="numeric"
                        required
                    >

                </div>


                <button
                    type="submit"
                    class="btn-main"
                >
                    Comenzar test →
                </button>

            </form>

        </section>

    </main>

    """

    return pagina_base(
        "Test Vocacional",
        contenido
    )


# =========================================================
# INICIAR TEST
# =========================================================

@app.route(
    "/iniciar_test",
    methods=["POST"]
)
def iniciar_test():

    nombre = request.form.get(
        "nombre",
        ""
    ).strip()

    email = request.form.get(
        "email",
        ""
    ).strip()

    edad = request.form.get(
        "edad",
        ""
    ).strip()


    # Validación básica

    if not nombre or not email or not edad:

        return redirect(
            url_for("index")
        )


    session["nombre"] = nombre

    session["email"] = email

    session["edad"] = edad


    # =====================================================
    # OBTENER TODAS LAS PREGUNTAS
    # =====================================================

    preguntas = Pregunta.query.all()


    if not preguntas:

        return """
        <h2>
            No existen preguntas registradas.
        </h2>
        """


    # =====================================================
    # CREAR ORDEN ALEATORIO
    # =====================================================

    preguntas_ids = [
        pregunta.id
        for pregunta in preguntas
    ]


    random.shuffle(
        preguntas_ids
    )


    # Guardamos el orden aleatorio

    session["preguntas_orden"] = (
        preguntas_ids
    )


    # Reiniciar respuestas

    session["pregunta_actual"] = 0

    session["respuestas"] = {}


    return redirect(
        url_for("test")
    )


# =========================================================
# MOSTRAR PREGUNTAS
# =========================================================

@app.route("/test")
def test():

    if "nombre" not in session:

        return redirect(
            url_for("index")
        )


    # Recuperar preguntas aleatorias

    preguntas_orden = session.get(
        "preguntas_orden",
        []
    )


    actual = session.get(
        "pregunta_actual",
        0
    )


    if not preguntas_orden:

        return redirect(
            url_for("index")
        )


    # =====================================================
    # VERIFICAR SI TERMINÓ
    # =====================================================

    if actual >= len(
        preguntas_orden
    ):

        return redirect(
            url_for(
                "procesar_resultados"
            )
        )


    # =====================================================
    # OBTENER PREGUNTA
    # =====================================================

    pregunta_id = preguntas_orden[
        actual
    ]


    pregunta = db.session.get(
        Pregunta,
        pregunta_id
    )


    if pregunta is None:

        return """
        <h2>
            No se encontró la pregunta.
        </h2>
        """


    # =====================================================
    # PROGRESO
    # =====================================================

    total = len(
        preguntas_orden
    )


    progreso = int(
        (
            (actual + 1)
            / total
        ) * 100
    )


    # =====================================================
    # OPCIONES
    # =====================================================

    opciones = [

        (
            1,
            "Muy en desacuerdo"
        ),

        (
            2,
            "En desacuerdo"
        ),

        (
            3,
            "Neutral"
        ),

        (
            4,
            "De acuerdo"
        ),

        (
            5,
            "Muy de acuerdo"
        )

    ]


    opciones_html = ""


    for valor, texto in opciones:

        opciones_html += f"""

        <label class="option">

            <input
                type="radio"
                name="puntuacion"
                value="{valor}"
                required
            >

            <span>
                {escape(texto)}
            </span>

        </label>

        """


    # =====================================================
    # CONTENIDO
    # =====================================================

    contenido = f"""

    <main class="app-container">

        <section class="card-custom">


            <div class="progress-area">


                <div class="progress-info">

                    <span>
                        Pregunta
                        {actual + 1}
                        de
                        {total}
                    </span>

                    <strong>
                        {progreso}%
                    </strong>

                </div>


                <div
                    class="progress"
                    aria-label="Progreso del test"
                >

                    <div
                        class="progress-bar"
                        style="
                            width:{progreso}%
                        "
                    >
                    </div>

                </div>


            </div>


            <p class="question">

                {escape(
                    pregunta.texto
                )}

            </p>


            <form
                method="POST"
                action="/responder"
            >


                <input
                    type="hidden"
                    name="pregunta_id"
                    value="{pregunta.id}"
                >


                {opciones_html}


                <button
                    class="btn-main"
                    type="submit"
                >

                    {
                        "Finalizar test"
                        if actual == total - 1
                        else "Siguiente →"
                    }

                </button>


            </form>


        </section>

    </main>

    """


    return pagina_base(

        f"Pregunta {actual + 1}",

        contenido

    )


# =========================================================
# GUARDAR RESPUESTA
# =========================================================

@app.route(
    "/responder",
    methods=["POST"]
)
def responder():

    pregunta_id = request.form.get(
        "pregunta_id"
    )

    puntuacion = request.form.get(
        "puntuacion"
    )


    if not pregunta_id or not puntuacion:

        return redirect(
            url_for("test")
        )


    respuestas = session.get(
        "respuestas",
        {}
    )


    # Guardar respuesta

    respuestas[str(
        pregunta_id
    )] = int(
        puntuacion
    )


    session["respuestas"] = (
        respuestas
    )


    # Avanzar

    session["pregunta_actual"] = (
        session.get(
            "pregunta_actual",
            0
        ) + 1
    )


    return redirect(
        url_for("test")
    )


# =========================================================
# PROCESAR RESULTADOS
# =========================================================

@app.route("/procesar_resultados")
def procesar_resultados():

    respuestas = session.get(
        "respuestas",
        {}
    )


    if not respuestas:

        return redirect(
            url_for("index")
        )


    # =====================================================
    # CREAR USUARIO
    # =====================================================

    usuario = Usuario(

        nombre=session.get(
            "nombre",
            ""
        ),

        email=session.get(
            "email",
            ""
        ),

        edad=int(
            session.get(
                "edad",
                0
            )
        )

    )


    db.session.add(
        usuario
    )

    db.session.commit()


    # =====================================================
    # CALCULAR PUNTUACIONES
    # =====================================================

    puntuaciones = defaultdict(int)

    total_preguntas = defaultdict(int)


    for pregunta_id, puntuacion in respuestas.items():

        pregunta = db.session.get(
            Pregunta,
            int(pregunta_id)
        )


        if pregunta is None:

            continue


        # Guardar respuesta

        respuesta = Respuesta(

            usuario_id=usuario.id,

            pregunta_id=pregunta.id,

            puntuacion=puntuacion

        )


        db.session.add(
            respuesta
        )


        # Sumar puntos al área

        puntuaciones[
            pregunta.area_id
        ] += puntuacion


        total_preguntas[
            pregunta.area_id
        ] += 1


    db.session.commit()


    # =====================================================
    # GENERAR RESULTADOS
    # =====================================================

    resultados = []


    for area_id, puntos in puntuaciones.items():

        cantidad = total_preguntas[
            area_id
        ]


        if cantidad == 0:

            continue


        # Máximo posible

        maximo = cantidad * 5


        porcentaje = (
            puntos / maximo
        ) * 100


        # Guardar resultado

        resultado = Resultado(

            usuario_id=usuario.id,

            area_id=area_id,

            puntuacion_total=puntos,

            porcentaje=porcentaje

        )


        db.session.add(
            resultado
        )


        # Obtener área

        area = db.session.get(
            AreaVocacional,
            area_id
        )


        # Obtener carrera

        carreras = Carrera.query.filter_by(
            area_id=area_id
        ).all()


        resultados.append(
            (
                area,
                porcentaje,
                carreras
            )
        )


    db.session.commit()


    # =====================================================
    # ORDENAR DE MAYOR A MENOR
    # =====================================================

    resultados.sort(
        key=lambda x: x[1],
        reverse=True
    )


    # =====================================================
    # CARRERA GANADORA
    # =====================================================

    if resultados:

        mejor_area = resultados[0][0]

        mejor_porcentaje = resultados[0][1]

        carreras = resultados[0][2]


        if carreras:

            carrera_recomendada = (
                carreras[0]
            )


            resultado_principal = f"""

            <div
                class="result-card"
                style="text-align:center;"
            >


                <div class="trophy">
                    🏆
                </div>


                <p
                    style="
                        color:#64748b;
                        margin-bottom:8px;
                    "
                >
                    La carrera que más se relaciona
                    con tus respuestas es:
                </p>


                <h2
                    style="
                        color:#1d4ed8;
                        margin:
                            8px
                            0
                            18px;
                        font-size:
                            clamp(
                                1.5rem,
                                5vw,
                                2rem
                            );
                    "
                >

                    {
                        escape(
                            carrera_recomendada.nombre
                        )
                    }

                </h2>


                <div
                    class="progress"
                    style="
                        margin:14px 0;
                    "
                >

                    <div
                        class="progress-bar"
                        style="
                            width:
                            {mejor_porcentaje}%
                        "
                    >
                    </div>

                </div>


                <div
                    class="percentage"
                >

                    {mejor_porcentaje:.1f}%
                    de afinidad

                </div>


                <div
                    class="career-description"
                >

                    <strong>
                        Sobre esta carrera:
                    </strong>

                    <br>

                    {
                        escape(
                            carrera_recomendada.descripcion
                            or
                            "Esta carrera se relaciona con tus intereses y habilidades."
                        )
                    }

                </div>


                <div
                    class="area-result"
                >

                    Área vocacional:

                    <strong>
                        {
                            escape(
                                mejor_area.nombre
                            )
                        }
                    </strong>

                </div>


            </div>

            """


        else:

            resultado_principal = f"""

            <div
                class="result-card"
                style="text-align:center;"
            >

                <div class="trophy">
                    🏆
                </div>

                <h2>
                    {
                        escape(
                            mejor_area.nombre
                        )
                    }
                </h2>

                <div class="percentage">

                    {mejor_porcentaje:.1f}%
                    de afinidad

                </div>

            </div>

            """


    else:

        resultado_principal = """

        <div
            class="result-card"
            style="text-align:center;"
        >

            <h2>
                No se pudo determinar
                una carrera
            </h2>

            <p>
                No se encontraron
                resultados suficientes.
            </p>

        </div>

        """


    # =====================================================
    # PÁGINA DE RESULTADOS
    # =====================================================

    contenido = f"""

    <main class="app-container">


        <div class="logo-wrapper">

            <img
                src="/static/logo.jpeg"
                alt="Logo ITSJC"
                class="logo"
                onerror="
                    this.style.display='none'
                "
            >

        </div>


        <section class="card-custom">


            <header class="result-header">

                <h1>
                    🎉 ¡Test completado!
                </h1>


                <p
                    style="
                        color:#64748b;
                    "
                >

                    Resultado para

                    <strong>
                        {
                            escape(
                                usuario.nombre
                            )
                        }
                    </strong>

                </p>

            </header>


            {resultado_principal}


            <a
                href="/reiniciar"
                class="btn-secondary"
            >

                ↻ Realizar otro test

            </a>


        </section>


    </main>

    """


    return pagina_base(
        "Resultados",
        contenido
    )


# =========================================================
# REINICIAR
# =========================================================

@app.route("/reiniciar")
def reiniciar():

    session.clear()

    return redirect(
        url_for("index")
    )


# =========================================================
# INICIALIZAR BASE DE DATOS
# =========================================================

def init_db():

    with app.app_context():

        db.create_all()


        # =================================================
        # ÁREAS
        # =================================================

        if not AreaVocacional.query.first():

            areas = [

                (
                    "Sistemas Informáticos",
                    "Tecnología, programación y desarrollo de sistemas."
                ),

                (
                    "Industria de Alimentos",
                    "Procesamiento, elaboración y control de alimentos."
                ),

                (
                    "Mecánica Automotriz",
                    "Mantenimiento y reparación de vehículos."
                ),

                (
                    "Electromecánica",
                    "Electricidad, electrónica y sistemas mecánicos."
                )

            ]


            for nombre, descripcion in areas:

                db.session.add(

                    AreaVocacional(

                        nombre=nombre,

                        descripcion=descripcion

                    )

                )


            db.session.commit()


            # =============================================
            # CARRERAS
            # =============================================

            carreras = [

                (
                    "Sistemas Informáticos",

                    "Aprenderás programación, desarrollo de software, bases de datos y tecnología.",

                    1
                ),

                (
                    "Industria de Alimentos",

                    "Aprenderás a procesar, elaborar y controlar la calidad de productos alimenticios.",

                    2
                ),

                (
                    "Mecánica Automotriz",

                    "Aprenderás mantenimiento, diagnóstico y reparación de vehículos.",

                    3
                ),

                (
                    "Electromecánica",

                    "Aprenderás electricidad, electrónica, motores y sistemas mecánicos.",

                    4
                )

            ]


            for nombre, descripcion, area_id in carreras:

                db.session.add(

                    Carrera(

                        nombre=nombre,

                        descripcion=descripcion,

                        area_id=area_id

                    )

                )


            db.session.commit()


            # =============================================
            # PREGUNTAS
            # =============================================

            preguntas = [

                # =========================================
                # SISTEMAS INFORMÁTICOS
                # =========================================

                (
                    "Me interesa aprender a programar y crear aplicaciones",
                    1
                ),

                (
                    "Disfruto trabajando con computadoras y tecnología",
                    1
                ),

                (
                    "Me gustaría aprender sobre bases de datos",
                    1
                ),

                (
                    "Me interesa crear páginas web y sistemas informáticos",
                    1
                ),

                (
                    "Me gusta resolver problemas utilizando la tecnología",
                    1
                ),


                # =========================================
                # INDUSTRIA DE ALIMENTOS
                # =========================================

                (
                    "Me interesa aprender cómo se elaboran y procesan los alimentos",
                    2
                ),

                (
                    "Me gustaría trabajar en la producción de productos alimenticios",
                    2
                ),

                (
                    "Me interesa conocer los procesos de conservación de alimentos",
                    2
                ),

                (
                    "Me preocupa que los alimentos cumplan normas de higiene y calidad",
                    2
                ),

                (
                    "Me gustaría experimentar con nuevos productos alimenticios",
                    2
                ),


                # =========================================
                # MECÁNICA AUTOMOTRIZ
                # =========================================

                (
                    "Me interesa conocer cómo funcionan los motores de los vehículos",
                    3
                ),

                (
                    "Disfruto reparar y realizar mantenimiento a vehículos",
                    3
                ),

                (
                    "Me gustaría aprender a identificar fallas mecánicas en automóviles",
                    3
                ),

                (
                    "Me interesa conocer las diferentes partes de un automóvil",
                    3
                ),

                (
                    "Me gustaría trabajar en el mantenimiento y reparación de vehículos",
                    3
                ),


                # =========================================
                # ELECTROMECÁNICA
                # =========================================

                (
                    "Me interesa aprender sobre electricidad y circuitos eléctricos",
                    4
                ),

                (
                    "Me gustaría trabajar con motores eléctricos y máquinas",
                    4
                ),

                (
                    "Me interesa conocer cómo funcionan los sistemas electrónicos",
                    4
                ),

                (
                    "Disfruto solucionar problemas eléctricos y mecánicos",
                    4
                ),

                (
                    "Me gustaría aprender a instalar y mantener equipos electromecánicos",
                    4
                )

            ]


            for texto, area_id in preguntas:

                db.session.add(

                    Pregunta(

                        texto=texto,

                        area_id=area_id

                    )

                )


            db.session.commit()


            print(
                "Base de datos inicializada correctamente."
            )


# =========================================================
# EJECUTAR APLICACIÓN
# =========================================================

if __name__ == "__main__":

    init_db()

    app.run(

        debug=True,

        host="0.0.0.0",

        port=5000

    )