"""
真实股票数据获取脚本（基于 yfinance）
用法：python scripts/get_stock_data.py NVDA AAPL MSFT
输出：每支股票的完整数据，供投资z分析使用
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import yfinance as yf
import datetime

def get_rsi(closes, period=14):
    if len(closes) < period + 1:
        return None
    deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
    gains = [d if d > 0 else 0 for d in deltas[-period:]]
    losses = [-d if d < 0 else 0 for d in deltas[-period:]]
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 1)

def analyze(symbol):
    ticker = yf.Ticker(symbol)
    info = ticker.fast_info

    # 基本行情
    price  = round(info.get("lastPrice", 0), 2)
    prev   = round(info.get("previousClose", 0), 2)
    change = round(price - prev, 2)
    pct    = round((change / prev * 100) if prev else 0, 2)

    # 历史数据（30天）用于均线和RSI
    hist = ticker.history(period="30d")
    closes = list(hist["Close"])
    volumes = list(hist["Volume"])

    ma5  = round(sum(closes[-5:]) / 5, 2)  if len(closes) >= 5  else None
    ma20 = round(sum(closes[-20:]) / 20, 2) if len(closes) >= 20 else None
    rsi  = get_rsi(closes)

    vol_today = int(volumes[-1]) if volumes else 0
    vol_avg   = int(sum(volumes[-10:]) / min(10, len(volumes))) if volumes else 0
    vol_ratio = round(vol_today / vol_avg, 1) if vol_avg else 0

    # 均线趋势
    if ma5 and ma20:
        trend = "多头排列(看涨)" if ma5 > ma20 else "空头排列(看跌)"
    else:
        trend = "数据不足"

    # 期权链（最近到期）
    try:
        expirations = ticker.options
        next_exp = expirations[0] if expirations else "N/A"
        chain = ticker.option_chain(next_exp) if next_exp != "N/A" else None
        # 找ATM期权
        atm_call = atm_put = "N/A"
        if chain is not None:
            calls = chain.calls
            puts  = chain.puts
            # 最接近当前价格的行权价
            atm_strike = min(calls["strike"], key=lambda x: abs(x - price))
            call_row = calls[calls["strike"] == atm_strike]
            put_row  = puts[puts["strike"] == atm_strike]
            if not call_row.empty:
                iv = round(float(call_row["impliedVolatility"].iloc[0]) * 100, 1)
                atm_call = f"${atm_strike} Call IV:{iv}%"
            if not put_row.empty:
                iv = round(float(put_row["impliedVolatility"].iloc[0]) * 100, 1)
                atm_put = f"${atm_strike} Put IV:{iv}%"
    except Exception:
        next_exp = atm_call = atm_put = "获取失败"

    print(f"""
=== {symbol} ===
当前价格：${price}  ({'+' if change>=0 else ''}{change} / {'+' if pct>=0 else ''}{pct}%)
昨收：${prev}

技术指标：
  MA5：${ma5}  MA20：${ma20}  → {trend}
  RSI(14)：{rsi}  {'超买(>70)' if rsi and rsi>70 else '超卖(<30)' if rsi and rsi<30 else '中性'}
  成交量：{vol_today:,}（均量的 {vol_ratio}x）

期权（最近到期 {next_exp}）：
  ATM Call：{atm_call}
  ATM Put ：{atm_put}
""")

if __name__ == "__main__":
    symbols = sys.argv[1:] if len(sys.argv) > 1 else ["NVDA","AAPL","MSFT","GOOGL","AMZN","META","TSLA","MU"]
    print(f"获取时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
    for s in symbols:
        try:
            analyze(s)
        except Exception as e:
            print(f"{s}: 获取失败 - {e}")
