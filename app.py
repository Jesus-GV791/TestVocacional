from flask import Flask, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from collections import defaultdict
from datetime import datetime
from markupsafe import escape
import random
import json

app = Flask(__name__)

app.secret_key = "clave-secreta-test-vocacional"


# =========================================================
# CONFIGURACIÓN MYSQL - AIVEN
# =========================================================

import os
from pathlib import Path
from sqlalchemy import URL

ca_path = str(Path(__file__).resolve().parent / "ca.pem")

app.config["SQLALCHEMY_DATABASE_URI"] = URL.create(
    drivername="mysql+pymysql",
    username=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
    host=os.environ["DB_HOST"],
    port=int(os.environ["DB_PORT"]),
    database=os.environ["DB_NAME"],
)

app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "connect_args": {
        "ssl": {"ca": ca_path}
    }
}

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# =========================================================
# TEMAS POR ÁREA  (solo colores para resultados)
# =========================================================

AREA_TEMAS = {
    1: {"c1": "#6366f1", "c2": "#8b5cf6"},
    2: {"c1": "#10b981", "c2": "#34d399"},
    3: {"c1": "#f59e0b", "c2": "#f97316"},
    4: {"c1": "#ec4899", "c2": "#a855f7"},
}

# Emojis NEUTROS: no revelan la carrera
ICONOS_NEUTROS = ["✨", "🌟", "💫", "⭐", "🔮", "🎈", "🎯", "🌈", "💠", "🪄"]


def tema_area(area_id):
    return AREA_TEMAS.get(area_id, {"c1": "#2563eb", "c2": "#3b82f6"})


# =========================================================
# MODELOS
# =========================================================

class AreaVocacional(db.Model):
    __tablename__ = "areas_vocacionales"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Carrera(db.Model):
    __tablename__ = "carreras"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    descripcion = db.Column(db.Text)
    area_id = db.Column(db.Integer, db.ForeignKey("areas_vocacionales.id"))


class Pregunta(db.Model):
    __tablename__ = "preguntas"
    id = db.Column(db.Integer, primary_key=True)
    texto = db.Column(db.Text, nullable=False)
    area_id = db.Column(db.Integer, db.ForeignKey("areas_vocacionales.id"))


class Usuario(db.Model):
    __tablename__ = "usuarios"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    email = db.Column(db.String(100))
    edad = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Respuesta(db.Model):
    __tablename__ = "respuestas"
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"))
    pregunta_id = db.Column(db.Integer, db.ForeignKey("preguntas.id"))
    puntuacion = db.Column(db.Integer)


class Resultado(db.Model):
    __tablename__ = "resultados"
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"))
    area_id = db.Column(db.Integer, db.ForeignKey("areas_vocacionales.id"))
    puntuacion_total = db.Column(db.Integer)
    porcentaje = db.Column(db.Numeric(5, 2))


# =========================================================
# ESTILOS
# =========================================================

