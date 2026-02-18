import re
import os
import pandas as pd
from unidecode import unidecode
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# ==============================
# 🔐 COLOQUE SEU TOKEN AQUI
# ==============================

TOKEN = "8512712361:AAEd3bzXSAAdq7kaGKNyemRrLeHCB94pZak"

# ==============================
# 🔥 FUNÇÃO DE NORMALIZAÇÃO
# ==============================

def normalizar_endereco(endereco):
    if pd.isna(endereco):
        return ""

    endereco = str(endereco)
    endereco = unidecode(endereco).lower()

    substituicoes = {
        r"\bav\b": "avenida",
        r"\bav.\b": "avenida",
        r"\br\b": "rua",
        r"\br.\b": "rua",
        r"\btrav\b": "travessa",
        r"\btrav.\b": "travessa",
        r"\bal\b": "alameda",
        r"\bal.\b": "alameda",
        r"\bdr\b": "doutor",
        r"\bdr.\b": "doutor"
    }

    for padrao, novo in substituicoes.items():
        endereco = re.sub(padrao, novo, endereco)

    endereco = re.sub(r"[^a-z0-9\s]", " ", endereco)
    endereco = re.sub(r"\s+", " ", endereco).strip()

    numero_match = re.search(r"\d+", endereco)
    if not numero_match:
        return endereco

    numero = numero_match.group()
    rua = endereco.split(numero)[0].strip()

    return f"{rua} {numero}"

# ==============================
# 🚀 COMANDO /start
# ==============================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚚 FlowRota Bot\n\nEnvie a planilha Excel que organizo a rota para você."
    )

# ==============================
# 📦 PROCESSAR PLANILHA
# ==============================

async def tratar_planilha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    documento = await update.message.document.get_file()
    caminho_arquivo = "entrada.xlsx"
    await documento.download_to_drive(caminho_arquivo)

    df = pd.read_excel(caminho_arquivo)

    # 🔥 AGORA USANDO SEQUENCE COMO PACOTES
    coluna_pacotes = "Sequence"
    coluna_endereco = "Destination Address"

    df = df[[coluna_pacotes, coluna_endereco]].copy()
    df = df.dropna(subset=[coluna_endereco])
    df = df.dropna(subset=[coluna_pacotes])

    total_pacotes = len(df)

    # Normaliza endereço
    df["endereco_normalizado"] = df[coluna_endereco].apply(normalizar_endereco)

    # Agrupa por endereço
    df_agrupado = (
        df.groupby("endereco_normalizado")
        .agg({
            coluna_endereco: "first",
            coluna_pacotes: lambda x: ", ".join(x.astype(str))
        })
        .reset_index(drop=True)
    )

    total_paradas = len(df_agrupado)

    # Nome do arquivo com data
    data_hoje = datetime.now().strftime("%d-%m-%Y")
    nome_saida = f"rota_tratada_{data_hoje}.xlsx"

    df_agrupado.to_excel(nome_saida, index=False)

    # 📊 RESUMO TELEGRAM
    media = round(total_pacotes / total_paradas, 2) if total_paradas > 0 else 0

    resumo = (
        "🚚 *FLOWROTA - ROTA PROCESSADA*\n\n"
        f"📦 Total de pacotes: *{total_pacotes}*\n"
        f"📍 Total de paradas: *{total_paradas}*\n"
        f"📊 Média por parada: *{media}*\n\n"
        "✅ Planilha pronta para importar no app."
    )

    await update.message.reply_text(resumo, parse_mode="Markdown")
    await update.message.reply_document(document=open(nome_saida, "rb"))

    os.remove(caminho_arquivo)
    os.remove(nome_saida)

# ==============================
# 🤖 INICIAR BOT
# ==============================

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.Document.ALL, tratar_planilha))

print("🤖 FlowRota Bot rodando...")
app.run_polling()
from flask import Flask
import threading

app_web = Flask(__name__)

@app_web.route("/")
def home():
    return "FlowRota Bot está rodando!"

def run_web():
    app_web.run(host="0.0.0.0", port=10000)

# Rodar Flask em thread separada
threading.Thread(target=run_web).start()
