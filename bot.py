"""
GitHub Actions 로 하루 한 번 돌아가는 한국투자증권 모의투자 봇 (간단 버전)

- 서버가 필요 없습니다. GitHub 가 정해진 시각에 이 파일을 한 번 실행하고 끝냅니다.
- 기본은 "조회만" 합니다. 실제로 모의투자 주문을 넣으려면
  GitHub 저장소 Settings → Secrets and variables → Actions → Variables 에서
  ORDER_MODE 를 on 으로 만드세요.
- 전략을 바꾸고 싶으면 아래 "전략" 부분만 고치면 됩니다. (Claude 에게 부탁해도 됩니다)
"""

import os
import sys

import requests

BASE_URL = "https://openapivts.koreainvestment.com:29443"  # 모의투자 서버

APP_KEY = os.environ.get("KIS_APP_KEY", "")
APP_SECRET = os.environ.get("KIS_APP_SECRET", "")
ACCOUNT_NO = os.environ.get("KIS_ACCOUNT_NO", "").replace("-", "")
ORDER_MODE = os.environ.get("ORDER_MODE", "off").lower() == "on"

# ------------------------------------------------------------------ #
#  전략 (여기만 고치면 됩니다)
# ------------------------------------------------------------------ #

WATCHLIST = {
    "005930": "삼성전자",
    "000660": "SK하이닉스",
    "035420": "NAVER",
}
BUY_BELOW_MA = 0.97   # 현재가가 20일 평균의 97% 아래면 1주 매수
TAKE_PROFIT = 5.0     # 보유 종목 수익률이 +5% 이상이면 전량 매도


def decide(ticker, price, ma20, holding):
    """한 종목에 대해 'buy' / 'sell' / None 과 이유를 돌려줍니다."""
    if holding and holding["수익률"] >= TAKE_PROFIT:
        return "sell", f"수익률 {holding['수익률']:.1f}% ≥ {TAKE_PROFIT}%"
    if not holding and ma20 and price < ma20 * BUY_BELOW_MA:
        return "buy", f"현재가 {price:,} < 20일 평균 {ma20:,.0f}의 {BUY_BELOW_MA:.0%}"
    return None, ""


# ------------------------------------------------------------------ #
#  한국투자증권 API (건드리지 않아도 됩니다)
# ------------------------------------------------------------------ #

def get_token():
    r = requests.post(f"{BASE_URL}/oauth2/tokenP", timeout=15, json={
        "grant_type": "client_credentials", "appkey": APP_KEY, "appsecret": APP_SECRET,
    })
    r.raise_for_status()
    return r.json()["access_token"]


def headers(token, tr_id):
    return {"authorization": f"Bearer {token}", "appkey": APP_KEY,
            "appsecret": APP_SECRET, "tr_id": tr_id}


def get_price(token, ticker):
    r = requests.get(f"{BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-price", timeout=15,
                     headers=headers(token, "FHKST01010100"),
                     params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": ticker})
    r.raise_for_status()
    return int(r.json()["output"]["stck_prpr"])


def get_ma20(token, ticker):
    r = requests.get(f"{BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-daily-price", timeout=15,
                     headers=headers(token, "FHKST01010400"),
                     params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": ticker,
                             "FID_PERIOD_DIV_CODE": "D", "FID_ORG_ADJ_PRC": "0"})
    r.raise_for_status()
    closes = [int(d["stck_clpr"]) for d in r.json().get("output", [])[:20] if d.get("stck_clpr")]
    return sum(closes) / len(closes) if closes else 0


def get_holdings(token):
    r = requests.get(f"{BASE_URL}/uapi/domestic-stock/v1/trading/inquire-balance", timeout=15,
                     headers=headers(token, "VTTC8434R"),
                     params={"CANO": ACCOUNT_NO[:8], "ACNT_PRDT_CD": ACCOUNT_NO[8:],
                             "AFHR_FLPR_YN": "N", "OFL_YN": "", "INQR_DVSN": "02", "UNPR_DVSN": "01",
                             "FUND_STTL_ICLD_YN": "N", "FNCG_AMT_AUTO_RDPT_YN": "N", "PRCS_DVSN": "01",
                             "CTX_AREA_FK100": "", "CTX_AREA_NK100": ""})
    r.raise_for_status()
    data = r.json()
    holdings = {}
    for item in data.get("output1", []):
        qty = int(item.get("hldg_qty", 0))
        if qty > 0:
            holdings[item["pdno"]] = {"수량": qty, "수익률": float(item.get("evlu_pfls_rt", 0))}
    summary = (data.get("output2") or [{}])[0]
    return holdings, int(summary.get("dnca_tot_amt", 0))


def order(token, ticker, qty, side):
    tr_id = "VTTC0802U" if side == "buy" else "VTTC0801U"
    r = requests.post(f"{BASE_URL}/uapi/domestic-stock/v1/trading/order-cash", timeout=15,
                      headers=headers(token, tr_id),
                      json={"CANO": ACCOUNT_NO[:8], "ACNT_PRDT_CD": ACCOUNT_NO[8:], "PDNO": ticker,
                            "ORD_DVSN": "01", "ORD_QTY": str(qty), "ORD_UNPR": "0"})
    r.raise_for_status()
    return r.json().get("msg1", "")


# ------------------------------------------------------------------ #
#  실행
# ------------------------------------------------------------------ #

def main():
    if not (APP_KEY and APP_SECRET and ACCOUNT_NO):
        print("❌ Secrets 가 비어 있습니다. KIS_APP_KEY, KIS_APP_SECRET, KIS_ACCOUNT_NO 를 등록하세요.")
        sys.exit(1)

    print(f"모드: {'주문 실행 (모의투자)' if ORDER_MODE else '조회만 (주문 안 함)'}")
    token = get_token()
    holdings, cash = get_holdings(token)
    print(f"예수금: {cash:,}원 / 보유 종목: {len(holdings)}개\n")

    for ticker, name in WATCHLIST.items():
        price = get_price(token, ticker)
        ma20 = get_ma20(token, ticker)
        holding = holdings.get(ticker)
        action, reason = decide(ticker, price, ma20, holding)
        line = f"{name}({ticker}) 현재가 {price:,}원 · 20일 평균 {ma20:,.0f}원"
        if not action:
            print(f"  {line} → 대기")
            continue
        qty = 1 if action == "buy" else holding["수량"]
        label = "매수" if action == "buy" else "매도"
        if ORDER_MODE:
            print(f"  {line} → {label} {qty}주 주문: {order(token, ticker, qty, action)} ({reason})")
        else:
            print(f"  {line} → [조회 모드] {label} {qty}주 했을 것 ({reason})")


if __name__ == "__main__":
    main()