def estilos():

    return """

    <style>

        @import url(
            'https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800;900&display=swap'
        );


        :root {
            --primary: #6366f1;
            --primary-2: #8b5cf6;
            --accent: #ec4899;
            --secondary: #0f172a;
            --success: #16a34a;
            --background: #f4f7fb;
            --card: rgba(255, 255, 255, .82);
            --text: #172033;
            --muted: #64748b;
            --border: rgba(226, 232, 240, .9);
            --shadow: rgba(79, 70, 229, .18);
        }


        body.dark {
            --secondary: #f1f5f9;
            --background: #070b1a;
            --card: rgba(23, 30, 55, .78);
            --text: #e2e8f0;
            --muted: #94a3b8;
            --border: rgba(71, 85, 130, .5);
            --shadow: rgba(0, 0, 0, .5);
        }


        * { box-sizing: border-box; }

        html { scroll-behavior: smooth; }


        body {
            margin: 0;
            min-height: 100vh;
            color: var(--text);
            font-family: 'Poppins', system-ui, sans-serif;
            background: var(--background);
            overflow-x: hidden;
            transition: background .5s ease, color .4s ease;
        }


        /* ===== FONDO ANIMADO ===== */

        .fondo {
            position: fixed;
            inset: 0;
            z-index: -2;
            overflow: hidden;
            background:
                linear-gradient(135deg, #eef2ff 0%, #f8fafc 40%, #fdf2f8 100%);
            transition: background .5s ease;
        }


        body.dark .fondo {
            background:
                linear-gradient(135deg, #050816 0%, #0b1024 50%, #140b22 100%);
        }


        .orbe {
            position: absolute;
            border-radius: 50%;
            filter: blur(70px);
            opacity: .55;
            animation: flotar 18s ease-in-out infinite;
        }

        .orbe.o1 { width: 420px; height: 420px; background: #6366f1; top: -120px; left: -100px; }
        .orbe.o2 { width: 380px; height: 380px; background: #ec4899; bottom: -120px; right: -80px; animation-delay: -6s; }
        .orbe.o3 { width: 320px; height: 320px; background: #10b981; top: 40%; left: 55%; animation-delay: -11s; }


        @keyframes flotar {
            0%, 100% { transform: translate(0, 0) scale(1); }
            33% { transform: translate(60px, -40px) scale(1.15); }
            66% { transform: translate(-40px, 50px) scale(.9); }
        }


        /* ===== EMOJIS FLOTANTES DE FONDO (NEUTROS) ===== */

        .flotante {
            position: fixed;
            z-index: -1;
            opacity: .16;
            pointer-events: none;
            user-select: none;
            animation: flotarEmoji 12s ease-in-out infinite;
        }


        @keyframes flotarEmoji {
            0%, 100% { transform: translateY(0) rotate(-10deg); }
            50% { transform: translateY(-46px) rotate(10deg); }
        }


        /* ===== BARRA DE CARGA ===== */

        .barra-carga {
            position: fixed;
            top: 0;
            left: 0;
            height: 4px;
            width: 0;
            z-index: 1000;
            border-radius: 0 4px 4px 0;
            background: linear-gradient(90deg, #6366f1, #ec4899, #10b981);
            box-shadow: 0 0 14px rgba(99, 102, 241, .8);
            transition: width .7s ease, opacity .5s ease;
        }


        /* ===== OVERLAY CARGANDO ===== */

        .cargando {
            position: fixed;
            inset: 0;
            z-index: 2000;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 18px;
            background: rgba(15, 23, 42, .45);
            backdrop-filter: blur(6px);
            opacity: 0;
            pointer-events: none;
            transition: opacity .3s ease;
        }

        .cargando.visible { opacity: 1; pointer-events: all; }


        .spinner {
            width: 62px;
            height: 62px;
            border-radius: 50%;
            border: 5px solid rgba(255, 255, 255, .25);
            border-top-color: #fff;
            animation: girar .8s linear infinite;
        }

        .cargando span { color: #fff; font-weight: 800; font-size: 1.1rem; }

        @keyframes girar { to { transform: rotate(360deg); } }


        .app-container {
            width: min(calc(100% - 32px), 1050px);
            margin: 0 auto;
            padding: 24px 0 180px;
            position: relative;
        }


        /* ===== BOTÓN TEMA ===== */

        .tema-btn {
            position: fixed;
            top: 18px;
            right: 18px;
            z-index: 500;
            width: 50px;
            height: 50px;
            border: 1px solid var(--border);
            border-radius: 50%;
            background: var(--card);
            backdrop-filter: blur(12px);
            font-size: 1.35rem;
            cursor: pointer;
            box-shadow: 0 8px 24px var(--shadow);
            transition: transform .3s ease, box-shadow .3s ease;
        }

        .tema-btn:hover {
            transform: rotate(25deg) scale(1.12);
            box-shadow: 0 12px 30px var(--shadow);
        }


        /* ===== LOGO ===== */

        .logo-wrapper {
            display: flex;
            justify-content: center;
            margin-bottom: 18px;
            animation: aparecerArriba .7s ease both;
        }

        .logo {
            width: clamp(100px, 22vw, 170px);
            height: clamp(100px, 22vw, 170px);
            object-fit: contain;
            border-radius: 24px;
            background: #fff;
            padding: 8px;
            box-shadow: 0 12px 40px var(--shadow);
            transition: transform .4s ease, box-shadow .4s ease;
            animation: flotarLogo 4s ease-in-out infinite;
        }

        .logo:hover {
            transform: translateY(-6px) scale(1.06) rotate(2deg);
            box-shadow: 0 20px 50px var(--shadow);
        }

        @keyframes flotarLogo {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-8px); }
        }


        /* ===== HERO ===== */

        .hero {
            text-align: center;
            margin-bottom: 26px;
            animation: aparecerArriba .7s .1s ease both;
        }

        .hero h1 {
            font-size: clamp(1.8rem, 6vw, 3rem);
            font-weight: 900;
            margin: 0 0 10px;
            letter-spacing: -.5px;
            background: linear-gradient(120deg, #6366f1, #ec4899, #8b5cf6, #6366f1);
            background-size: 300% 300%;
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
            animation: degradado 6s ease infinite;
        }

        @keyframes degradado {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        .hero p {
            color: var(--muted);
            font-size: clamp(.95rem, 2.5vw, 1.1rem);
            margin: 0 auto;
            max-width: 650px;
            line-height: 1.6;
        }


        /* ===== TARJETAS ===== */

        .card-custom {
            background: var(--card);
            backdrop-filter: blur(18px);
            -webkit-backdrop-filter: blur(18px);
            border: 1px solid var(--border);
            border-radius: 28px;
            padding: clamp(20px, 5vw, 40px);
            box-shadow: 0 24px 60px var(--shadow);
            animation: aparecerArriba .6s ease both;
            position: relative;
            overflow: hidden;
            transition: box-shadow .4s ease;
        }

        .card-custom:hover { box-shadow: 0 30px 70px rgba(99, 102, 241, .25); }


        /* ===== FORMULARIO ===== */

        .form-label { display: block; font-weight: 700; margin-bottom: 8px; font-size: .95rem; }

        .form-control {
            width: 100%;
            min-height: 52px;
            border: 2px solid var(--border);
            border-radius: 16px;
            padding: 12px 16px;
            font-size: 1rem;
            font-family: inherit;
            outline: none;
            background: var(--card);
            color: var(--text);
            transition: border-color .25s ease, box-shadow .25s ease, transform .25s ease;
        }

        .form-control:focus {
            border-color: var(--primary);
            box-shadow: 0 0 0 5px rgba(99, 102, 241, .15);
            transform: translateY(-2px);
        }

        .field { margin-bottom: 18px; animation: aparecerArriba .5s ease both; }
        .field:nth-child(1) { animation-delay: .15s; }
        .field:nth-child(2) { animation-delay: .25s; }
        .field:nth-child(3) { animation-delay: .35s; }


        /* ===== BOTÓN PRINCIPAL ===== */

        .btn-main {
            position: relative;
            overflow: hidden;
            width: 100%;
            min-height: 56px;
            border: 0;
            border-radius: 16px;
            background: linear-gradient(135deg, var(--primary), var(--primary-2));
            background-size: 200% 200%;
            color: #fff;
            font-size: 1.05rem;
            font-weight: 800;
            font-family: inherit;
            cursor: pointer;
            transition: transform .25s ease, box-shadow .25s ease;
            animation: degradado 5s ease infinite;
            box-shadow: 0 10px 30px rgba(99, 102, 241, .35);
        }

        .btn-main:hover { transform: translateY(-3px) scale(1.02); box-shadow: 0 16px 40px rgba(99, 102, 241, .55); }
        .btn-main:active { transform: translateY(-1px) scale(.99); }


        /* ===== PROGRESO ===== */

        .progress-area { margin: 4px 0 26px; }

        .progress-info {
            display: flex;
            justify-content: space-between;
            gap: 12px;
            color: var(--muted);
            font-size: .9rem;
            font-weight: 600;
            margin-bottom: 10px;
        }

        .progress {
            width: 100%;
            height: 14px;
            overflow: hidden;
            background: rgba(148, 163, 184, .25);
            border-radius: 50px;
        }

        .progress-bar {
            height: 100%;
            width: 0;
            border-radius: 50px;
            background: linear-gradient(90deg, var(--primary), var(--accent), var(--primary-2));
            background-size: 200% 100%;
            transition: width .55s cubic-bezier(.22, 1, .36, 1);
            animation: brillo 2.5s linear infinite;
        }

        @keyframes brillo {
            0% { background-position: 0% 50%; }
            100% { background-position: 200% 50%; }
        }


        /* ===== PREGUNTA ===== */

        .question {
            font-size: clamp(1.2rem, 4vw, 1.6rem);
            line-height: 1.45;
            font-weight: 800;
            margin: 0 0 22px;
            animation: aparecerArriba .4s ease both;
        }

        .question .icono-area {
            display: inline-block;
            font-size: 1.9rem;
            animation: saltar 2.2s ease-in-out infinite;
        }


        /* ===== CAMBIO RÁPIDO DE PREGUNTA ===== */

        #zonaPregunta { min-height: 320px; }

        #zonaPregunta.entrando {
            animation: swapIn .30s cubic-bezier(.22, 1, .36, 1) both;
        }

        @keyframes swapIn {
            from { opacity: 0; transform: translateX(30px); }
            to { opacity: 1; transform: translateX(0); }
        }

        form.sacudir { animation: sacudir .4s ease; }

        @keyframes sacudir {
            0%, 100% { transform: translateX(0); }
            25% { transform: translateX(-8px); }
            75% { transform: translateX(8px); }
        }


        /* ===== OPCIONES ===== */

        .option {
            position: relative;
            display: flex;
            align-items: center;
            gap: 14px;
            width: 100%;
            padding: 15px 18px;
            margin-bottom: 12px;
            border: 2px solid var(--border);
            border-radius: 16px;
            background: var(--card);
            cursor: pointer;
            font-size: 1rem;
            font-weight: 500;
            transition: transform .22s ease, background .25s ease;
            animation: aparecerLado .38s ease both;
        }

        .option:nth-of-type(1) { animation-delay: .03s; }
        .option:nth-of-type(2) { animation-delay: .08s; }
        .option:nth-of-type(3) { animation-delay: .13s; }
        .option:nth-of-type(4) { animation-delay: .18s; }
        .option:nth-of-type(5) { animation-delay: .23s; }

        .option:hover {
            transform: translateX(8px) rotate(-.6deg) scale(1.015);
            background: rgba(99, 102, 241, .07);
            animation: bordeArcoiris 2s linear infinite;
        }

        @keyframes bordeArcoiris {
            0% { border-color: #6366f1; box-shadow: 0 0 0 5px rgba(99, 102, 241, .16), 0 8px 22px rgba(99, 102, 241, .22); }
            25% { border-color: #ec4899; box-shadow: 0 0 0 5px rgba(236, 72, 153, .16), 0 8px 22px rgba(236, 72, 153, .22); }
            50% { border-color: #10b981; box-shadow: 0 0 0 5px rgba(16, 185, 129, .16), 0 8px 22px rgba(16, 185, 129, .22); }
            75% { border-color: #f59e0b; box-shadow: 0 0 0 5px rgba(245, 158, 11, .16), 0 8px 22px rgba(245, 158, 11, .22); }
            100% { border-color: #6366f1; box-shadow: 0 0 0 5px rgba(99, 102, 241, .16), 0 8px 22px rgba(99, 102, 241, .22); }
        }

        .option .emoji-op { font-size: 1.4rem; transition: transform .3s cubic-bezier(.34, 1.56, .64, 1); }
        .option:hover .emoji-op { transform: scale(1.4) rotate(12deg); }

        .option input {
            appearance: none;
            -webkit-appearance: none;
            width: 24px;
            height: 24px;
            flex-shrink: 0;
            border: 2px solid var(--border);
            border-radius: 50%;
            cursor: pointer;
            transition: all .25s ease;
            position: relative;
        }

        .option input:checked {
            border-color: var(--primary);
            background: var(--primary);
            box-shadow: 0 0 0 5px rgba(99, 102, 241, .18);
        }

        .option input:checked::after {
            content: '';
            position: absolute;
            left: 7px;
            top: 3px;
            width: 6px;
            height: 11px;
            border: solid #fff;
            border-width: 0 3px 3px 0;
            transform: rotate(45deg) scale(0);
            animation: check .3s ease forwards;
        }

        @keyframes check { to { transform: rotate(45deg) scale(1); } }

        .option:has(input:checked),
        .option.elegida {
            border-color: var(--primary) !important;
            background: rgba(99, 102, 241, .14) !important;
            transform: translateX(8px) scale(1.02);
            box-shadow: 0 8px 24px rgba(99, 102, 241, .22);
            animation: none !important;
        }


        /* ===== RESULTADOS ===== */

        .result-header { text-align: center; margin-bottom: 28px; animation: aparecerArriba .6s ease both; }

        .result-header h1 { font-size: clamp(1.6rem, 5.5vw, 2.5rem); font-weight: 900; margin-bottom: 8px; }

        .result-card {
            border: 1px solid var(--border);
            border-radius: 22px;
            padding: 28px;
            margin-bottom: 18px;
            background: var(--card);
            backdrop-filter: blur(14px);
            animation: popIn .7s cubic-bezier(.22, 1.2, .36, 1) both;
            position: relative;
            overflow: hidden;
            transition: transform .3s ease, box-shadow .3s ease;
        }

        .result-card:hover { transform: translateY(-4px); box-shadow: 0 20px 50px rgba(99, 102, 241, .2); }

        .result-card.destacado::after {
            content: '';
            position: absolute;
            inset: 0;
            border-radius: 22px;
            padding: 2px;
            background: linear-gradient(120deg, #6366f1, #ec4899, #8b5cf6);
            -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
            -webkit-mask-composite: xor;
            mask-composite: exclude;
            pointer-events: none;
        }

        .career-description {
            padding: 18px;
            border-radius: 16px;
            background: rgba(99, 102, 241, .08);
            color: var(--text);
            line-height: 1.65;
            margin-top: 16px;
            border: 1px solid var(--border);
        }

        .area-result {
            margin-top: 18px;
            padding: 15px;
            border-radius: 16px;
            background: rgba(99, 102, 241, .12);
            font-weight: 600;
        }

        .trophy { font-size: 4rem; margin-bottom: 8px; display: inline-block; animation: saltar 2s ease-in-out infinite; }

        @keyframes saltar {
            0%, 100% { transform: translateY(0) rotate(-6deg); }
            50% { transform: translateY(-14px) rotate(6deg); }
        }

        .anillo { width: 150px; height: 150px; margin: 0 auto 12px; position: relative; display: grid; place-items: center; }
        .anillo svg { transform: rotate(-90deg); }
        .anillo .valor { position: absolute; font-size: 1.7rem; font-weight: 900; }


        /* ===== BOTÓN SECUNDARIO ===== */

        .btn-secondary {
            display: inline-flex;
            justify-content: center;
            align-items: center;
            gap: 8px;
            width: 100%;
            min-height: 54px;
            border-radius: 16px;
            border: 2px solid var(--border);
            background: var(--card);
            color: var(--text);
            text-decoration: none;
            font-weight: 800;
            transition: all .25s ease;
        }

        .btn-secondary:hover {
            background: var(--primary);
            color: #fff;
            border-color: var(--primary);
            transform: translateY(-3px);
            box-shadow: 0 12px 30px rgba(99, 102, 241, .35);
        }

        .welcome-icon {
            font-size: 3.5rem;
            text-align: center;
            margin-bottom: 6px;
            display: inline-block;
            width: 100%;
            animation: saltar 2.5s ease-in-out infinite;
        }


        /* ===== PARTÍCULAS ===== */

        .particula {
            position: fixed;
            pointer-events: none;
            z-index: 900;
            animation: particulaVolar 1.2s ease-out forwards;
        }

        @keyframes particulaVolar {
            0% { transform: translate(0, 0) scale(0) rotate(0deg); opacity: 1; }
            100% { transform: translate(var(--dx), var(--dy)) scale(1.3) rotate(360deg); opacity: 0; }
        }


        /* ===== CONFETI ===== */

        .confeti {
            position: fixed;
            top: -20px;
            z-index: 999;
            pointer-events: none;
            animation: caer linear forwards;
        }

        @keyframes caer {
            to { transform: translateY(105vh) rotate(720deg); opacity: 0; }
        }


        /* =====================================================
           MASCOTA  ->  LADO DERECHO
           ===================================================== */

        .mascota-caja {
            position: fixed;
            right: 24px;
            bottom: 14px;
            z-index: 400;
            pointer-events: none;
            user-select: none;
            transform-origin: bottom right;
            transform: rotate(var(--tilt, 0deg));
            transition: transform .45s cubic-bezier(.34, 1.3, .64, 1);
            filter: drop-shadow(0 14px 26px rgba(0, 0, 0, .22));
            will-change: transform;
            --tilt: 0deg;
        }


        .mascota-glow {
            position: absolute;
            inset: 6% 4% 2% 4%;
            border-radius: 50%;
            background: radial-gradient(
                circle,
                rgba(99, 102, 241, .32),
                rgba(236, 72, 153, .16) 55%,
                transparent 72%
            );
            filter: blur(16px);
            z-index: -1;
            animation: respirarLuz 4.5s ease-in-out infinite;
        }

        @keyframes respirarLuz {
            0%, 100% { transform: scale(.9); opacity: .55; }
            50% { transform: scale(1.08); opacity: 1; }
        }


        .mascota-img {
            width: 190px;
            height: auto;
            display: block;
            transform-origin: bottom center;
            animation: mascotaIdle 4s ease-in-out infinite;
        }


        @keyframes mascotaIdle {
            0%, 100% { transform: translateY(0) rotate(-1.6deg) scale(1); }
            25% { transform: translateY(-7px) rotate(0deg) scale(1.01); }
            50% { transform: translateY(-12px) rotate(1.6deg) scale(1.02); }
            75% { transform: translateY(-6px) rotate(0deg) scale(1.01); }
        }


        .mascota-img.salta {
            animation: mascotaSalto .8s cubic-bezier(.34, 1.56, .64, 1);
        }


        @keyframes mascotaSalto {
            0% { transform: translateY(0) rotate(0deg) scale(1); }
            30% { transform: translateY(-52px) rotate(-8deg) scale(1.06); }
            55% { transform: translateY(-18px) rotate(7deg) scale(1.02); }
            75% { transform: translateY(-4px) rotate(-2deg) scale(1); }
            100% { transform: translateY(0) rotate(0deg) scale(1); }
        }


        .mascota-img.celebra {
            animation: mascotaCelebra .65s ease-in-out infinite;
        }


        @keyframes mascotaCelebra {
            0%, 100% { transform: translateY(0) rotate(-6deg) scale(1); }
            50% { transform: translateY(-24px) rotate(6deg) scale(1.07); }
        }


        .chispa {
            position: fixed;
            z-index: 399;
            pointer-events: none;
            font-size: 17px;
            animation: chispaSubir 1.9s ease-out forwards;
        }

        @keyframes chispaSubir {
            0% { opacity: 0; transform: translateY(0) scale(.3) rotate(0deg); }
            18% { opacity: 1; }
            100% { opacity: 0; transform: translateY(-80px) scale(1.15) rotate(35deg); }
        }


        /* ===== GLOBO DE TEXTO ===== */

        .capi-globo {
            position: fixed;
            right: 216px;
            bottom: 158px;
            max-width: min(46vw, 230px);
            background: #fff;
            color: #1e293b;
            padding: 11px 18px;
            border-radius: 20px;
            font-weight: 800;
            font-size: .92rem;
            text-align: center;
            line-height: 1.35;
            box-shadow: 0 12px 32px rgba(0, 0, 0, .18);
            opacity: 0;
            z-index: 401;
            pointer-events: none;
            transform: translateX(-12px) scale(.85);
            transform-origin: right center;
            transition: all .35s cubic-bezier(.34, 1.56, .64, 1);
        }

        .capi-globo.visible {
            opacity: 1;
            transform: translateX(0) scale(1);
        }

        .capi-globo::after {
            content: '';
            position: absolute;
            right: -9px;
            top: 50%;
            transform: translateY(-50%);
            border: 10px solid transparent;
            border-left-color: #fff;
            border-right: 0;
        }

        body.dark .capi-globo { background: #1e293b; color: #e2e8f0; }
        body.dark .capi-globo::after { border-left-color: #1e293b; }


        /* ===== ANIMACIONES GENERALES ===== */

        @keyframes aparecerArriba {
            from { opacity: 0; transform: translateY(22px); }
            to { opacity: 1; transform: translateY(0); }
        }

        @keyframes aparecerLado {
            from { opacity: 0; transform: translateX(-18px); }
            to { opacity: 1; transform: translateX(0); }
        }

        @keyframes popIn {
            0% { opacity: 0; transform: scale(.9); }
            100% { opacity: 1; transform: scale(1); }
        }


        /* ===== RESPONSIVE ===== */

        @media (min-width: 1024px) {
            .app-container { padding-right: 205px; }
        }


        @media (min-width: 577px) and (max-width: 1023px) {

            .mascota-img { width: 150px; }
            .app-container { padding-bottom: 165px; }

            .capi-globo {
                right: 176px;
                bottom: 128px;
                font-size: .85rem;
                max-width: 40vw;
            }
        }


        @media (max-width: 576px) {

            .app-container {
                width: calc(100% - 20px);
                padding-top: 14px;
                padding-bottom: 150px;
            }

            .card-custom { border-radius: 20px; padding: 18px 15px; }
            .tema-btn { width: 44px; height: 44px; font-size: 1.15rem; }
            .option { padding: 13px 14px; }
            .question { font-size: 1.2rem; }
            .result-card { padding: 20px; }
            #zonaPregunta { min-height: 280px; }

            .mascota-caja { right: 10px; bottom: 8px; }
            .mascota-img { width: 118px; }

            .capi-globo {
                right: 130px;
                bottom: 92px;
                font-size: .78rem;
                padding: 8px 12px;
                max-width: 50vw;
            }
        }


        @media (min-width: 768px) {
            .form-grid { display: grid; grid-template-columns: 2fr 1fr; gap: 16px; }
        }

    </style>

    """


