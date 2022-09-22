import requests as rq
from datetime import datetime
import dateutil
import yfinance as yf
import argparse
from typing import List, Optional
import dataclasses
import discord_webhook
from functools import partial

CAPITOL_TRADES_API = "https://bff.capitoltrades.com/trades"

@dataclasses.dataclass
class PolTrade:
    ticker: str
    asset_type: str
    tx_type: str

    pol_name: str
    party: str
    filing_url: str

    gap: int
    tx_date: str
    rep_date: str

    def is_stock(self) -> bool:
        return self.asset_type == "stock"

    def is_short(self) -> Optional[bool]:
        match self.tx_type:
            case "sell":
                return False
            case "buy":
                return False
            case _:
                return None
    
    def is_not_sus(self, out_m: int) -> bool:
        ndata = yf.Ticker(self.ticker.split(":")[0])
        history = ndata.history(period="3mo", interval="1d")

        if history.empty:
            return True
        
        if self.tx_date not in history.index:
            return True
        if self.rep_date not in history.index:
            return True

        tstdev = history["Close"].std()
        tmean = history["Close"].mean()

        bstd = history.loc[:self.tx_date]["Close"].std()
        bmax = history.loc[:self.tx_date]["Close"].max()
        bmin = history.loc[:self.tx_date]["Close"].min()
        bprice = history.loc[self.tx_date]["Close"]

        astd = history.loc[self.tx_date:self.rep_date]["Close"].std()
        amax = history.loc[self.tx_date:self.rep_date]["Close"].max()
        amin = history.loc[self.tx_date:self.rep_date]["Close"].min()
        aprice = history.loc[self.rep_date]["Close"]

        if bstd < astd or astd >= tstdev:
            return False
        
        if self.is_short and abs(tmean-amin) > out_m*tstdev:
            return False
        
        if (not self.is_short) and abs(tmean-amax) > out_m*tstdev:
            return False
        
        return True

    def capitalize_party(self) -> str:
        return self.party.capitalize()

    def __str__(self):
        return f"{self.tx_type.upper()} {self.ticker} -> {self.pol_name} ({self.capitalize_party()}) reported after {self.gap} days [{self.filing_url}]"


def do_fetch_data(start: datetime, end: datetime) -> List[PolTrade]:
    parsed_trades = []

    # Fetch data from API
    r = rq.get(CAPITOL_TRADES_API)
    recent_stock_data = r.json()["data"]

    for trade in recent_stock_data:
        pdate = datetime.strptime(trade["pubDate"], "%Y-%m-%dT%H:%M:%SZ").date()

        pol = trade["politician"]
        pol_full_name = f'{pol["firstName"]} {pol["lastName"]}'

        if pdate < start.date() or pdate >= end.date():
            continue

        parsed_trades.append(PolTrade(
            ticker=trade["asset"]["assetTicker"], 
            pol_name=pol_full_name, 
            asset_type=trade["asset"]["assetType"], 
            gap=trade["reportingGap"], 
            filing_url=trade["filingURL"],
            tx_type=trade["txType"], 
            party=trade["politician"]["party"],
            tx_date=trade["txDate"],
            rep_date=trade["filingDate"]))

    return parsed_trades

def report_print(trades: List[PolTrade]):
    for trade in trades:
        print(trade)

def report_discord(webhook_url: str, trades: List[PolTrade]):
    for trade in trades:
        webhook = discord_webhook.DiscordWebhook(url=webhook_url, rate_limit_retry=True)
        embed = discord_webhook.DiscordEmbed(title="New Trade!", description=str(trade), color=0x00ff00)
        webhook.add_embed(embed)
        webhook.execute()

def report_trades(trades: List[PolTrade], report_all: bool, webhook: Optional[str], outlier_m: int, max_gap: int):
    final_trades = trades
    reporter = partial(report_discord, webhook) if webhook else report_print

    if report_all:
        reporter(trades)
        return
    
    final_trades = [trade for trade in trades if trade.is_stock() and trade.gap <= max_gap and trade.is_not_sus(outlier_m)]

    reporter(final_trades)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="US Politician Trading Notifier")
    parser.add_argument("--start", nargs='?', default=datetime.today(), type=datetime.fromisoformat, help="Date to analyse trades from (ISO format)")
    parser.add_argument("--end", nargs='?', default=datetime.today(), type=datetime.fromisoformat, help="Date to analyse to (ISO format)")
    parser.add_argument("--outlier-multiplier", nargs='?', type=int, default=3, help="Definition of an outlier (for min/max). A multiplier of STDEV")
    parser.add_argument("--report-all",action='store_true', default=False, help="Report all trades regardless of possibility that major price action already occured")
    parser.add_argument("--webhook", nargs='?', type=str, help="Discord webhook URL for reports")
    parser.add_argument("--max-gap", nargs='?', type=int, default=50, help="Max allowed gap between trade and report date")
    args = parser.parse_args()

    trades = do_fetch_data(args.start, args.end)
    report_trades(trades, args.report_all, args.webhook, args.outlier_multiplier, args.max_gap)
