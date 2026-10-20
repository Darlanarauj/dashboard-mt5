"""
script_mt5.py
Lê o lucro flutuante do MetaTrader 5 e envia para o Firebase Realtime Database a cada 1s.

Requisitos:
  - Windows (a biblioteca oficial MetaTrader5 só funciona em Windows)
  - Terminal MetaTrader 5 aberto e logado
  - Ficheiro .env preenchido (veja .env.example)
"""

import os
import sys
import time
from datetime import datetime, timezone

import MetaTrader5 as mt5
import requests
from dotenv import load_dotenv

load_dotenv()

# ----------------------------------------------------------------------------
# Configuração (via .env)
# ----------------------------------------------------------------------------
FIREBASE_DB_URL = os.getenv("FIREBASE_DB_URL", "").rstrip("/")
FIREBASE_DB_SECRET = os.getenv("FIREBASE_DB_SECRET", "")  # opcional (ver README)
FIREBASE_PATH = os.getenv("FIREBASE_PATH", "monitor")

# Taxa de câmbio: se USD_BRL_FIXED for > 0 usa taxa fixa; senão usa a API.
USD_BRL_FIXED = float(os.getenv("USD_BRL_FIXED", "0") or 0)
FX_FALLBACK_RATE = float(os.getenv("FX_FALLBACK_RATE", "5.50"))
FX_REFRESH_SECONDS = int(os.getenv("FX_REFRESH_SECONDS", "60"))
FX_API_URL = "https://economia.awesomeapi.com.br/json/last/USD-BRL"

INTERVAL_SECONDS = float(os.getenv("INTERVAL_SECONDS", "1"))
HTTP_TIMEOUT = 5

session = requests.Session()


def log(msg: str) -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


# ----------------------------------------------------------------------------
# Câmbio USD -> BRL
# ----------------------------------------------------------------------------
class FxRate:
    def __init__(self) -> None:
        self.rate = USD_BRL_FIXED if USD_BRL_FIXED > 0 else FX_FALLBACK_RATE
        self.last_update = 0.0

    def get(self) -> float:
        if USD_BRL_FIXED > 0:
            return USD_BRL_FIXED
        if time.time() - self.last_update >= FX_REFRESH_SECONDS:
            self.last_update = time.time()  # evita martelar a API se falhar
            try:
                r = session.get(FX_API_URL, timeout=HTTP_TIMEOUT)
                r.raise_for_status()
                self.rate = float(r.json()["USDBRL"]["bid"])
                log(f"Cotação USD/BRL atualizada: {self.rate:.4f}")
            except Exception as exc:  # noqa: BLE001
                log(f"Falha ao obter cotação (usando {self.rate:.4f}): {exc}")
        return self.rate


# ----------------------------------------------------------------------------
# MetaTrader 5
# ----------------------------------------------------------------------------
def connect_mt5() -> None:
    while not mt5.initialize():
        log(f"Não foi possível conectar ao MT5: {mt5.last_error()}. A tentar de novo em 5s...")
        time.sleep(5)
    info = mt5.account_info()
    if info is not None:
        log(f"Conectado ao MT5 | Conta {info.login} | Moeda da conta: {info.currency}")
        if info.currency != "USD":
            log("AVISO: a moeda da conta não é USD. 'lucro_usd' refletirá a moeda da conta.")


def read_floating_profit() -> tuple[float, int]:
    """Devolve (lucro flutuante na moeda da conta, nº de posições abertas)."""
    positions = mt5.positions_get()
    if positions is None:
        raise RuntimeError(f"positions_get falhou: {mt5.last_error()}")
    profit = sum(p.profit + p.swap for p in positions)
    return float(profit), len(positions)


# ----------------------------------------------------------------------------
# Firebase Realtime Database (REST)
# ----------------------------------------------------------------------------
def send_to_firebase(payload: dict) -> None:
    url = f"{FIREBASE_DB_URL}/{FIREBASE_PATH}.json"
    params = {"auth": FIREBASE_DB_SECRET} if FIREBASE_DB_SECRET else None
    r = session.put(url, json=payload, params=params, timeout=HTTP_TIMEOUT)
    r.raise_for_status()


# ----------------------------------------------------------------------------
# Loop principal
# ----------------------------------------------------------------------------
def main() -> None:
    if not FIREBASE_DB_URL:
        sys.exit("Defina FIREBASE_DB_URL no ficheiro .env (veja .env.example).")

    fx = FxRate()
    connect_mt5()
    log("Monitorização iniciada. Ctrl+C para sair.")

    try:
        while True:
            started = time.time()
            try:
                lucro_usd, n_pos = read_floating_profit()
                lucro_brl = lucro_usd * fx.get()

                payload = {
                    "lucro_brl": round(lucro_brl, 2),
                    "lucro_usd": round(lucro_usd, 2),
                    "posicoes_abertas": n_pos,
                    "status": "GREEN" if lucro_brl >= 0 else "RED",
                    "timestamp": int(datetime.now(timezone.utc).timestamp() * 1000),
                }
                send_to_firebase(payload)
                log(f"{payload['status']} | R$ {payload['lucro_brl']:.2f} | "
                    f"US$ {payload['lucro_usd']:.2f} | {n_pos} pos.")

            except requests.RequestException as exc:
                log(f"Erro de rede ao enviar ao Firebase: {exc}")
            except RuntimeError as exc:
                log(f"Erro MT5: {exc}. A reconectar...")
                mt5.shutdown()
                connect_mt5()

            time.sleep(max(0.0, INTERVAL_SECONDS - (time.time() - started)))
    except KeyboardInterrupt:
        log("Encerrando...")
    finally:
        mt5.shutdown()


if __name__ == "__main__":
    main()
