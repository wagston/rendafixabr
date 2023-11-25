import pandas as pd
import requests
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

pd.options.display.float_format = '{:,.8f}'.format


#####
## BUSCA DI FUTURO DA BMF/B3
class BMF:
  def __init__(self, val_date):
    """
    Gera o objeto da bmf a partir de val_date em formato de datetime.date
    """
    self.val_date = val_date
    mes = self.val_date.month
    dia = self.val_date.day
    if self.val_date.month<10: mes='0'+str(self.val_date.month)
    if self.val_date.day<10: dia = '0'+str(self.val_date.day)
    self.dt_barra = f'{dia}/{mes}/{val_date.year}'
    self.dt_corrida = f'{val_date.year}{mes}{dia}'
    self.headers = {"User-Agent":'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36'}

  def _baixa_cupom(self):
    """
    Dada a val_date baixa a curva de cupom limpo
    """
    link = f'https://www2.bmf.com.br/pages/portal/bmfbovespa/boletim1/TxRef1.asp?Data={self.dt_barra}&Data1={self.dt_corrida}&slcTaxa=DOC'
    page = requests.get(link, headers=self.headers, verify=False)
    soup = BeautifulSoup(page.content, 'html.parser')
    texto = soup.find_all('td')
    dias, taxas = [], []
    tabelas = ["['tabelaConteudo1']", "['tabelaConteudo2']"]
    for i in range(len(texto)):
        try:
            if str(texto[i]['class']) in tabelas:
                tratado = texto[i].text.replace('\r\n','').replace(',','.').replace(' ','')
                if i==0 or i%2==0:
                    dias.append(int(tratado))
                else:
                    taxas.append(float(tratado)/100)
        except:
            pass
    return pd.DataFrame(data=taxas, index=dias, columns={'taxas360'})

  def _baixa_pre(self):
    """
    Dada a val_date baixa a curva pré-di
    """
    link = f'https://www2.bmf.com.br/pages/portal/bmfbovespa/boletim1/TxRef1.asp?Data={self.dt_barra}&Data1={self.dt_corrida}&slcTaxa=PRE'
    page = requests.get(link, headers=self.headers, verify=False)
    soup = BeautifulSoup(page.content, 'html.parser')
    texto = soup.find_all('td')
    dias, taxas252, taxas360 = [], [], []
    tabelas = ["['tabelaConteudo1']", "['tabelaConteudo2']"]
    for i in range(0,len(texto),3):
        try:
            if str(texto[i]['class']) in tabelas:
                if i<=len(texto)-2:
                    dias.append(int(texto[i].text.replace('\r\n','').replace(',','.').replace(' ','')))
                    taxas252.append(float(texto[i+1].text.replace('\r\n','').replace(',','.').replace(' ',''))/100)
                    taxas360.append(float(texto[i+2].text.replace('\r\n','').replace(',','.').replace(' ',''))/100)
        except:
            pass
    return pd.DataFrame({'taxas252':taxas252,'taxas360':taxas360}, index=dias)

  def getdifuturo(self, date_str):
    df_fut = self._baixa_pre()
    df_fut['taxas252'] = df_fut['taxas252']*100
    df_fut = df_fut.reset_index()
    df_fut['data'] = date_str
    df_fut['data'] = pd.to_datetime(df_fut['data'])
    df_fut['time_added'] = pd.to_timedelta(df_fut['index'],'d')
    df_fut['data'] = df_fut['data']+ df_fut['time_added']
    return df_fut
  