# =========================================================
# MASCOTA
# =========================================================

def mascota_html():

    return """

    <div class="mascota-caja" id="capi">

        <div class="mascota-glow"></div>

        <img
            src="/static/capibara.png"
            class="mascota-img"
            id="mascotaImg"
            alt="Mascota capibara"
            onerror="this.style.display='none'"
        >

    </div>

    <div class="capi-globo" id="capiGlobo">¡Hola! 🦫</div>

    """


# =========================================================
# RENDER DE UNA PREGUNTA  (ahora acepta DICT)
# =========================================================

def render_pregunta(pregunta, indice, total):

    icono = ICONOS_NEUTROS[indice % len(ICONOS_NEUTROS)]

    progreso = int(((indice + 1) / total) * 100)

    opciones = [
        (1, "Muy en desacuerdo", "😕"),
        (2, "En desacuerdo", "🙁"),
        (3, "Neutral", "😐"),
        (4, "De acuerdo", "🙂"),
        (5, "Muy de acuerdo", "😄"),
    ]

    opciones_html = ""

    for valor, texto, emoji in opciones:

        opciones_html += (
            '<label class="option">'
            '<input type="radio" name="puntuacion" value="' + str(valor) + '" required>'
            '<span class="emoji-op">' + emoji + '</span>'
            '<span>' + str(escape(texto)) + '</span>'
            '</label>'
        )

    boton = "🎉 Finalizar test" if indice == total - 1 else "Siguiente →"

    return (
        '<div class="progress-area">'
            '<div class="progress-info">'
                '<span>Pregunta ' + str(indice + 1) + ' de ' + str(total) + '</span>'
                '<strong>' + str(progreso) + '%</strong>'
            '</div>'
            '<div class="progress" aria-label="Progreso del test">'
                '<div class="progress-bar" data-pct="' + str(progreso) + '" style="width:' + str(progreso) + '%"></div>'
            '</div>'
        '</div>'
        '<p class="question" style="display:flex;align-items:center;gap:12px;">'
            '<span class="icono-area">' + icono + '</span>'
            + str(escape(pregunta["texto"])) +
        '</p>'
        '<form id="formPregunta" method="POST" action="/responder">'
            '<input type="hidden" name="pregunta_id" value="' + str(pregunta["id"]) + '">'
            + opciones_html +
            '<button class="btn-main" type="submit">' + boton + '</button>'
        '</form>'
    )


