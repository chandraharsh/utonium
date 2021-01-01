import pandas as pd
from bs4 import BeautifulSoup
import requests


class STicker:

    def __init__(self, symbol):
        self.symbol = symbol
        self.core_url = 'https://www.screener.in'
        self.link = f"{self.core_url}/company/{self.symbol}/consolidated/"
        page = requests.get(self.link)
        self.__soup = BeautifulSoup(page.content, 'html.parser')
        self.__tables = pd.read_html(self.link)

    def get_screener_link(self):
        return self.link

    def get_company_description(self):
        return self.__soup.find_all('p')[0].string.strip()

    def get_company_name(self):
        return self.__soup.find_all('h1')[0].string.strip()

    def get_company_link(self):
        return self.__soup.find('div', attrs={
            "class": "company-links show-from-tablet-landscape"})\
            .find_all('a')[0].get('href')

    def get_bse_link(self):
        return self.__soup.find('div', attrs={
            "class": "company-links show-from-tablet-landscape"})\
            .find_all('a')[1].get('href')

    def get_nse_link(self):
        return self.__soup.find('div', attrs={
            "class": "company-links show-from-tablet-landscape"})\
            .find_all('a')[2].get('href')

    def get_industry_peer_comparison(self) -> pd.DataFrame:
        comparison_link = self.core_url + \
            self.__soup.find('section', id='peers').find_next(
                'a').find_next('a').get('href')
        peer_comparison = pd.read_html(comparison_link)
        peer_comparison = peer_comparison[0]
        peer_comparison.drop('S.No.', axis=1, inplace=True)
        if 15 in peer_comparison.index:
            peer_comparison.drop(index=15, inplace=True)
            peer_comparison.reset_index(drop=True, inplace=True)
        return peer_comparison

    def get_industry(self) -> str:
        return self.__soup.find('section', id='peers').find_next('a').\
            find_next('a').string.strip()

    def get_sector(self) -> str:
        return self.__soup.find('section', id='peers').\
            find_next('a').string.strip()

    def get_key_stats(self) -> dict:
        section = self.__soup.find('div', class_='company-ratios')
        company_ratios = section.find_next('ul').find_all('li')
        return {ratio.find('span', class_='name').string.strip():
                '/'.join([a.string for a in ratio.find_all(
                    'span', class_='number') if a.string is not None])
                for ratio in company_ratios}

    def get_pros_and_cons(self) -> dict:

        def get_list(class_) -> list:
            section = self.__soup.find('div', class_=class_)
            list = section.find_next('ul').find_all('li')
            try:
                return [l.string.strip() for l in list]
            except(Exception):
                return []

        pros = get_list('pros')
        cons = get_list('cons')
        return {'pros': pros, 'cons': cons}

    def get_quarterly_results(self) -> pd.DataFrame:
        table = self.__tables[0]
        return self.read_and_format_table(table[:-1])

    def get_profit_and_loss(self) -> pd.DataFrame:
        table = self.__tables[1]
        return self.read_and_format_table(table)

    def get_balance_sheet(self) -> pd.DataFrame:
        table = self.__tables[6]
        return self.read_and_format_table(table)

    def get_cash_flow(self) -> pd.DataFrame:
        table = self.__tables[7]
        return self.read_and_format_table(table)

    def get_ratios(self) -> pd.DataFrame:
        table = self.__tables[8]
        return self.read_and_format_table(table)

    def get_shareholder_pattern(self) -> pd.DataFrame:
        table = self.__tables[9]
        return self.read_and_format_table(table)

    def get_compounded_sales_growth(self) -> dict:
        table = self.__tables[2]
        return self.read_and_format_table_to_dict(table=table)

    def get_compounded_profit_growth(self) -> dict:
        table = self.__tables[3]
        return self.read_and_format_table_to_dict(table=table)

    def get_stock_price_cagr(self) -> dict:
        table = self.__tables[4]
        return self.read_and_format_table_to_dict(table=table)

    def get_return_on_equity(self) -> dict:
        table = self.__tables[5]
        return self.read_and_format_table_to_dict(table=table)

    def read_and_format_table(self, table: pd.DataFrame) -> pd.DataFrame:
        table.rename(columns={'Unnamed: 0': ''}, inplace=True)
        table[''] = table[''].str.replace('+', '')
        return table

    def read_and_format_table_to_dict(self, table: pd.DataFrame) -> dict:
        table = table.to_dict(orient='split')
        data = table['data']
        return {d[0][:-1]: d[1] for d in data}
