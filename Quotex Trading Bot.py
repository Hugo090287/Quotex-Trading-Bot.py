from fastapi import FastAPI
from pydantic import BaseModel
import numpy as np
import pandas as pd
import uvicorn
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

app = FastAPI()

# Configuración inicial del bot
class BotConfig(BaseModel):
    capital_total: float
    riesgo_bajo: float = 1.0  # % de capital en zonas no seguras
    riesgo_alto: float = 3.0  # % de capital en zonas seguras
    max_operaciones: int = 3  # Número máximo de operaciones por día
    activo: bool = False  # Estado del bot

config = BotConfig(capital_total=100)

def calcular_soporte_resistencia(data):
    soporte = data['low'].rolling(window=10).min()
    resistencia = data['high'].rolling(window=10).max()
    return soporte, resistencia

def calcular_rsi(data, period=14):
    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calcular_media_movil(data, period=10):
    return data['close'].rolling(window=period).mean()

def detectar_manipulacion(data):
    volatilidad = data['high'] - data['low']
    return (volatilidad > data['close'] * 0.02).astype(int)  # Marcamos si la volatilidad es mayor al 2%

@app.get("/", response_class=HTMLResponse)
def interfaz():
    return """
    <html>
        <head><title>Bot de Trading</title></head>
        <body>
            <h1>Bienvenido al Bot de Trading para Quotex</h1>
            <p>Para activar el bot, hacer clic en el siguiente enlace:</p>
            <a href="/activar">Activar Bot</a> | <a href="/desactivar">Desactivar Bot</a>
        </body>
    </html>
    """

@app.get("/estado")
def obtener_estado():
    return {"activo": config.activo, "capital_total": config.capital_total, "max_operaciones": config.max_operaciones}

@app.get("/activar")
def activar_bot():
    config.activo = True
    return "<h2>Bot activado</h2><a href='/'>Volver</a>"

@app.get("/desactivar")
def desactivar_bot():
    config.activo = False
    return "<h2>Bot desactivado</h2><a href='/'>Volver</a>"

@app.post("/analizar")
def analizar_mercado(datos: list):
    df = pd.DataFrame(datos)
    df['soporte'], df['resistencia'] = calcular_soporte_resistencia(df)
    df['rsi'] = calcular_rsi(df)
    df['media_movil'] = calcular_media_movil(df)
    df['manipulacion'] = detectar_manipulacion(df)
    df['entrada_compra'] = (df['rsi'] < 35) & (df['close'] > df['soporte'])
    df['entrada_venta'] = (df['rsi'] > 65) & (df['close'] < df['resistencia'])
    return df.tail(1).to_dict(orient='records')

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