# =========================================================
# SCRIPTS
# =========================================================

def scripts():

    return """

    <script>

        const EMOJIS_NEUTROS = [
            "✨", "🌟", "⭐", "💫", "🔮",
            "🎈", "🎯", "🌈", "💠", "🪄", "🧿", "🫧"
        ];

        const FRASES = [
            "¡Tú puedes! 💪",
            "¡Vas genial! ✨",
            "¡Sigue así! 🌟",
            "¡Buena elección! 👀",
            "¡Casi terminamos! 🎯",
            "¡Eso es! 🔥",
            "¡Interesante! 🤔"
        ];


        function alAzar(lista) {
            return lista[Math.floor(Math.random() * lista.length)];
        }


        (function () {
            try {
                if (localStorage.getItem("tema") === "oscuro") {
                    document.body.classList.add("dark");
                }
            } catch (e) {}
        })();


        function alternarTema() {

            document.body.classList.toggle("dark");

            const oscuro = document.body.classList.contains("dark");

            try {
                localStorage.setItem("tema", oscuro ? "oscuro" : "claro");
            } catch (e) {}

            const btn = document.getElementById("temaBtn");

            if (btn) btn.textContent = oscuro ? "☀️" : "🌙";
        }


        function estallidoEmojis(x, y) {

            for (let i = 0; i < 14; i++) {

                const e = document.createElement("div");

                e.className = "particula";
                e.textContent = alAzar(EMOJIS_NEUTROS);
                e.style.left = x + "px";
                e.style.top = y + "px";
                e.style.fontSize = (18 + Math.random() * 24) + "px";

                const ang = Math.random() * Math.PI * 2;
                const dist = 70 + Math.random() * 140;

                e.style.setProperty("--dx", (Math.cos(ang) * dist) + "px");
                e.style.setProperty("--dy", (Math.sin(ang) * dist - 90) + "px");

                document.body.appendChild(e);

                setTimeout(function () { e.remove(); }, 1300);
            }
        }


        function capiReacciona() {

            const img = document.getElementById("mascotaImg");
            const globo = document.getElementById("capiGlobo");

            if (img) {
                img.classList.remove("salta");
                void img.offsetWidth;
                img.classList.add("salta");
                setTimeout(function () { img.classList.remove("salta"); }, 820);
            }

            if (globo) {
                globo.textContent = alAzar(FRASES);
                globo.classList.add("visible");
                clearTimeout(window.__globo);
                window.__globo = setTimeout(function () {
                    globo.classList.remove("visible");
                }, 2200);
            }
        }


        function lanzarConfeti() {

            const colores = [
                "#6366f1", "#8b5cf6", "#ec4899",
                "#10b981", "#f59e0b", "#3b82f6"
            ];

            for (let i = 0; i < 150; i++) {

                const c = document.createElement("div");

                c.className = "confeti";
                c.style.left = Math.random() * 100 + "vw";
                c.style.background = colores[Math.floor(Math.random() * colores.length)];
                c.style.width = (6 + Math.random() * 9) + "px";
                c.style.height = (6 + Math.random() * 9) + "px";
                c.style.borderRadius = Math.random() > 0.5 ? "50%" : "3px";
                c.style.animationDelay = (Math.random() * 0.9) + "s";
                c.style.animationDuration = (2.6 + Math.random() * 2.4) + "s";

                document.body.appendChild(c);

                setTimeout(function () { c.remove(); }, 6000);
            }
        }


        function flotantesNeutros() {

            for (let i = 0; i < 9; i++) {

                const e = document.createElement("div");

                e.className = "flotante";
                e.textContent = alAzar(EMOJIS_NEUTROS);
                e.style.left = (5 + Math.random() * 90) + "vw";
                e.style.top = (8 + Math.random() * 80) + "vh";
                e.style.fontSize = (26 + Math.random() * 34) + "px";
                e.style.animationDelay = (-Math.random() * 12) + "s";
                e.style.animationDuration = (10 + Math.random() * 8) + "s";

                document.body.appendChild(e);
            }
        }


        function chispaMascota() {

            if (document.hidden) return;

            const caja = document.getElementById("capi");

            if (!caja) return;

            const r = caja.getBoundingClientRect();

            if (!r.width) return;

            const e = document.createElement("div");

            e.className = "chispa";
            e.textContent = ["✨", "⭐", "💫", "🌟"][Math.floor(Math.random() * 4)];
            e.style.left = (r.left + Math.random() * r.width) + "px";
            e.style.top = (
                r.top + r.height * 0.2 + Math.random() * r.height * 0.5
            ) + "px";

            document.body.appendChild(e);

            setTimeout(function () { e.remove(); }, 2000);
        }


        function ripple(btn, e) {

            const rect = btn.getBoundingClientRect();

            const size = Math.max(rect.width, rect.height);

            const r = document.createElement("span");

            r.style.position = "absolute";
            r.style.borderRadius = "50%";
            r.style.background = "rgba(255,255,255,.5)";
            r.style.width = r.style.height = size + "px";
            r.style.left = (e.clientX - rect.left - size / 2) + "px";
            r.style.top = (e.clientY - rect.top - size / 2) + "px";
            r.style.transform = "scale(0)";
            r.style.pointerEvents = "none";
            r.style.transition = "transform .6s ease, opacity .6s ease";

            btn.appendChild(r);

            requestAnimationFrame(function () {
                r.style.transform = "scale(2.4)";
                r.style.opacity = "0";
            });

            setTimeout(function () { r.remove(); }, 700);
        }


        // ===== LA MASCOTA SE INCLINA HACIA EL CURSOR =====

        document.addEventListener("mousemove", function (e) {

            const caja = document.getElementById("capi");

            if (!caja) return;

            const centro = window.innerWidth / 2;

            const desplaz = (e.clientX - centro) / centro;

            caja.style.setProperty("--tilt", (desplaz * 6).toFixed(2) + "deg");
        });


        // =================================================
        // TEST INSTANTÁNEO
        // =================================================

        function iniciarTestRapido(datos) {

            const PREGUNTAS = JSON.parse(
                document.getElementById("datosPreguntas").textContent
            );

            const TOTAL = PREGUNTAS.length;

            const zona = document.getElementById("zonaPregunta");

            const ICONOS = [
                "✨", "🌟", "💫", "⭐", "🔮",
                "🎈", "🎯", "🌈", "💠", "🪄"
            ];

            const OPCIONES = [
                [1, "Muy en desacuerdo", "😕"],
                [2, "En desacuerdo", "🙁"],
                [3, "Neutral", "😐"],
                [4, "De acuerdo", "🙂"],
                [5, "Muy de acuerdo", "😄"]
            ];

            let indice = 0;
            let respuestas = {};
            let bloqueado = false;

            function esc(s) {
                return String(s)
                    .replace(/&/g, "&amp;")
                    .replace(/</g, "&lt;")
                    .replace(/>/g, "&gt;");
            }

            function html(i) {

                const p = PREGUNTAS[i];

                const icono = ICONOS[i % ICONOS.length];

                const progreso = Math.round(((i + 1) / TOTAL) * 100);

                let ops = "";

                for (let k = 0; k < OPCIONES.length; k++) {

                    const o = OPCIONES[k];

                    ops +=
                        '<label class="option">' +
                            '<input type="radio" name="puntuacion" value="' + o[0] + '" required>' +
                            '<span class="emoji-op">' + o[2] + '</span>' +
                            '<span>' + o[1] + '</span>' +
                        '</label>';
                }

                const textoBoton =
                    (i === TOTAL - 1) ? "🎉 Finalizar test" : "Siguiente →";

                return '' +
                    '<div class="progress-area">' +
                        '<div class="progress-info">' +
                            '<span>Pregunta ' + (i + 1) + ' de ' + TOTAL + '</span>' +
                            '<strong>' + progreso + '%</strong>' +
                        '</div>' +
                        '<div class="progress">' +
                            '<div class="progress-bar" data-pct="' + progreso + '" style="width:0"></div>' +
                        '</div>' +
                    '</div>' +
                    '<p class="question" style="display:flex;align-items:center;gap:12px;">' +
                        '<span class="icono-area">' + icono + '</span>' +
                        esc(p.texto) +
                    '</p>' +
                    '<form id="formPregunta" method="POST" action="/responder">' +
                        '<input type="hidden" name="pregunta_id" value="' + p.id + '">' +
                        ops +
                        '<button class="btn-main" type="submit">' + textoBoton + '</button>' +
                    '</form>';
            }

            function bindForm() {

                const form = document.getElementById("formPregunta");

                if (!form) return;

                form.addEventListener("submit", function (e) {

                    e.preventDefault();

                    const sel = form.querySelector(
                        'input[name="puntuacion"]:checked'
                    );

                    if (!sel) {
                        form.classList.remove("sacudir");
                        void form.offsetWidth;
                        form.classList.add("sacudir");
                        return;
                    }

                    elegir(sel.value, sel);
                });

                const radios = form.querySelectorAll('input[name="puntuacion"]');

                for (let k = 0; k < radios.length; k++) {

                    radios[k].addEventListener("change", function () {
                        elegir(this.value, this);
                    });
                }
            }

            function pintar(i) {

                zona.classList.remove("entrando");

                zona.innerHTML = html(i);

                void zona.offsetWidth;

                zona.classList.add("entrando");

                const bar = zona.querySelector(".progress-bar");

                if (bar) {
                    const pct = bar.getAttribute("data-pct");
                    requestAnimationFrame(function () {
                        bar.style.width = pct + "%";
                    });
                }

                bindForm();
            }

            function elegir(valor, input) {

                if (bloqueado) return;

                bloqueado = true;

                const p = PREGUNTAS[indice];

                respuestas[p.id] = parseInt(valor, 10);

                const lab = input.closest(".option");

                if (lab) lab.classList.add("elegida");

                setTimeout(function () {

                    indice++;

                    if (indice >= TOTAL) {
                        finalizar();
                        return;
                    }

                    pintar(indice);

                    bloqueado = false;

                }, 190);
            }

            function finalizar() {

                const ov = document.getElementById("cargando");

                const txt = ov ? ov.querySelector("span") : null;

                if (txt) txt.textContent = "Calculando resultados...";

                if (ov) ov.classList.add("visible");

                fetch(datos.getAttribute("data-enviar"), {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ respuestas: respuestas })
                })
                .then(function (r) { return r.json(); })
                .then(function (res) {
                    window.location.href =
                        (res && res.url) ? res.url : "/procesar_resultados";
                })
                .catch(function () {
                    window.location.href = "/procesar_resultados";
                });
            }

            // atajos 1-5
            document.addEventListener("keydown", function (e) {

                if (bloqueado) return;

                const n = parseInt(e.key, 10);

                if (n >= 1 && n <= 5) {

                    const inp = document.querySelector(
                        '#formPregunta input[value="' + n + '"]'
                    );

                    if (inp) {
                        inp.checked = true;
                        elegir(String(n), inp);
                    }
                }
            });

            // anima la barra del primer render
            const barInicial = zona.querySelector(".progress-bar");

            if (barInicial) {
                const pct = barInicial.getAttribute("data-pct");
                barInicial.style.width = "0";
                setTimeout(function () {
                    barInicial.style.width = pct + "%";
                }, 120);
            }

            bindForm();
        }


        document.addEventListener("DOMContentLoaded", function () {

            const barra = document.getElementById("barraCarga");

            if (barra) {
                setTimeout(function () { barra.style.width = "100%"; }, 60);
                setTimeout(function () { barra.style.opacity = "0"; }, 800);
            }


            const contadores = document.querySelectorAll("[data-contar]");

            for (let i = 0; i < contadores.length; i++) {

                (function (el) {

                    const objetivo = parseFloat(el.getAttribute("data-contar"));

                    let actual = 0;

                    const inc = objetivo / 60;

                    const timer = setInterval(function () {

                        actual += inc;

                        if (actual >= objetivo) {
                            actual = objetivo;
                            clearInterval(timer);
                        }

                        el.textContent = actual.toFixed(1);

                    }, 16);

                })(contadores[i]);
            }


            const anillos = document.querySelectorAll("circle[data-anillo]");

            for (let i = 0; i < anillos.length; i++) {

                (function (c) {

                    const pct = parseFloat(c.getAttribute("data-anillo"));

                    const radio = c.r.baseVal.value;

                    const circ = 2 * Math.PI * radio;

                    c.style.strokeDasharray = circ;
                    c.style.strokeDashoffset = circ;

                    setTimeout(function () {
                        c.style.strokeDashoffset = circ - (pct / 100) * circ;
                    }, 200);

                })(anillos[i]);
            }


            flotantesNeutros();


            if (document.getElementById("activarConfeti")) {

                setTimeout(lanzarConfeti, 350);

                const img = document.getElementById("mascotaImg");

                if (img) img.classList.add("celebra");
            }


            setInterval(function () {

                if (document.hidden) return;

                const img = document.getElementById("mascotaImg");

                if (!img) return;

                if (img.classList.contains("celebra")) return;
                if (img.classList.contains("salta")) return;

                img.classList.add("salta");

                setTimeout(function () { img.classList.remove("salta"); }, 820);

            }, 9000);


            setInterval(chispaMascota, 2600);


            // ===== TEST RÁPIDO (con red de seguridad) =====

            const datos = document.getElementById("datosTest");

            if (datos) {
                try {
                    iniciarTestRapido(datos);
                } catch (err) {
                    console.error("Modo rápido no disponible:", err);
                }
            }


            // overlay solo en formularios normales
            const forms = document.querySelectorAll("form");

            for (let i = 0; i < forms.length; i++) {

                forms[i].addEventListener("submit", function () {

                    if (this.id === "formPregunta") return;

                    const ov = document.getElementById("cargando");

                    if (ov) ov.classList.add("visible");
                });
            }

        });


        // ===== DELEGACIÓN GLOBAL =====

        document.addEventListener("click", function (e) {

            const op = e.target.closest(".option");

            if (op) {
                estallidoEmojis(e.clientX, e.clientY);
                capiReacciona();
            }

            const btn = e.target.closest(".btn-main");

            if (btn) ripple(btn, e);
        });

    </script>

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

        <meta name="theme-color" content="#6366f1">

        <title>{escape(titulo)}</title>

        {estilos()}

    </head>

    <body>

        <div class="barra-carga" id="barraCarga"></div>


        <div class="fondo">
            <div class="orbe o1"></div>
            <div class="orbe o2"></div>
            <div class="orbe o3"></div>
        </div>


        <button
            class="tema-btn"
            id="temaBtn"
            onclick="alternarTema()"
            title="Cambiar tema"
        >
            🌙
        </button>


        {contenido}

        {mascota_html()}


        <div class="cargando" id="cargando">
            <div class="spinner"></div>
            <span>Preparando...</span>
        </div>


        {scripts()}

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
                onerror="this.style.display='none'"
            >
        </div>


        <header class="hero">

            <h1>Test Vocacional</h1>

            <p>
                Descubre qué carrera se adapta mejor
                a tus intereses, habilidades y preferencias.
            </p>

        </header>


        <section class="card-custom">

            <div class="welcome-icon">🎓</div>

            <h2 style="text-align:center;margin:0 0 6px;">
                ¡Comencemos!
            </h2>

            <p style="text-align:center;color:var(--muted);line-height:1.6;margin-bottom:26px;">
                Completa tus datos para iniciar el test vocacional.
            </p>


            <form method="POST" action="/iniciar_test">

                <div class="field">
                    <label class="form-label" for="nombre">Nombre</label>
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
                    <label class="form-label" for="email">Correo electrónico</label>
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
                    <label class="form-label" for="edad">Edad</label>
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


                <button type="submit" class="btn-main">
                    Comenzar test →
                </button>

            </form>

        </section>

    </main>

    """

    return pagina_base("Test Vocacional", contenido)


