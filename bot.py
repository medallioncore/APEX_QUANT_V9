import yfinance as yf
import numpy as np
import requests

# VERSIONE DEL SISTEMA: APEX V9 (PHOENIX)
# ==========================================
TOKEN_TELEGRAM = '8762905583:AAEivBbsZPIXwaBYqQ3krdq8STpCMYqUgIk'
CHAT_ID = '8353806939'

portafoglio_attivo = {
    "BAH": {"PMC": 69.65, "Data_Acquisto": "2026-03-23"},
    "IB1T.DE": {"PMC": 5.82, "Data_Acquisto": "2026-03-09"},
    "DFEN.DE": {"PMC": 58.45, "Data_Acquisto": "2026-03-23"},
    "URNU.MI": {"PMC": 26.20, "Data_Acquisto": "2026-03-16"}
}

watchlist_ingressi = {
    "DFEN.DE": 400, "ALB": 400, "QCOM": 400, "AMBA": 400, "FCX": 400, 
    "REMX.MI": 400, "QCLN.MI": 400, "ETN": 400, "COPG.MI": 400, "LDO.MI": 400, 
    "ADBE": 400, "NOW": 400, "U-UN.TO": 400, "YCA.L": 400, "IB1T.DE": 400, 
    "URNM.DE": 400, "UEC": 400, "SWMR": 400
}

def get_price_safe(ticker):
    try:
        df = yf.download(ticker, period="5d", progress=False)
        if not df.empty:
            return float(df['Close'].values[-1])
    except: pass
    return None

def invia_telegram(messaggio):
    url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
    requests.post(url, data={'chat_id': CHAT_ID, 'text': messaggio, 'parse_mode': 'HTML'})

def MASTER_START():
    macro = "VERDE"
    vix = get_price_safe("^VIX")
    if vix:
        macro = "ROSSO" if vix > 30 else "GIALLO" if vix > 22 else "VERDE"

    report_p = ""
    for ticker, dati in portafoglio_attivo.items():
        p_att = get_price_safe(ticker)
        if p_att:
            p_lordo = ((p_att / dati["PMC"]) - 1) * 100
            report_p += f"🔹 <b>{ticker}</b>: {p_lordo:+.2f}% (P: {p_att:.2f})\n"
        else:
            report_p += f"⚠️ Errore server dati per {ticker}\n"

    report_w = ""
    if macro == "ROSSO":
        report_w = "🚨 <b>VETO ROSSO:</b> Mercato volatile. Nessun ingresso.\n"
    else:
        for ticker, budget in watchlist_ingressi.items():
            try:
                df = yf.download(ticker, period="1y", progress=False)
                if df.empty: continue
                p_att = float(df['Close'].values[-1])
                counts, bins = np.histogram(df.tail(252)['Close'], bins=50, weights=df.tail(252)['Volume'])
                poc = (bins[np.argmax(counts)] + bins[np.argmax(counts)+1]) / 2
                target_in = poc * 1.02
                dist = ((p_att / target_in) - 1) * 100
                if dist <= 3.0:
                    quote = int(budget / target_in)
                    report_w += f"🎯 <b>BUY LIMIT:</b> {ticker} | Distanza: {dist:.1f}%\n"
            except: continue
            
    if not report_w and macro != "ROSSO":
        report_w = "<i>Nessun asset in zona POC.</i>\n"

    msg = f"📊 <b>APEX V9: PHOENIX ZERO</b> 📊\n"
    msg += f"🌍 MACRO STATUS: {macro}\n\n"
    msg += "🛡️ <b>PORTAFOGLIO:</b>\n" + (report_p if report_p else "Vuoto\n")
    msg += "\n🔭 <b>RADAR:</b>\n" + report_w
    invia_telegram(msg)

if __name__ == "__main__":
    MASTER_START()
