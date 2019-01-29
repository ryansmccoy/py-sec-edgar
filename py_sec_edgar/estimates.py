
import os
import pandas as pd
from datetime import datetime, timedelta

from settings import CONFIG

def export_estimates_from_yahoo(today_date=None):

    if today_date is None:
        today_date = datetime.today()

    yesterday_date = (today_date - timedelta(days=1)).strftime('%Y-%m-%d')
    weekend_date = (today_date + timedelta(days=4)).strftime('%Y-%m-%d')
    today_date = today_date.strftime('%Y-%m-%d')

    df_calendar = pd.read_html(f'https://finance.yahoo.com/calendar/earnings?from={yesterday_date}&to={weekend_date}&day={today_date}')

    df_all_est = []

    for ticker in df_calendar[0]['Symbol'].tolist():
        try:
            print(f'Downloading Estimates for {ticker}')

            df_est = pd.read_html(r'https://finance.yahoo.com/quote/{ticker}/analysis?p={ticker}')
            eps_est, rev_est = df_est[0], df_est[1]

            rev_est = rev_est.melt(id_vars=['Revenue Estimate'],var_name='Period')
            rev_est['Ticker'] = ticker
            rev_est['Item'] = "REVENUES"
            rev_est.rename(index=str, columns={"Revenue Estimate": "Statistic"}, inplace=True)
            rev_est['DateTime'] = str(datetime.utcnow())
            df_all_est.append(rev_est)

            eps_est = eps_est.melt(id_vars=['Earnings Estimate'],var_name='Period')
            eps_est['Ticker'] = ticker
            eps_est['Item'] = "EPS"
            eps_est.rename(index=str, columns={"Earnings Estimate": "Statistic"}, inplace=True)
            eps_est['DateTime'] = str(datetime.utcnow())
            df_all_est.append(eps_est)

            print(eps_est.append(rev_est).to_string())

        except Exception as e:
            print(f"Error Downloading {ticker} \n{e}\n")

    df_all_merged = pd.concat(df_all_est)
    df_all_merged = df_all_merged.reset_index(drop=True)
    df_all_merged = df_all_merged.T.reindex(['DateTime', 'Ticker', 'Item', 'Statistic', 'Period', 'value']).T

    df_all_merged.to_csv(os.path.join(CONFIG.DATA_DIR, r'{}_{}_estimates.csv'.format(datetime.now().strftime('%Y%m%dTZ%H%m%S'), datetime.today().strftime("%Y%m%d"))))
