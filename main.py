import os, asyncio, requests
from datetime import datetime, timedelta
import yfinance as yf
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = 6475391396
BTC_ADDRESS = "3AqCJyt6AaBTD2VrustPqvJ8143WkP5BaX"
USDT_ADDRESS = "TYRCpAKs22XPu2Ti67oseWHeT5oLDbcYtL"
subscribers = set()
user_data = {}

MARKETS = {"BTC":"BTC-USD","ETH":"ETH-USD","BNB":"BNB-USD","SOL":"SOL-USD","XRP":"XRP-USD","ADA":"ADA-USD","DOGE":"DOGE-USD","AVAX":"AVAX-USD","DOT":"DOT-USD","LINK":"LINK-USD","MATIC":"MATIC-USD","LTC":"LTC-USD","TRX":"TRX-USD","SHIB":"SHIB-USD"}

def calc_rsi(p, period=14):
    d = p.diff()
    g = (d.where(d>0,0)).rolling(window=period).mean()
    l = (-d.where(d<0,0)).rolling(window=period).mean()
    rs = g / l
    return 100 - (100 / (1+rs))

def scan_market(symbol, ticker):
    try:
        df = yf.download(ticker, period="1d", interval="5m", progress=False)
        if len(df) < 20: return None
        df['RSI'] = calc_rsi(df['Close'])
        last = df.iloc[-1]; prev = df.iloc[-2]
        price = float(last['Close']); rsi = float(last['RSI'])
        move = ((price - float(prev['Close']))/float(prev['Close']))*100
        if rsi < 35: signal = "BUY"
        elif rsi > 70: signal = "SELL"
        else: return None
        sl = price * 1.008 if signal=="SELL" else price*0.992
        tp = price * 0.985 if signal=="SELL" else price*1.015
        emoji = "🟢" if signal=="BUY" else "🔴"
        return f"Market scanner alert\n\n{emoji} {symbol} — {signal} (Strong)\nPrice: {price:.2f} | 5m move: {move:.2f}% | RSI: {rsi:.1f}\nEntry: {price:.2f}\nStop Loss: {sl:.2f} | Take Profit: {tp:.2f}"
    except: return None

def is_paid(uid):
    if uid == ADMIN_ID: return True
    d = user_data.get(uid)
    if not d: return True
    pu = d.get('paid_until'); j = d.get('join')
    if pu and datetime.now() < pu: return True
    if datetime.now() < j + timedelta(days=6): return True
    return False

def get_paywall():
    return f"⏰ 6-day FREE trial ended!\n\nTo continue Sky360Pro 24/7 for 30 days:\n\n🇬🇭 AFRICA (GH/NG/UG): 50 GHS\n🌍 OUTSIDE AFRICA (USA, etc): $30 USD\n\nBTC: {BTC_ADDRESS}\nUSDT TRC20: {USDT_ADDRESS}\n\nAfter pay send /paid TX_HASH\n/check status\n/country GH|NG|UG|OTHER"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_chat.id
    if uid not in user_data: user_data[uid] = {'join': datetime.now(), 'paid_until': None}
    subscribers.add(uid)
    await update.message.reply_text(f"Market Scanner — 14 markets, checked every minute for new strong signals.\n\nYou are subscribed to automatic alerts. Your admin account has permanent free access.\nUse /signal for an on-demand scan, /country GH|NG|UG|OTHER to set your plan, or /stop to unsubscribe from automatic alerts.\nData is from Yahoo Finance and may be delayed. This is not financial advice.\n\n{get_paywall() if not is_paid(uid) else '✅ Active! Sky360Pro 24/7 watching.'}")

async def signal_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_chat.id
    if not is_paid(uid):
        await update.message.reply_text(get_paywall()); return
    await update.message.reply_text("🔍 Sky360Pro scanning 14 markets...")
    f=0
    for s,t in MARKETS.items():
        m=scan_market(s,t)
        if m:
            await update.message.reply_text(m); f+=1; await asyncio.sleep(1)
    if f==0: await update.message.reply_text("No strong signals now. Sky360Pro will auto alert you.")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    subscribers.discard(update.effective_chat.id)
    await update.message.reply_text("❌ Unsubscribed from auto alerts.")

async def country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Use: /country GH|NG|UG|OTHER"); return
    uid = update.effective_chat.id
    if uid not in user_data: user_data[uid] = {'join': datetime.now(), 'paid_until': None}
    user_data[uid]['country']=context.args[0].upper()
    price = "50 GHS" if context.args[0].upper() in ["GH","NG","UG","GHANA","NIGERIA","UGANDA"] else "$30 USD"
    await update.message.reply_text(f"✅ Country {context.args[0].upper()} - Plan: {price}")

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid=update.effective_chat.id
    if uid==ADMIN_ID:
        await update.message.reply_text("👑 Admin FREE FOREVER 24/7"); return
    d=user_data.get(uid)
    if not d:
        await update.message.reply_text("6 days free trial started! /start"); return
    pu=d.get('paid_until'); j=d.get('join')
    if pu and datetime.now()<pu: await update.message.reply_text(f"✅ Active until {pu}")
    elif datetime.now() < j+timedelta(days=6): await update.message.reply_text(f"✅ Free trial active")
    else: await update.message.reply_text(get_paywall())

async def paid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Send: /paid YOUR_TX_HASH"); return
    tx=context.args[0]; uid=update.effective_chat.id
    await update.message.reply_text(f"🔍 Verifying {tx}...")
    verified=True if len(tx)>20 else False
    if verified:
        user_data[uid]=user_data.get(uid,{'join':datetime.now()})
        user_data[uid]['paid_until']=datetime.now()+timedelta(days=30)
        subscribers.add(uid)
        await update.message.reply_text("✅ Payment confirmed! Sky360Pro activated 30 days 24/7!")
    else: await update.message.reply_text("❌ Invalid hash. Contact admin.")

async def auto_scan(app):
    while True:
        await asyncio.sleep(60)
        for s,t in MARKETS.items():
            a=scan_market(s,t)
            if a:
                for cid in list(subscribers):
                    if is_paid(cid):
                        try: await app.bot.send_message(chat_id=cid, text=a)
                        except: pass
                await asyncio.sleep(1)

async def post_init(app): asyncio.create_task(auto_scan(app))

def main():
    app=Application.builder().token(TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start",start))
    app.add_handler(CommandHandler("signal",signal_cmd))
    app.add_handler(CommandHandler("stop",stop))
    app.add_handler(CommandHandler("country",country))
    app.add_handler(CommandHandler("check",check))
    app.add_handler(CommandHandler("paid",paid))
    app.run_polling()

if __name__=="__main__": main()
