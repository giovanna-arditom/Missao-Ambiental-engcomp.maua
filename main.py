
#IMPORT BIBLIOTECAS
import pandas as pd
import streamlit as st
import numpy 
import plotly.express as px
import math

#(Comando para rodar streamlit: python -m streamlit run main.py)


#CONFIGURANDO TELA INICIAL
st.set_page_config(page_title="Missão Ambiental", layout="wide") #setando a aba superior
st.title("Estação missão ambiental - Análise de dados") #título da página


#PUXANDO DADOS CSV
df = pd.read_csv('monitoramento_microclima_sintetico.csv', parse_dates=['timestamp']) #atribuindo minha ta

st.subheader("Primeiras linhas")
st.dataframe(df.head()) #visualização das primeiras 5 linhas

st.subheader("Informações gerais")
st.write(f'Linhas: {df.shape[0]} | Colunas: {df.shape[1]}') #verificando a quantidade de linhas e colunas do dataframe
st.write(df.dtypes) #verificando os tipode de daddos das colunas


#LIMPEZA DOS DADOS (NaN e Outliers)
st.subheader("Valores faltantes (NaN)")

nans = df.isna().sum() #conta quantos valores são NaN
st.dataframe(nans[nans > 0]) #mostra só as colunas que tam ao menos 1 valor faltando


#Aqui temos que tomar uma decisão do que fazer com esses valores
#No contexto atual, vamos preencher com a mediana
valor_mp25 = df["mp25_ugm3"].median() #calculo da mediana da coluna mp25_ugm3
valor_temp = df['temperatura_c'].mean() #calculo da média da coluna temperatura_c
valor_co2 = df['co2_ppm'].mean() #calculo da média da coluna co2_ppm
valor_so2 = df['so2_ppb'].median() #calculo da mediana da coluna so2_ppb

df['mp25_ugm3'] = df["mp25_ugm3"].fillna(valor_mp25) #preencher os valores da coluna mp25_ugm3 com a mediana
df['temperatura_c'] = df['temperatura_c'].fillna(valor_temp)
df['co2_ppm'] = df['co2_ppm'].fillna(valor_co2)
df['so2_ppb'] = df['so2_ppb'].fillna(valor_so2)

#EXIBIÇÃO DOS NaN PREENCHIDOS
valores_preenchidos = pd.DataFrame({
    'Coluna': ['mp25_ugm3', 'temperatura_c', 'co2_ppm', 'so2_ppb'],
    'metodo': ['mediana', 'média', 'média', 'mediana'],
    'Valor Preenchido': [valor_mp25, valor_temp, valor_co2, valor_so2]
})

st.subheader("Valores preenchidos dos NaNs")
st.dataframe(valores_preenchidos.round(2))

#tratamento de outliers
def detectar_outliers_iqr(coluna):
    q1 = df[coluna].quantile(0.25) #valoers abaixo dos 25% dos dados
    q3 = df[coluna].quantile(0.75) #valoers acima dos 25% dos dados
    iqr = q3 - q1
    limite_inf = q1 - 1.5 * iqr #abaixo disso o valor é considerado outlier para baixo
    limite_sup = q3 + 1.5 * iqr #acima disso o valor é considerado outlier para cima
    return df[(df[coluna] < limite_inf) | (df[coluna] > limite_sup)] #retorno da minha função no meio dos quartis


st.subheader("Outliers em MP2.5")
outliers = detectar_outliers_iqr('mp25_ugm3') #executando a função para a coluna mp25
st.dataframe(outliers[['timestamp', 'mp25_ugm3']]) #exibindo os valores de outliers em tabela



#REMOÇÃO DE OUTLIERS EM TODAS AS COLUNAS NUMÉRICAS  
indices_outliers = set()
colunas_numericas = ['temperatura_c', 'umidade_relativa_pct', 'pressao_hpa', 'velocidade_vento_ms','direcao_vento_graus','mp25_ugm3', 'mp10_ugm3',
                     'co_ppm', 'nox_ppb', 'so2_ppb', 'ch4_ppm'] #colunas utilizadas na correlação

#a coluna co2_ppm nao foi utilizada na correlação pois seus outliers estão relacionados com ciclos, fazendo com que esse número suba muito e não seja muito significativo. 
#Para entender mais, faça um histograma de co2 ao longo do dia


st.subheader('Outliers por coluna:')
for coluna in colunas_numericas:
    outliers_coluna = detectar_outliers_iqr(coluna)
    st.write(f'{coluna}: {len(outliers_coluna)} outliers')

for coluna in colunas_numericas:
    outliers_coluna = detectar_outliers_iqr(coluna)
    indices_outliers.update(outliers_coluna.index)

linhas_antes = df.shape[0]
df_original = df.copy() #criação de uma cópia do dataframe original antes da remoção dos outliers
df = df.drop(indices_outliers) #remocao unica de todas as linhas identificadas
linhas_depois = df.shape[0]

st.subheader('Remoção de outliers')
st.write(f'Linhas removidas por serem outliers em pelo menos uma coluna: {linhas_antes - linhas_depois}')


#ESTATÍSTICA DESCRITIVA
valores = df['temperatura_c'].dropna().tolist() #remove os valores vazios e tranforma nuqma lista

media_manual = sum(valores) / len(valores) #calculo manual da média

st.subheader("Valor da média de temperatura calculado na mão")
st.write(f'Valor da média calculado na mão: {media_manual:.2f}') #exibe o valor da média manual com 2 casas decimais

st.subheader('Valores estatísticos feitos no pandas')
st.dataframe(df.describe().round(2)) #exibo todas as variáveis estatísticas com 2 casas decimais 


#PADRÕES NO TEMPO
df['hora'] = df['timestamp'].dt.hour #pegando valor e hora e colocando na coluna nova
df['dia_util'] = df['timestamp'].dt.dayofweek < 5 #pegandoos dias da semana na coluna nova

st.subheader('Padrão por hora do dia (Mp2.5)')
media_hora = df.groupby('hora')['mp25_ugm3'].mean() #media dos valores mp25 por hora
st.bar_chart(media_hora)

st.subheader('Dia util x fim de semana (Mp2.5)')
media_tipo_dia = df.groupby('dia_util')['mp25_ugm3'].mean() #media dos valores mp25 por dia da semana e fim de semana
st.bar_chart(media_tipo_dia)


#CORRELAÇÃO
st.subheader('Correlação')


corr = df[colunas_numericas].corr() #correlação das colunas definidas anteriormente

fig = px.imshow(corr, text_auto='.2f', color_continuous_scale='RdBu_r', zmin=-1, zmax=1) #criação do gráfico de correlação
st.plotly_chart(fig, use_container_width='True') #exibição do gráfico de correlação