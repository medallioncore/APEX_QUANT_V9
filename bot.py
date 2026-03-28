import yfinance as yf
import numpy as np
import requests
import datetime

# VERSIONE DEL SISTEMA: APEX V9.1 (MEDALLION CORE V5.8 FINAL)
# ==========================================
TOKEN_TELEGRAM = '8762905583:AAEivBbsZPIXwaBYqQ3krdq8STpCMYqUgIk'
CHAT_ID = '8353806939'

portafoglio_attivo = {
    "BAH": {"PMC": 69.65, "Data_Acquisto": "2026-03-23", "SL_Price": 64.07},
    "IB1T.DE": {"PMC": 5.82, "Data_Acquisto": "2026-03-09", "SL_Price": 5.35},
    "DFEN.DE": {"PMC": 58.45, "Data_Acquisto": "2026-03-23", "SL_Price": 53.77},
    "URNU.MI": {"PMC": 26.20, "Data_Acquisto": "2026-03-16", "SL_Price": 24.10}
}

watchlist_ingressi = {
    "DFEN.DE": 400, "ALB": 400, "QCOM": 400, "AMBA": 400, "FCX": 400, 
    "REMX.MI": 400, "QCLN.MI": 400, "ETN": 400, "COPG.MI": 400, "LDO.MI": 400, 
    "ADBE": 400, "NOW": 400, "U-UN.TO": 400, "YCA.L": 400, "IB1T.DE": 400, 
    "URNM.DE": 400, "UEC": 400, "SWMR": 400
}

def get_price_safe(ticker):
    """Estrazione antiproiettile per evitare crash di YFinance"""
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
    oggi = datetime.datetime.today()
    
    # 1. GATEKEEPER MACRO (Sensore VIX tarato a >25)
    macro = "VERDE"
    vix = get_price_safe("^VIX")
    if vix:
        macro = "ROSSO" if vix > 25 else "GIALLO" if vix > 20 else "VERDE"

    # 2. MOTORE FX VELOCE (Fallback di sicurezza incluso)
    fx = {"GBP": 1.17, "CAD": 0.68, "USD": 0.92}
    try:
        usd_data = get_price_safe("USDEUR=X")
        if usd_data: fx["USD"] = usd_data
    except: pass

    # 3. M1_DEFENSE & USCITE PORTAFOGLIO
    report_p = ""
    for ticker, dati in portafoglio_attivo.items():
        p_att = get_price_safe(ticker)
        if not p_att:
            report_p += f"⚠️ Errore dati per {ticker}\n"
            continue
            
        p_lordo = ((p_att / dati["PMC"]) - 1) * 100
        giorni_hold = (oggi - datetime.datetime.strptime(dati["Data_Acquisto"], "%Y-%m-%d")).days
        
        # Logica di Esecuzione Master 2.0
        if p_att <= dati["SL_Price"]:
            report_p += f"🔴 <b>SELL (STOP LOSS):</b> {ticker} | P&L: {p_lordo:.2f}%\n"
        elif p_lordo >= 26.0:
            report_p += f"🟢 <b>SELL (TARGET 26%):</b> {ticker} | P&L: +{p_lordo:.2f}%\n"
        elif giorni_hold > 45 and p_lordo < 3.0:
            report_p += f"🟡 <b>SELL (TIMEDECAY):</b> {ticker} | {giorni_hold}gg | P&L: {p_lordo:.2f}%\n"
        else:
            report_p += f"🔹 <b>HOLD:</b> {ticker} | P&L: {p_lordo:+.2f}% | Hold: {giorni_hold}gg\n"

    # 4. M2_SUPPLY & RADAR POC CON FX
    report_w = ""
    if macro == "ROSSO":
        report_w = "🚨 <b>VETO ROSSO:</b> VIX > 25. Cash is King. Zero Ingressi.\n"
    else:
        for ticker, budget in watchlist_ingressi.items():
            try:
                df = yf.download(ticker, period="1y", progress=False)
                if df.empty: continue
                p_att = float(df['Close'].values[-1])
                
                # Conversione FX Live
                tasso = 1.0
                if ticker.endswith(".L"): tasso = fx["GBP"] / 100 
                elif ticker.endswith(".TO"): tasso = fx["CAD"]
                elif not ticker.endswith(".MI") and not ticker.endswith(".DE") and not ticker.endswith(".AS"): 
                    tasso = fx["USD"]

                counts, bins = np.histogram(df.tail(252)['Close'], bins=50, weights=df.tail(252)['Volume'])
                poc = (bins[np.argmax(counts)] + bins[np.argmax(counts)+1]) / 2
                target_in = poc * 1.02
                dist = ((p_att / target_in) - 1) * 100
                
                if dist <= 3.0:
                    quote = int(budget / (target_in * tasso))
                    valore_euro = quote * target_in * tasso
                    report_w += f"🎯 <b>LIMIT BUY POC:</b> {ticker}\n"
                    report_w += f"▪️ Target: {target_in:.2f} | Quote: {quote} ({valore_euro:.2f}€)\n\n"
            except: continue
            
    if not report_w and macro != "ROSSO":
        report_w = "<i>Nessun asset in zona POC.</i>\n"

    # 5. INVIO TELEGRAM
    msg = f"📊 <b>APEX V9.1: MEDALLION CORE</b> 📊\n"
    msg += f"🌍 MACRO STATUS: {macro} (VIX)\n\n"
    msg += "🛡️ <b>M1 DEFENSE & USCITE:</b>\n" + (report_p if report_p else "Vuoto\n")
    msg += "\n🔭 <b>M2 SUPPLY (RADAR POC):</b>\n" + report_w
    invia_telegram(msg)

if __name__ == "__main__":
    MASTER_START()