# =========================================================
# INICIAR TEST
# =========================================================

@app.route("/iniciar_test", methods=["POST"])
def iniciar_test():

    nombre = request.form.get("nombre", "").strip()
    email = request.form.get("email", "").strip()
    edad = request.form.get("edad", "").strip()

    if not nombre or not email or not edad:
        return redirect(url_for("index"))

    session["nombre"] = nombre
    session["email"] = email
    session["edad"] = edad

    preguntas = Pregunta.query.all()

    if not preguntas:
        return "<h2>No existen preguntas registradas.</h2>"

    preguntas_ids = [p.id for p in preguntas]

    random.shuffle(preguntas_ids)

    session["preguntas_orden"] = preguntas_ids
    session["pregunta_actual"] = 0
    session["respuestas"] = {}

    return redirect(url_for("test"))


# =========================================================
# MOSTRAR PREGUNTAS
# =========================================================

@app.route("/test")
def test():

    if "nombre" not in session:
        return redirect(url_for("index"))

    preguntas_orden = session.get("preguntas_orden", [])

    if not preguntas_orden:
        return redirect(url_for("index"))

    actual = session.get("pregunta_actual", 0)

    if actual >= len(preguntas_orden):
        return redirect(url_for("procesar_resultados"))

    # lista completa -> se manda una sola vez al navegador
    preguntas = []

    for pid in preguntas_orden:

        p = db.session.get(Pregunta, pid)

        if p is not None:
            preguntas.append({"id": p.id, "texto": p.texto})

    total = len(preguntas)

    if total == 0:
        return "<h2>No existen preguntas registradas.</h2>"

    if actual >= total:
        actual = total - 1

    datos_json = json.dumps(preguntas, ensure_ascii=False)

    contenido = f"""

    <main class="app-container">

        <div
            id="datosTest"
            data-enviar="{url_for('enviar_respuestas')}"
            style="display:none"
        ></div>

        <script type="application/json" id="datosPreguntas">{datos_json}</script>

        <section class="card-custom" id="tarjetaTest">

            <div id="zonaPregunta">{render_pregunta(preguntas[actual], actual, total)}</div>

        </section>

    </main>

    """

    return pagina_base("Test en curso", contenido)


