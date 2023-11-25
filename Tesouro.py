import pandas as pd

# bibliotecas para trabalhar offline com a biblioteca
import plotly.graph_objs as go 
from plotly.subplots import make_subplots

pd.options.display.float_format = '{:,.8f}'.format

from datetime import datetime
import urllib.request, json


class Tesouro:
  #####
  ## BUSCA TAXAS HISTORICAS DO TESOURO DIRETO NO TESOURO TRANSPARENTE
  def busca_taxas_tesouro_direto(self):
    url = 'https://www.tesourotransparente.gov.br/ckan/dataset/df56aa42-484a-4a59-8184-7676580c81e3/resource/796d2059-14e9-44e3-80c9-2d9e30b405c1/download/PrecoTaxaTesouroDireto.csv'
    df  = pd.read_csv(url, sep=';', decimal=',')
    df['Data Vencimento'] = pd.to_datetime(df['Data Vencimento'], dayfirst=True)
    df['Data Base']       = pd.to_datetime(df['Data Base'], dayfirst=True)
    multi_indice = pd.MultiIndex.from_frame(df.iloc[:, :3])
    df = df.set_index(multi_indice).iloc[: , 3:]
    return df


  #####
  ## BUSCA INDICES SELIC, DI e IPCA DO BCB 
  def busca_bcb_indices(self, indice="selic", data_inicial="03/01/2011", data_final="08/08/2023"):  
    if indice=='selic_anual':
      url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.1178/dados?formato=csv&dataInicial="+data_inicial+"&dataFinal="
    elif indice=='cdi':
      url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados?formato=csv&dataInicial="+data_inicial+"&dataFinal="
    elif indice=='ipca':
      url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.12061/dados?formato=csv&dataInicial="+data_inicial+"&dataFinal="
    else: #selic
      url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.11/dados?formato=csv&dataInicial="+data_inicial+"&dataFinal="
    
    df = pd.read_csv(url+data_final,sep=';', decimal=',')
    df['data'] = pd.to_datetime(df['data'], format="%d/%m/%Y")
    df = df.set_index('data')
    df['selic dia'] = round(pow((1+df['valor']/100), 1/252), 8)-1
    return df


  ######
  ## COMPARA PREFIXADOS NA CURVA VS MERCADO
  ##   Recebe dataframe com titulo ja selecionado
  ##   e datas de inicio e fim da analise
  def compara_prefixado_curva_mercado(self, dftit, tit_venc, inicio, fim):
    dftit = dftit[(dftit.index>=inicio)&(dftit.index<=fim)].copy()
    tx = dftit['Taxa Compra Manha'][0]

    df_compra = pd.DataFrame()
    df_compra['Data'] = dftit.index
    print('DU: '+str(len(df_compra)))

    df_mercado = df_compra.copy() 
    df_compra['Tx Compra'] = tx


    # Calcula rentabilidade acumulada Curva
    tx_dia = (pow(tx/100+1, 1/252)-1)*100
    df_compra['Tx Dia Prefix'] = tx_dia
    df_compra['Tx Dia Prefix Prep'] = tx_dia/100+1
    df_compra['LTN Curva'] = (df_compra['Tx Dia Prefix Prep'].cumprod()-1)*100


    # Calcula rentabilidade acumulada Mercado
    #  1) calcula o ganho percentual dia a dia (ganho percentual da PU atual em relação ao dia anterior; rentabilidade diária)
    #  2) vai acumulando as rentabilidades diárias para calcular a rentabilidade até cada dia
    dftit['PU Compra Manha Dia Anterior'] = dftit['PU Compra Manha'].shift(1)
    dftit['Rent'] = (dftit['PU Compra Manha']/dftit['PU Compra Manha Dia Anterior'] -1)*100

    df_mercado = dftit[['Taxa Compra Manha']]
    df_mercado['Tx Dia Prefix'] = dftit[['Rent']]
    df_mercado['Tx Dia Prefix Prep'] = df_mercado['Tx Dia Prefix']/100+1
    df_mercado['LTN Mercado'] = (df_mercado['Tx Dia Prefix Prep'].cumprod()-1)*100

    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(go.Scatter(x=df_compra['Data'], y=df_compra['Tx Compra'],
                            mode='lines', line={'dash': 'dash', 'color': 'blue'}, name=tit_venc+' Tx Compra'),
                            secondary_y=False)
    fig.add_trace(go.Scatter(x=df_mercado.index, y=df_mercado['Taxa Compra Manha'],
                            mode='lines', line={'dash': 'dash'}, name=tit_venc+' Tx Mercado'),
                            secondary_y=False)
    fig.add_trace(go.Scatter(x=df_compra['Data'], y=df_compra['LTN Curva'],
                            mode='lines', line={'color': 'blue'}, name=tit_venc+' Rentabilidade Curva'),
                            secondary_y=True)
    fig.add_trace(go.Scatter(x=df_mercado.index, y=df_mercado['LTN Mercado'],
                            mode='lines', line={'color': 'orangered'}, name=tit_venc+' Rentabilidade Mercado'),
                            secondary_y=True)
    fig.update_layout(
        title={'text': 'Taxas de LTNs', 'y':0.9, 'x':0.43, 'xanchor': 'center', 'yanchor': 'top'},
        width=1400,
        height=800)
    fig.show()


  ######
  ## COMPARA TITULOS SELIC NA CURVA VS MERCADO
  ##   Recebe dataframe com titulo ja selecionado
  ##   e datas de inicio e fim da analise
  def compara_selic_curva_mercado(self, dftit, tit_venc, inicio):
    
    # Coleta dados da Selic
    hoje = datetime.today().strftime('%d/%m/%Y')
    dfselic = self.busca_bcb_indices(indice="selic_anual", data_final=hoje)  
    
    dftit = dftit[dftit.index>=inicio].copy()
    df_compra = pd.DataFrame()
    df_compra['Data'] = dftit.index
    print('DU: '+str(len(df_compra)))

    df_mercado = df_compra.copy() 

    # Calcula rentabilidade acumulada Curva
    df_compra = dftit[['Taxa Compra Manha']]
    # Soma Selic ao longo do tempo, mas sempre com o spread da data da compra
    df_compra[['Taxa Compra Manha']] = df_compra['Taxa Compra Manha'][0]
    df_compra = df_compra.reset_index().merge(dfselic.reset_index(), left_on='Data Base', right_on='data')
    df_compra['Tx Compra'] = df_compra['valor'] + df_compra['Taxa Compra Manha']
    df_compra['Tx Dia'] = df_compra.apply(lambda x: ( pow( x['Tx Compra']/100+1, 1/252 )  - 1) * 100, axis=1)
    df_compra['Tx Dia Prep'] = df_compra['Tx Dia']/100+1
    df_compra['LFT Curva'] = (df_compra['Tx Dia Prep'].cumprod()-1)*100

    # Calcula rentabilidade acumulada Mercado
    #  1) calcula o ganho percentual dia a dia (ganho percentual da PU atual em relação ao dia anterior; rentabilidade diária)
    #  2) vai acumulando as rentabilidades diárias para calcular a rentabilidade até cada dia
    df_mercado = dftit[['Taxa Compra Manha']]
    df_mercado = df_mercado.reset_index().merge(dfselic.reset_index(), left_on='Data Base', right_on='data')
    df_mercado['Taxa Compra Total'] = df_mercado['Taxa Compra Manha'] + df_mercado['valor']
    df_mercado['Tx Dia'] = df_mercado.apply(lambda x: ( pow( x['Taxa Compra Total']/100+1, 1/252 )  - 1) * 100, axis=1)
    df_mercado['Tx Dia Prep'] = df_mercado['Tx Dia']/100+1
    df_mercado['LFT Mercado'] = (df_mercado['Tx Dia Prep'].cumprod()-1)*100

    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(go.Scatter(x=df_compra['Data Base'], y=df_compra['Taxa Compra Manha'],
                            mode='lines', line={'dash': 'dash', 'color': 'blue'}, name=tit_venc+' Tx Compra'),
                            secondary_y=False)
    fig.add_trace(go.Scatter(x=df_mercado['Data Base'], y=df_mercado['Taxa Compra Manha'],
                            mode='lines', line={'dash': 'dash'}, name=tit_venc+' Tx Mercado'),
                            secondary_y=False)
    fig.add_trace(go.Scatter(x=df_compra['Data Base'], y=df_compra['LFT Curva'],
                            mode='lines', line={'color': 'blue'}, name=tit_venc+' Rentabilidade Curva'),
                            secondary_y=True)
    fig.add_trace(go.Scatter(x=df_mercado['Data Base'], y=df_mercado['LFT Mercado'],
                            mode='lines', line={'color': 'orangered'}, name=tit_venc+' Rentabilidade Mercado'),
                            secondary_y=True)
    fig.update_layout(
        title={'text': 'Taxas de LFTs', 'y':0.9, 'x':0.43, 'xanchor': 'center', 'yanchor': 'top'},
        width=1400,
        height=800)
    fig.show()


  #####
  ## BUSCA COTACAO ATUAL DOS TITULOS SENDO VENDIDOS NO TESOURO DIRETO
  def busca_tesouro_cotacao_atual(self):
    with urllib.request.urlopen("https://www.tesourodireto.com.br/json/br/com/b3/tesourodireto/service/api/treasurybondsinfo.json") as url:
      data = json.load(url)
    lst = []
    titulos = data['response']['TrsrBdTradgList']
    for tit in titulos:
      #somente titulos em venda hoje, ou seja, com valor de investimento diferente de zero
      if (tit['TrsrBd']['untrInvstmtVal']!=0):
        name   = tit['TrsrBd']['nm']
        typ    = tit['TrsrBd']['FinIndxs']['nm']
        code   = tit['TrsrBdType']['nm']
        venc   = tit['TrsrBd']['mtrtyDt']
        rent   = tit['TrsrBd']['anulInvstmtRate']
        invest = tit['TrsrBd']['minInvstmtAmt']
        pu     = tit['TrsrBd']['untrInvstmtVal']
        tx_resgate = tit['TrsrBd']['anulRedRate']
        pu_resgate = tit['TrsrBd']['untrRedVal']
        min_resgate= tit['TrsrBd']['minRedVal']
        lst.append(pd.DataFrame([[name,typ,code,rent,invest,pu,venc,tx_resgate,pu_resgate]], columns=['Título','Tipo','Código','Rentabilidade Anual','Invest.Mínimo','Preço Unitário','Vencimento',
                                                                                                      'Taxa Resgate','Preço Regate']))
    
    df = pd.concat(lst, ignore_index=True)#.sort_values(by=['Titulo','Vencimento'])
    df['Vencimento'] = pd.to_datetime(df['Vencimento'])
    df['Código'] = pd.Categorical(df['Código'], ['LTN','NTN-F','LFT','NTNB PRINC','NTN-B','NTN-B1'])
    df = df.sort_values(by='Código').reset_index(drop=True)
    return df
