# Stockbish
## What is Stockbish
Stockbish is a tiny program written in Python that looks at trades executed by members of th US Congress (pulled from a public database). This is possible due to mandatory disclosure laws.
The trades are than analysed in a very simple way (unusual standard deviation and outliers) to see if any major price action already happened. If nothing dramatic (seems) to have happened yet, it is reported as interesting.

If a webhook URL is provided, this can be reported to a discord channel. A quick systemd service and timer will allow one to get daily updates on trading activity.

## How does it work?

```
$ pipenv install
$ pipenv shell
$ python3 main.py --h
usage: main.py [-h] [--start [START]] [--end [END]] [--outlier-multiplier [OUTLIER_MULTIPLIER]] [--report-all] [--webhook [WEBHOOK]] [--max-gap [MAX_GAP]]

US Congress Trading Notifier

options:
  -h, --help            show this help message and exit
  --start [START]       Date to analyse trades from (ISO format)
  --end [END]           Date to analyse to (ISO format)
  --outlier-multiplier [OUTLIER_MULTIPLIER]
                        Definition of an outlier (for min/max). A multiplier of STDEV
  --report-all          Report all trades regardless of possibility that major price action already occured
  --webhook [WEBHOOK]   Discord webhook URL for reports
  --max-gap [MAX_GAP]   Max allowed gap between trade and report date
```

## Notice
Trade at your own risk. We - the developers - do not provide financial advice. The sources this app uses might provide inaccurate information. This app is for informational purposes only and might provide inaccurate information. **We do not take responsibility for any losses incurred.**