# =========================================================
# GUARDAR RESPUESTA (fallback sin JS)
# =========================================================

@app.route("/responder", methods=["POST"])
def responder():

    pregunta_id = request.form.get("pregunta_id")
    puntuacion = request.form.get("puntuacion")

    if not pregunta_id or not puntuacion:
        return redirect(url_for("test"))

    respuestas = session.get("respuestas", {})

    respuestas[str(pregunta_id)] = int(puntuacion)

    session["respuestas"] = respuestas

    session["pregunta_actual"] = session.get("pregunta_actual", 0) + 1

    return redirect(url_for("test"))


# =========================================================
# RECIBIR TODAS LAS RESPUESTAS (modo rápido)
# =========================================================

@app.route("/enviar_respuestas", methods=["POST"])
def enviar_respuestas():

    datos = request.get_json(silent=True) or {}

    recibidas = datos.get("respuestas", {})

    limpias = {}

    for k, v in recibidas.items():

        try:
            limpias[str(int(k))] = int(v)
        except (TypeError, ValueError):
            continue

    session["respuestas"] = limpias

    return {"ok": True, "url": url_for("procesar_resultados")}


# =========================================================
# PROCESAR RESULTADOS
# =========================================================

@app.route("/procesar_resultados")
def procesar_resultados():

    respuestas = session.get("respuestas", {})

    if not respuestas:
        return redirect(url_for("index"))

    usuario = Usuario(
        nombre=session.get("nombre", ""),
        email=session.get("email", ""),
        edad=int(session.get("edad", 0) or 0),
    )

    db.session.add(usuario)
    db.session.commit()

    puntuaciones = defaultdict(int)
    total_preguntas = defaultdict(int)

    for pregunta_id, puntuacion in respuestas.items():

        pregunta = db.session.get(Pregunta, int(pregunta_id))

        if pregunta is None:
            continue

        db.session.add(
            Respuesta(
                usuario_id=usuario.id,
                pregunta_id=pregunta.id,
                puntuacion=puntuacion,
            )
        )

        puntuaciones[pregunta.area_id] += puntuacion
        total_preguntas[pregunta.area_id] += 1

    db.session.commit()

    resultados = []

    for area_id, puntos in puntuaciones.items():

        cantidad = total_preguntas[area_id]

        if cantidad == 0:
            continue

        maximo = cantidad * 5
        porcentaje = (puntos / maximo) * 100

        db.session.add(
            Resultado(
                usuario_id=usuario.id,
                area_id=area_id,
                puntuacion_total=puntos,
                porcentaje=porcentaje,
            )
        )

        area = db.session.get(AreaVocacional, area_id)
        carreras = Carrera.query.filter_by(area_id=area_id).all()

        resultados.append((area, porcentaje, carreras))

    db.session.commit()

    resultados.sort(key=lambda x: x[1], reverse=True)

    tarjetas_secundarias = ""

    for area, porcentaje, carreras in resultados[1:]:

        tema = tema_area(area.id)

        nombre_carrera = (
            escape(carreras[0].nombre) if carreras else escape(area.nombre)
        )

        tarjetas_secundarias += f"""

        <div class="result-card">

            <div style="display:flex;align-items:center;gap:14px;margin-bottom:14px;">

                <span style="font-size:2rem;">🎯</span>

                <div style="flex:1;">

                    <h3 style="margin:0 0 4px;font-size:1.1rem;">
                        {nombre_carrera}
                    </h3>

                    <span style="color:var(--muted);font-size:.85rem;">
                        {escape(area.nombre)}
                    </span>

                </div>

                <strong style="font-size:1.25rem;color:{tema["c1"]};">
                    <span data-contar="{porcentaje:.1f}">{porcentaje:.1f}</span>%
                </strong>

            </div>

            <div class="progress">
                <div
                    class="progress-bar"
                    data-pct="{porcentaje:.1f}"
                    style="background:linear-gradient(90deg,{tema["c1"]},{tema["c2"]});"
                ></div>
            </div>

        </div>

        """

    if resultados:

        mejor_area, mejor_porcentaje, carreras = resultados[0]

        tema = tema_area(mejor_area.id)

        nombre_principal = (
            escape(carreras[0].nombre) if carreras else escape(mejor_area.nombre)
        )

        descripcion = (
            escape(carreras[0].descripcion)
            if carreras and carreras[0].descripcion
            else "Esta carrera se relaciona con tus intereses y habilidades."
        )

        radio = 62

        resultado_principal = f"""

        <div class="result-card destacado" style="text-align:center;">

            <div class="trophy">🏆</div>

            <p style="color:var(--muted);margin:0 0 14px;">
                La carrera que más se relaciona con tus respuestas es:
            </p>

            <div class="anillo">

                <svg width="150" height="150">
                    <circle
                        cx="75" cy="75" r="{radio}"
                        fill="none"
                        stroke="rgba(148,163,184,.25)"
                        stroke-width="10"
                    ></circle>
                    <circle
                        cx="75" cy="75" r="{radio}"
                        fill="none"
                        stroke="{tema["c1"]}"
                        stroke-width="10"
                        stroke-linecap="round"
                        data-anillo="{mejor_porcentaje:.1f}"
                        style="transition:stroke-dashoffset 1.4s cubic-bezier(.22,1,.36,1);"
                    ></circle>
                </svg>

                <div class="valor" style="color:{tema["c1"]};">
                    <span data-contar="{mejor_porcentaje:.1f}">{mejor_porcentaje:.1f}</span>%
                </div>

            </div>

            <h2 style="color:{tema["c1"]};margin:8px 0 6px;font-size:clamp(1.5rem,5vw,2.1rem);">
                {nombre_principal}
            </h2>

            <p style="color:var(--muted);margin:0;">afinidad con tu perfil</p>

            <div class="career-description" style="text-align:left;">
                <strong>Sobre esta carrera:</strong><br>
                {descripcion}
            </div>

            <div class="area-result">
                Área vocacional: <strong>{escape(mejor_area.nombre)}</strong>
            </div>

        </div>

        """

    else:

        resultado_principal = """

        <div class="result-card" style="text-align:center;">
            <h2>No se pudo determinar una carrera</h2>
            <p>No se encontraron resultados suficientes.</p>
        </div>

        """

    titulo_secundarias = ""

    if tarjetas_secundarias:
        titulo_secundarias = """

        <h3 style="margin:34px 0 16px;font-size:1.2rem;text-align:center;color:var(--muted);">
            Otras áreas con afinidad
        </h3>

        """

    contenido = f"""

    <main class="app-container">

        <div class="logo-wrapper">
            <img
                src="/static/logo.jpeg"
                alt="Logo ITSJC"
                class="logo"
                onerror="this.style.display='none'"
            >
        </div>


        <section class="card-custom">

            <header class="result-header">

                <h1>🎉 ¡Test completado!</h1>

                <p style="color:var(--muted);">
                    Resultado para <strong>{escape(usuario.nombre)}</strong>
                </p>

            </header>

            {resultado_principal}

            {titulo_secundarias}

            {tarjetas_secundarias}

            <div style="margin-top:26px;">
                <a href="/reiniciar" class="btn-secondary">
                    ↻ Realizar otro test
                </a>
            </div>

        </section>


        <div id="activarConfeti"></div>

    </main>

    """

    return pagina_base("Resultados", contenido)


# =========================================================
# REINICIAR
# =========================================================

@app.route("/reiniciar")
def reiniciar():

    session.clear()
    return redirect(url_for("index"))


# =========================================================
# INICIALIZAR BASE DE DATOS
# =========================================================

def init_db():

    with app.app_context():

        db.create_all()

        if not AreaVocacional.query.first():

            areas = [
                ("Sistemas Informáticos",
                 "Tecnología, programación y desarrollo de sistemas."),
                ("Industria de Alimentos",
                 "Procesamiento, elaboración y control de alimentos."),
                ("Mecánica Automotriz",
                 "Mantenimiento y reparación de vehículos."),
                ("Electromecánica",
                 "Electricidad, electrónica y sistemas mecánicos."),
            ]

            for nombre, descripcion in areas:
                db.session.add(
                    AreaVocacional(nombre=nombre, descripcion=descripcion)
                )

            db.session.commit()

            carreras = [
                ("Sistemas Informáticos",
                 "Aprenderás programación, desarrollo de software, bases de datos y tecnología.", 1),
                ("Industria de Alimentos",
                 "Aprenderás a procesar, elaborar y controlar la calidad de productos alimenticios.", 2),
                ("Mecánica Automotriz",
                 "Aprenderás mantenimiento, diagnóstico y reparación de vehículos.", 3),
                ("Electromecánica",
                 "Aprenderás electricidad, electrónica, motores y sistemas mecánicos.", 4),
            ]

            for nombre, descripcion, area_id in carreras:
                db.session.add(
                    Carrera(nombre=nombre, descripcion=descripcion, area_id=area_id)
                )

            db.session.commit()

            preguntas = [
                ("Me interesa aprender a programar y crear aplicaciones", 1),
                ("Disfruto trabajando con computadoras y tecnología", 1),
                ("Me gustaría aprender sobre bases de datos", 1),
                ("Me interesa crear páginas web y sistemas informáticos", 1),
                ("Me gusta resolver problemas utilizando la tecnología", 1),
                ("Me interesa aprender cómo se elaboran y procesan los alimentos", 2),
                ("Me gustaría trabajar en la producción de productos alimenticios", 2),
                ("Me interesa conocer los procesos de conservación de alimentos", 2),
                ("Me preocupa que los alimentos cumplan normas de higiene y calidad", 2),
                ("Me gustaría experimentar con nuevos productos alimenticios", 2),
                ("Me interesa conocer cómo funcionan los motores de los vehículos", 3),
                ("Disfruto reparar y realizar mantenimiento a vehículos", 3),
                ("Me gustaría aprender a identificar fallas mecánicas en automóviles", 3),
                ("Me interesa conocer las diferentes partes de un automóvil", 3),
                ("Me gustaría trabajar en el mantenimiento y reparación de vehículos", 3),
                ("Me interesa aprender sobre electricidad y circuitos eléctricos", 4),
                ("Me gustaría trabajar con motores eléctricos y máquinas", 4),
                ("Me interesa conocer cómo funcionan los sistemas electrónicos", 4),
                ("Disfruto solucionar problemas eléctricos y mecánicos", 4),
                ("Me gustaría aprender a instalar y mantener equipos electromecánicos", 4),
            ]

            for texto, area_id in preguntas:
                db.session.add(Pregunta(texto=texto, area_id=area_id))

            db.session.commit()

            print("Base de datos inicializada correctamente.")


# =========================================================
# EJECUTAR
# =========================================================

if __name__ == "__main__":

    init_db()

    app.run(debug=True, host="0.0.0.0", port=5000)