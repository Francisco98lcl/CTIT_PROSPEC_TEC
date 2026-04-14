# -*- coding: utf-8 -*-
"""
Created on Fri Apr 10 16:00:55 2026

@author: popch
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from sklearn.feature_extraction.text import CountVectorizer
from wordcloud import WordCloud
import pycountry
import re


st.set_page_config(layout="wide")

# =====================================================
# SESSION STATE
# =====================================================

if "taxonomy" not in st.session_state:
    st.session_state.taxonomy = None
    
# =====================================================
# FUNÇÕES DE EQUAÇÃO DE PALAVRAS
# =====================================================

country_map_iso = {
    "CN": "China",
    "US": "United States",
    "BR": "Brazil",
    "DE": "Germany",
    "FR": "France",
    "JP": "Japan",
    "KR": "South Korea",
    "GB": "United Kingdom",
    "IN": "India",
    "IT": "Italy",
    "CA": "Canada",
    "ES": "Spain",
    "AU": "Australia",
    "RU": "Russia",
    "EP": "European Patent Office",
    "WO": "WIPO",
    "EA": "Eurasian Patent Organization",
    "AP": "African Regional Intellectual Property Organization"
    
}

def iso_to_country(code):
    try:
        return pycountry.countries.get(alpha_2=code).name
    except:
        return "Unknown"

def safe_iso(code):
    if pd.isna(code):
        return "Unknown"
    
    code = str(code).strip().upper()
    
    # casos especiais
    if code in country_map_iso:
        return country_map_iso[code]
    
    try:
        country = pycountry.countries.get(alpha_2=code)
        if country:
            return country.name
    except:
        pass
    
    return "Unknown"

#df_pat["Country"] = df_pat["jurisdiction"].apply(iso_to_country)

country_map = {
    # Estados Unidos
    "USA": "United States",
    "U.S.A.": "United States",
    "United States of America": "United States",
    
    # Brasil
    "Brasil": "Brazil",
    
    # Reino Unido
    "UK": "United Kingdom",
    "England": "United Kingdom",
    "Scotland": "United Kingdom",
    
    # China
    "PR China": "China",
    "People's Republic of China": "China",
    
    # Coreias
    "South Korea": "Korea, South",
    "Republic of Korea": "Korea, South",
    
    # Outros exemplos comuns
    "Russia": "Russian Federation",
    "Iran": "Iran, Islamic Republic of",
}

def normalize_country(name):
    if not name:
        return "Unknown"
    
    name = name.strip()
    
    # Primeiro tenta no dicionário
    if name in country_map:
        return country_map[name]
    
    # Depois tenta pycountry
    try:
        country = pycountry.countries.search_fuzzy(name)[0]
        return country.name
    except:
        return name

def extract_first_author_country(affiliation):
    if not affiliation:
        return "Unknown"
    
    # 1. pegar primeira afiliação
    first_aff = affiliation.split(";")[0]
    
    # 2. separar por vírgula
    parts = first_aff.split(",")
    
    # 3. pegar último elemento (país)
    if len(parts) > 1:
        country_raw = parts[-1].strip()
    else:
        return "Unknown"
    
    # 4. normalizar
    return normalize_country(country_raw)

def build_block(words):
    return "(" + " OR ".join([f'"{w}"' for w in words]) + ")"

def generate_query(taxonomy):
    blocks = []
    for key in taxonomy:
        if taxonomy[key]:
            blocks.append(build_block(taxonomy[key]))
    return "TITLE-ABS-KEY(\n\n" + "\n\nAND\n\n".join(blocks) + "\n\n)"


# =====================================================
# UI
# =====================================================
st.title("📊 Prospecção tecnológica")

# =====================================================
# ABAS
# =====================================================

tab1, tab2, tab3 =st.tabs(["Equação de Busca", "Bibliometria", "Patenteometria"])

# =====================================================
# ABA 1 - EQUAÇÃO DE BUSCA
# =====================================================


with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        st.header("Gerador automático de equação Scopus")
    with col2:
        st.subheader('Descreva a sua taxonomia de pesquisa preenchendo os slots de categoria. Os slots devem ser preenchidos em inglês')
    st.markdown('''Como utilizar a taxonomia para prospecção tecnológica:
                    A estrutura **Ação** → **Objeto** → **Contexto** → **Fenômeno** → **Indicador** → **Material** foi desenvolvida para organizar de forma lógica e estratégica os termos de busca, permitindo construir consultas mais precisas e alinhadas com o objetivo da análise tecnológica.
                    Essa abordagem ajuda a transformar uma ideia ampla em uma equação de busca estruturada, aumentando a relevância dos resultados tanto em bases científicas quanto em bancos de patentes.''')
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('**Ação**: Representa o que está sendo feito (processo ou intervenção.')
        st.markdown(' **Objeto**: Elemento principal sobre o qual a ação ocorre.')
    with col2:
        st.markdown('**Contexto**: Ambiente ou aplicação onde o objeto está inserido.')
        st.markdown('**Fenômeno**: Problema ou mecanismo que motiva o estudo.')
    with col3:
        st.markdown('**Indicador**: Variáveis que permitem avaliar desempenho ou comportamento.')
        st.markdown('**Material**: Substâncias ou tecnologias utilizadas na solução.')
    
    default_tax = st.session_state.taxonomy if st.session_state.taxonomy else {
        "Ação": ["application","coating","repair"],
        "Objeto": ["pipeline","tank","structure"],
        "Contexto": ["offshore","industrial"],
        "Fenômeno": ["corrosion","rust"],
        "Indicador": ["adhesive","coating"],
        "Materiais": ["epoxy","polyurethane"]
    }

    taxonomy_input = {}
    
    st.subheader("Definição da Taxonomia")
    
    left_keys = ["Ação", "Objeto"]
    center_keys = ["Contexto", "Fenômeno"]
    right_keys = ["Indicador", "Materiais"]
    
    col1, col2, col3 = st.columns(3)
        
    with col1:
        for k in left_keys:
            taxonomy_input[k] = st.text_area(
                k,
                ",".join(default_tax[k])
            )
            
    with col2:
        for k in center_keys:
            taxonomy_input[k] = st.text_area(
                k,
                ",".join(default_tax[k])
            )
            
    with col3:
        for k in right_keys:
            taxonomy_input[k] = st.text_area(
                k,
                ",".join(default_tax[k])
            )
                
    taxonomy = {
        k: [t.strip().lower() for t in v.split(",") if t.strip()]
        for k, v in taxonomy_input.items()
    }

    col1, col2 = st.columns(2)

    if col1.button("💾 Salvar taxonomia"):
        st.session_state.taxonomy = taxonomy
        st.success("Taxonomia salva!")

    if col2.button("🚀 Gerar equação"):
        query = generate_query(taxonomy)
        st.subheader("📄 Equação Scopus:")
        st.code(query)
        st.download_button("📥 Baixar", query, "query.txt")


# =====================================================
# ABA 2 - BIBLIOMETRIA
# =====================================================
with tab2:
    
    if st.session_state.taxonomy is None:
        st.warning("Defina a taxonomia na aba 'Gerar Equação' primeiro.")
        st.stop()
        
    taxonomy = st.session_state.taxonomy
    
    # =====================================================
    # SIDEBAR
    # =====================================================

    st.sidebar.header("Categorias")

    selected_groups = st.sidebar.multiselect(
        "Categorias",
        list(taxonomy.keys()),
        default=list(taxonomy.keys())
    )

    custom_tax = {}

    for g in selected_groups:
        txt = st.sidebar.text_area(g, ",".join(taxonomy[g]), key=f"sidebar_{g}")
        custom_tax[g] = [t.strip().lower() for t in txt.split(",") if t.strip()]

    # garantir categorias não selecionadas vazias
    for g in taxonomy.keys():
        if g not in custom_tax:
            custom_tax[g] = []
    
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader('Exporte o arquivo scopus com as informações de "Citation Information", "Bibliographical information" e "Abstract & keywords"')
        
    with col2:
        # =====================================================
        # UPLOAD
        # =====================================================
    
        file = st.file_uploader("Upload CSV", type=["csv"])
    
    if file:
    
        df = pd.read_csv(file)
        df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    
        text_columns = ["Title","Abstract","Author Keywords","Index Keywords"]
        df["text"] = df[text_columns].fillna("").agg(" ".join, axis=1).str.lower()
    
        # =====================================================
        # FILTRO DE ANO
        # =====================================================
    
        year_range = st.sidebar.slider(
            "Year range",
            int(df["Year"].min()),
            int(df["Year"].max()),
            (2000, 2025)
        )
    
        df = df[(df["Year"] >= year_range[0]) & (df["Year"] <= year_range[1])]
    
        # =====================================================
        # TERMOS
        # =====================================================
    
        all_terms = list(set(sum(custom_tax.values(), [])))
    
        if len(all_terms) == 0:
            st.warning("Insira termos de pesquisa na barra lateral")
            st.stop()
    
        # =====================================================
        # MATRIZ
        # =====================================================
    
        vectorizer = CountVectorizer(vocabulary=all_terms, binary=True)
        X = vectorizer.fit_transform(df["text"])
    
        term_df = pd.DataFrame(X.toarray(), columns=vectorizer.get_feature_names_out())
        term_df = term_df.astype(int)
    
        # =====================================================
        # WORD CLOUDS
        # =====================================================
    
        st.subheader("Nuvem de palavras geral")
    
        wc_all = WordCloud(width=1000, height=400, background_color="white") \
            .generate(" ".join(df["text"]))
    
        fig1, ax1 = plt.subplots()
        ax1.imshow(wc_all)
        ax1.axis("off")
        st.pyplot(fig1)
    
        st.subheader("Nuvem de palavras - Considerando a taxonomia proposta")
    
        taxonomy_freq = term_df.sum().to_dict()
    
        wc_tax = WordCloud(width=1000, height=400, background_color="white") \
            .generate_from_frequencies(taxonomy_freq)
    
        fig2, ax2 = plt.subplots()
        ax2.imshow(wc_tax)
        ax2.axis("off")
        st.pyplot(fig2)
    
        # =====================================================
        # PUBLICAÇÕES
        # =====================================================
    
        st.subheader("Evolução das publicações ao longo dos anos")
    
        year_counts = df["Year"].value_counts().sort_index()
        cumulative = year_counts.cumsum()
        
        col1, col2 = st.columns(2)
        with col1:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=year_counts.index, y=year_counts.values, name="Yearly"))
            fig.update_layout(title="Distribuição anual das produções científicas")
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=cumulative.index, y=cumulative.values, name="Cumulative"))
            fig.update_layout(title="Evolução cronológica acumulada das produções científicas")
            st.plotly_chart(fig, use_container_width=True)
        # =====================================================
        # 📈 TERM EVOLUTION (CUMULATIVE)
        # =====================================================
        
        st.subheader("Evolução das pesquisas acerca das taxonomias propostas")
        
        col1, col2 = st.columns(2)
        with col1:
            term_year_df = term_df.copy()
            term_year_df["Year"] = df["Year"].values
            yearly_terms = term_year_df.groupby("Year").sum().sort_index()
            yearly_cum = yearly_terms.cumsum()
            # top 10 termos mais frequentes
            top_terms = term_df.sum().sort_values(ascending=False).head(10).index
            fig = go.Figure()  
            for term in custom_tax["Ação"]:
                fig.add_trace(go.Scatter(
                    x=yearly_cum.index,
                    y=yearly_cum[term],
                    mode="lines",
                    name=term
                ))
            fig.update_layout(title="Evolução das Pesquisas - Verbos de Ação")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            term_year_df = term_df.copy()
            term_year_df["Year"] = df["Year"].values         
            yearly_terms = term_year_df.groupby("Year").sum().sort_index()
            yearly_cum = yearly_terms.cumsum()  
            # top 10 termos mais frequentes
            top_terms = term_df.sum().sort_values(ascending=False).head(10).index    
            fig = go.Figure()     
            for term in custom_tax["Contexto"]:
                fig.add_trace(go.Scatter(
                    x=yearly_cum.index,
                    y=yearly_cum[term],
                    mode="lines",
                    name=term
                ))
            fig.update_layout(title="Evolução das Pesquisas - Contexto")    
            st.plotly_chart(fig, use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            term_year_df = term_df.copy()
            term_year_df["Year"] = df["Year"].values
            yearly_terms = term_year_df.groupby("Year").sum().sort_index()
            yearly_cum = yearly_terms.cumsum()
            # top 10 termos mais frequentes
            top_terms = term_df.sum().sort_values(ascending=False).head(10).index
            fig = go.Figure()  
            for term in custom_tax["Objeto"]:
                fig.add_trace(go.Scatter(
                    x=yearly_cum.index,
                    y=yearly_cum[term],
                    mode="lines",
                    name=term
                ))
            fig.update_layout(title="Evolução das Pesquisas - Objeto")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            term_year_df = term_df.copy()
            term_year_df["Year"] = df["Year"].values         
            yearly_terms = term_year_df.groupby("Year").sum().sort_index()
            yearly_cum = yearly_terms.cumsum()  
            # top 10 termos mais frequentes
            top_terms = term_df.sum().sort_values(ascending=False).head(10).index    
            fig = go.Figure()     
            for term in custom_tax["Fenômeno"]:
                fig.add_trace(go.Scatter(
                    x=yearly_cum.index,
                    y=yearly_cum[term],
                    mode="lines",
                    name=term
                ))
            fig.update_layout(title="Evolução das Pesquisas - Fenômeno")    
            st.plotly_chart(fig, use_container_width=True)
            
        col1, col2 = st.columns(2)
        with col1:
            term_year_df = term_df.copy()
            term_year_df["Year"] = df["Year"].values
            yearly_terms = term_year_df.groupby("Year").sum().sort_index()
            yearly_cum = yearly_terms.cumsum()
            # top 10 termos mais frequentes
            top_terms = term_df.sum().sort_values(ascending=False).head(10).index
            fig = go.Figure()  
            for term in custom_tax["Indicador"]:
                fig.add_trace(go.Scatter(
                    x=yearly_cum.index,
                    y=yearly_cum[term],
                    mode="lines",
                    name=term
                ))
            fig.update_layout(title="Evolução das Pesquisas - Indicador")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            term_year_df = term_df.copy()
            term_year_df["Year"] = df["Year"].values         
            yearly_terms = term_year_df.groupby("Year").sum().sort_index()
            yearly_cum = yearly_terms.cumsum()  
            # top 10 termos mais frequentes
            top_terms = term_df.sum().sort_values(ascending=False).head(10).index    
            fig = go.Figure()     
            for term in custom_tax["Materiais"]:
                fig.add_trace(go.Scatter(
                    x=yearly_cum.index,
                    y=yearly_cum[term],
                    mode="lines",
                    name=term
                ))
            fig.update_layout(title="Evolução das Pesquisas - Materiais")    
            st.plotly_chart(fig, use_container_width=True)
        
        
    
        # =====================================================
        # PAÍSES
        # =====================================================
    
        #countries = []
        df["Country"] = df["Affiliations"].fillna("").apply(extract_first_author_country)
        # Ranking geral
        country_counts = df["Country"].value_counts()
        # Top 10
        top10 = country_counts.head(10)
        # Posição do Brasil
        if "Brazil" in country_counts.index:
            brasil_rank = country_counts.index.get_loc("Brazil") + 1
            brasil_label = f"Brazil ({brasil_rank}º)"
            brasil_value = country_counts["Brazil"]
        else:
            brasil_rank = None
            brasil_label = None
            brasil_value = None
                
                
    
        # =====================================================
        # CUMULATIVO POR PAÍS
        # =====================================================
        st.subheader("Análise de produções científicas por países")
        col1, col2 = st.columns(2)
        with col1:
            #st.subheader("Produção Científica acumulada por país")
            country_year = df.groupby(["Country","Year"]).size().reset_index(name="Count")
            fig = go.Figure()
            # Lista de países: Top 10 + Brasil (se não estiver no top 10)
            selected_countries = list(top10.index)
            
            if "Brazil" in country_counts.index and "Brazil" not in selected_countries:
                selected_countries.append("Brazil")
            
            for c in selected_countries:
                data = country_year[country_year["Country"] == c].sort_values("Year")
            
                name = c
                if c == "Brazil" and brasil_rank:
                    name = brasil_label
            
                fig.add_trace(go.Scatter(
                    x=data["Year"],
                    y=data["Count"].cumsum(),
                    name=name
                ))
            fig.update_layout(title="Produção Científica acumulada por país")  
            st.plotly_chart(fig, use_container_width=True)
            
            
            
        with col2:
            #st.subheader("Países com mais produções Científicas")
            bar_data = top10.copy()

            if "Brazil" in country_counts.index and "Brazil" not in bar_data.index:
                bar_data[brasil_label] = brasil_value
            elif "Brazil" in bar_data.index:
                # substitui nome para incluir posição
                bar_data.rename(index={"Brazil": brasil_label}, inplace=True)
        
            # Converter para dataframe
            bar_df = bar_data.reset_index()
            bar_df.columns = ["Country", "Count"]
            
            fig_bar = go.Figure(go.Bar(
                x=bar_df["Count"],
                y=bar_df["Country"],
                orientation='h'
            ))
            
            fig_bar.update_layout(
                yaxis=dict(autorange="reversed")  # maior no topo
            )
            fig_bar.update_layout(title="Países com mais produções Científicas")
            st.plotly_chart(fig_bar, use_container_width=True)
            
        
        # =====================================================
        # 🌍 MOST USED TERMS BY COUNTRY - parei aqui
        # =====================================================
        
        st.subheader("Termo dominante por País")
        
        term_df_country = term_df.copy()
        term_df_country["Country"] = df["Country"].values
        
        col1, col2 = st.columns(2)
        #-----Ação-----------
        with col1:
            selected_terms = custom_tax["Ação"]
            # manter apenas termos existentes no dataframe
            selected_terms = [t for t in selected_terms if t in term_df_country.columns]
            grouped = term_df_country.groupby("Country")[selected_terms].sum()
            country_term_data = []
            for country, row in grouped.iterrows():
                # ignorar países sem dados
                if row.sum() == 0:
                    continue
            
                dominant_term = row.idxmax()
                dominant_value = row.max()
                country_term_data.append({
                    "Country": country,
                    "Term": dominant_term,
                    "Value": dominant_value
                })
            # =========================
            # DATAFRAME FINAL
            # =========================
            map_df = pd.DataFrame(country_term_data)
            # segurança extra
            if map_df.empty:
                st.warning("Sem dados suficientes para gerar o mapa.")
            else:
                # =========================
                # MAPA
                # =========================            
                fig = px.choropleth(
                    map_df,
                    locations="Country",
                    locationmode="country names",
                    color="Term",
                    hover_data=["Value"],
                    title="Termo dominante por país - Verbo de Ação"
                )
                st.plotly_chart(fig, use_container_width=True)
            
        #-----Contexto-----------
        with col2:
            selected_terms = custom_tax["Contexto"]
            # manter apenas termos existentes no dataframe
            selected_terms = [t for t in selected_terms if t in term_df_country.columns]
            grouped = term_df_country.groupby("Country")[selected_terms].sum()
            country_term_data = []
            for country, row in grouped.iterrows():
                # ignorar países sem dados
                if row.sum() == 0:
                    continue
            
                dominant_term = row.idxmax()
                dominant_value = row.max()
                country_term_data.append({
                    "Country": country,
                    "Term": dominant_term,
                    "Value": dominant_value
                })
            # =========================
            # DATAFRAME FINAL
            # =========================
            map_df = pd.DataFrame(country_term_data)
            # segurança extra
            if map_df.empty:
                st.warning("Sem dados suficientes para gerar o mapa.")
            else:
                # =========================
                # MAPA
                # =========================    
                fig = px.choropleth(
                    map_df,
                    locations="Country",
                    locationmode="country names",
                    color="Term",
                    hover_data=["Value"],
                    title="Termo dominante por país - Contexto"
                )
                st.plotly_chart(fig, use_container_width=True)
            
        
        col1, col2 = st.columns(2)
        #-----Objeto-----------
        with col1:
            selected_terms = custom_tax["Objeto"]
            # manter apenas termos existentes no dataframe
            selected_terms = [t for t in selected_terms if t in term_df_country.columns]
            grouped = term_df_country.groupby("Country")[selected_terms].sum()
            country_term_data = []
            for country, row in grouped.iterrows():
                # ignorar países sem dados
                if row.sum() == 0:
                    continue
            
                dominant_term = row.idxmax()
                dominant_value = row.max()
                country_term_data.append({
                    "Country": country,
                    "Term": dominant_term,
                    "Value": dominant_value
                })
            # =========================
            # DATAFRAME FINAL
            # =========================
            map_df = pd.DataFrame(country_term_data)
            # segurança extra
            if map_df.empty:
                st.warning("Sem dados suficientes para gerar o mapa.")
            else:
                # =========================
                # MAPA
                # =========================    
                fig = px.choropleth(
                    map_df,
                    locations="Country",
                    locationmode="country names",
                    color="Term",
                    hover_data=["Value"],
                    title="Termo dominante por país - Objeto"
                )
                st.plotly_chart(fig, use_container_width=True)
                
        #-----Fenômeno-----------     
        with col2:
            selected_terms = custom_tax["Fenômeno"]
            # manter apenas termos existentes no dataframe
            selected_terms = [t for t in selected_terms if t in term_df_country.columns]
            grouped = term_df_country.groupby("Country")[selected_terms].sum()
            country_term_data = []
            for country, row in grouped.iterrows():
                # ignorar países sem dados
                if row.sum() == 0:
                    continue
            
                dominant_term = row.idxmax()
                dominant_value = row.max()
                country_term_data.append({
                    "Country": country,
                    "Term": dominant_term,
                    "Value": dominant_value
                })
            # =========================
            # DATAFRAME FINAL
            # =========================
            map_df = pd.DataFrame(country_term_data)
            # segurança extra
            if map_df.empty:
                st.warning("Sem dados suficientes para gerar o mapa.")
            else:
                # =========================
                # MAPA
                # =========================    
                fig = px.choropleth(
                    map_df,
                    locations="Country",
                    locationmode="country names",
                    color="Term",
                    hover_data=["Value"],
                    title="Termo dominante por país - Fenômeno"
                )
                st.plotly_chart(fig, use_container_width=True)
                
        col1, col2 = st.columns(2)
        #-----Indicador-----------
        with col1:
            selected_terms = custom_tax["Indicador"]
            # manter apenas termos existentes no dataframe
            selected_terms = [t for t in selected_terms if t in term_df_country.columns]
            grouped = term_df_country.groupby("Country")[selected_terms].sum()
            country_term_data = []
            for country, row in grouped.iterrows():
                # ignorar países sem dados
                if row.sum() == 0:
                    continue
            
                dominant_term = row.idxmax()
                dominant_value = row.max()
                country_term_data.append({
                    "Country": country,
                    "Term": dominant_term,
                    "Value": dominant_value
                })
            # =========================
            # DATAFRAME FINAL
            # =========================
            map_df = pd.DataFrame(country_term_data)
            # segurança extra
            if map_df.empty:
                st.warning("Sem dados suficientes para gerar o mapa.")
            else:
                # =========================
                # MAPA
                # =========================    
                fig = px.choropleth(
                    map_df,
                    locations="Country",
                    locationmode="country names",
                    color="Term",
                    hover_data=["Value"],
                    title="Termo dominante por país - Indicador"
                )
                st.plotly_chart(fig, use_container_width=True)
                
        #-----Materiais-----------
        with col2:
            selected_terms = custom_tax["Materiais"]
            # manter apenas termos existentes no dataframe
            selected_terms = [t for t in selected_terms if t in term_df_country.columns]
            grouped = term_df_country.groupby("Country")[selected_terms].sum()
            country_term_data = []
            for country, row in grouped.iterrows():
                # ignorar países sem dados
                if row.sum() == 0:
                    continue
            
                dominant_term = row.idxmax()
                dominant_value = row.max()
                country_term_data.append({
                    "Country": country,
                    "Term": dominant_term,
                    "Value": dominant_value
                })
            # =========================
            # DATAFRAME FINAL
            # =========================
            map_df = pd.DataFrame(country_term_data)
            # segurança extra
            if map_df.empty:
                st.warning("Sem dados suficientes para gerar o mapa.")
            else:
                # =========================
                # MAPA
                # =========================
            
                fig = px.choropleth(
                    map_df,
                    locations="Country",
                    locationmode="country names",
                    color="Term",
                    hover_data=["Value"],
                    title="Termo dominante por país - Materiais"
                )
                st.plotly_chart(fig, use_container_width=True)
             
        #if:           
            #grouped = term_df_country.groupby("Country").sum()
            #country_term_data = []
            #for country, row in grouped.iterrows():
            #    if row.sum() == 0:
            #        continue
            #    dominant_term = row.idxmax()
            #    dominant_value = row.max()
            #    country_term_data.append({
            #        "Country": country,
            ##        "Term": dominant_term,
            #        "Value": dominant_value
            #    })
            #        
            #map_df = pd.DataFrame(country_term_data)
            #
            #fig = px.choropleth(
            #    map_df,
            #    locations="Country",
            #    locationmode="country names",
            #    color="Term",
            #    hover_data=["Value"]
            #)
            #st.plotly_chart(fig, use_container_width=True)
    
        # ordenar por volume total
        #grouped["Total"] = grouped.sum(axis=1)
        #grouped = grouped.sort_values("Total", ascending=False).drop(columns="Total")
        #st.subheader("📊 Matriz País × Termos")
        #st.dataframe(grouped)
        

        # =====================================================
        # FLOW (AGORA FILTRADO CORRETAMENTE)
        # =====================================================
    
        st.subheader("Diagrama do Fluxo Taxonômico")
    
        threshold = st.sidebar.slider("Flow threshold", 1, 20, 5)
    
        # garantir só dados numéricos
        term_numeric = term_df.select_dtypes(include=["number"])
        
        co_df = term_numeric.T @ term_numeric
    
        flows = []
    
        # hierarchy correta com custom_tax
    
        for a in custom_tax["Ação"]:
            for o in custom_tax["Objeto"]:
                if a in co_df.index and o in co_df.columns:
                    if co_df.loc[a,o] > threshold:
                        flows.append((a,o,co_df.loc[a,o]))
    
        for o in custom_tax["Objeto"]:
            for c in custom_tax["Contexto"]:
                if o in co_df.index and c in co_df.columns:
                    if co_df.loc[o,c] > threshold:
                        flows.append((o,c,co_df.loc[o,c]))
    
        for c in custom_tax["Contexto"]:
            for p in custom_tax["Fenômeno"]:
                if c in co_df.index and p in co_df.columns:
                    if co_df.loc[c,p] > threshold:
                        flows.append((c,p,co_df.loc[c,p]))
    
        for p in custom_tax["Fenômeno"]:
            for i in custom_tax["Indicador"]:
                if p in co_df.index and i in co_df.columns:
                    if co_df.loc[p,i] > threshold:
                        flows.append((p,i,co_df.loc[p,i]))
    
        for i in custom_tax["Indicador"]:
            for m in custom_tax["Materiais"]:
                if i in co_df.index and m in co_df.columns:
                    if co_df.loc[i,m] > threshold:
                        flows.append((i,m,co_df.loc[i,m]))
    
        if flows:
    
            nodes = list(set([f[0] for f in flows] + [f[1] for f in flows]))
            idx = {n:i for i,n in enumerate(nodes)}
    
            fig = go.Figure(data=[go.Sankey(
                node=dict(label=nodes, pad=20, thickness=15),
                link=dict(
                    source=[idx[f[0]] for f in flows],
                    target=[idx[f[1]] for f in flows],
                    value=[f[2] for f in flows]
                )
            )])
    
            st.plotly_chart(fig, use_container_width=True)
    
        else:
            st.warning("No flows detected")
    
        # =====================================================
        # 📊 TABELA FINAL DA TAXONOMIA
        # =====================================================
    
        st.subheader("📊 Taxonomy Table")
    
        table_data = []
    
        for k, v in custom_tax.items():
            table_data.append({
                "Category": k,
                "Terms": ", ".join(v)
            })
    
        tax_table = pd.DataFrame(table_data)
    
        st.dataframe(tax_table)
    
    else:
        st.info("Upload your CSV file")
        
with tab3:
    
    if st.session_state.taxonomy is None:
        st.warning("Defina a taxonomia na aba 'Gerar Equação' primeiro.")
        st.stop()
        
    taxonomy = st.session_state.taxonomy
    

   #INÍCIO DO CÓDIGO 
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader('Exporte o arquivo do Lens de forma completa')
        
    with col2:
        # =====================================================
        # UPLOAD
        # =====================================================
    
        file_pat = st.file_uploader("Upload CSV Patente", type=["csv"])
    
    if file_pat:
        
        df_pat = pd.read_csv(file_pat)
        df_pat.columns = df_pat.columns.str.strip()
        df_pat["Year"] = pd.to_numeric(df_pat["Publication Year"], errors="coerce")
        df_pat = df_pat.dropna(subset=["Year"])
        df_pat["text"] = df_pat[["Title","Abstract"]].fillna("").agg(" ".join, axis=1).str.lower()
        df_pat["Country"] = df_pat["Jurisdiction"].apply(safe_iso)
    
        # =========================
        # FILTROS SIDEBAR
        # =========================
        
        st.sidebar.subheader("Filtros de Patentes")
        
        # Document Type
        doc_types = df_pat["Document Type"].dropna().unique()
        selected_doc = st.sidebar.multiselect("Tipo de Patente", doc_types)
        
        if selected_doc:
            df_pat = df_pat[df_pat["Document Type"].isin(selected_doc)]
        
        # Legal Status
        legal_status = df_pat["Legal Status"].dropna().unique()
        selected_status = st.sidebar.multiselect("Status Legal", legal_status)
        
        if selected_status:
            df_pat = df_pat[df_pat["Legal Status"].isin(selected_status)]
            
        
        # =========================
        # EXTENDED FAMILY (CRÍTICO)
        # =========================
        
        if "Extended Family Member Jurisdictions" in df_pat.columns:
        
            df_pat["family_list"] = df_pat["Extended Family Member Jurisdictions"].fillna("").apply(
                lambda x: [
                    i.strip().upper() 
                    for i in re.split(r"[;,]", str(x)) 
                    if i.strip()
                ]
            )
        
            all_countries = sorted(list(set(sum(df_pat["family_list"], []))))
        
            selected_family = st.sidebar.multiselect(
                "Proteção em países",
                all_countries
            )
        
            if selected_family:
                selected_family = [p.upper() for p in selected_family]
                df_pat = df_pat[
                    df_pat["family_list"].apply(
                        lambda x: len(x) > 0 and set(selected_family).issubset(set(x)) #set(x) == set(selected_family)
                    )
                ]
                
        # =====================================================
        # FILTRO DE ANO
        # =====================================================
    
        year_range = st.sidebar.slider(
            "Year range Patentes",
            int(df_pat["Year"].min()),
            int(df_pat["Year"].max()),
            (2000, 2025)
        )
    
        df_pat = df_pat[(df_pat["Year"] >= year_range[0]) & (df_pat["Year"] <= year_range[1])]
    
        # =====================================================
        # TERMOS
        # =====================================================
    
        all_terms = list(set(sum(custom_tax.values(), [])))
    
        if len(all_terms) == 0:
            st.warning("Insira termos de pesquisa na barra lateral")
            st.stop()
    
        # =====================================================
        # MATRIZ
        # =====================================================
    
        vectorizer_pat = CountVectorizer(vocabulary=all_terms, binary=True)
        X_pat = vectorizer_pat.fit_transform(df_pat["text"])
    
        term_df_pat = pd.DataFrame(X_pat.toarray(), columns=vectorizer_pat.get_feature_names_out())
        term_df_pat = term_df_pat.astype(int)
       
        # =====================================================
        # FAMÍLIAS
        # =====================================================
        df_family = df_pat.explode("family_list")
        df_family = df_family[df_family["family_list"] != ""]
        family_counts = df_family["family_list"].value_counts()
        df_family["Country"] = df_family["family_list"].apply(safe_iso)
        family_counts = df_family["Country"].value_counts()
        # =====================================================
        # WORD CLOUDS
        # =====================================================
    
        st.subheader("Nuvem de palavras geral")
    
        wc_all = WordCloud(width=1000, height=400, background_color="white") \
            .generate(" ".join(df_pat["text"]))
    
        fig1, ax1 = plt.subplots()
        ax1.imshow(wc_all)
        ax1.axis("off")
        st.pyplot(fig1)
    
        st.subheader("Nuvem de palavras - Considerando a taxonomia proposta")
    
        taxonomy_freq = term_df_pat.sum().to_dict()
    
        wc_tax = WordCloud(width=1000, height=400, background_color="white") \
            .generate_from_frequencies(taxonomy_freq)
    
        fig2, ax2 = plt.subplots()
        ax2.imshow(wc_tax)
        ax2.axis("off")
        st.pyplot(fig2)
    
        # =====================================================
        # PUBLICAÇÕES
        # =====================================================
    
        st.subheader("Evolução das patentes ao longo dos anos")
    
        year_counts = df_pat["Year"].value_counts().sort_index()
        cumulative = year_counts.cumsum()
        
        col1, col2 = st.columns(2)
        with col1:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=year_counts.index, y=year_counts.values, name="Yearly"))
            fig.update_layout(title="Patentes por Ano")
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=cumulative.index, y=cumulative.values, name="Cumulative"))
            fig.update_layout(title="Evolução cumulativa das patentes")
            st.plotly_chart(fig, use_container_width=True)
        # =====================================================
        # 📈 TERM EVOLUTION (CUMULATIVE)
        # =====================================================
        
        st.subheader("Evolução das patentes acerca das taxonomias propostas")
        
        col1, col2 = st.columns(2)
        with col1:
            term_year_df_pat = term_df_pat.copy()
            term_year_df_pat["Year"] = df_pat["Year"].values
            yearly_terms = term_year_df_pat.groupby("Year").sum().sort_index()
            yearly_cum = yearly_terms.cumsum()
            # top 10 termos mais frequentes
            top_terms = term_df_pat.sum().sort_values(ascending=False).head(10).index
            fig = go.Figure()  
            for term in custom_tax["Ação"]:
                fig.add_trace(go.Scatter(
                    x=yearly_cum.index,
                    y=yearly_cum[term],
                    mode="lines",
                    name=term
                ))
            fig.update_layout(title="Evolução das Patentes - Verbos de Ação")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            term_year_df_pat = term_df_pat.copy()
            term_year_df_pat["Year"] = df_pat["Year"].values         
            yearly_terms = term_year_df_pat.groupby("Year").sum().sort_index()
            yearly_cum = yearly_terms.cumsum()  
            # top 10 termos mais frequentes
            top_terms = term_df_pat.sum().sort_values(ascending=False).head(10).index    
            fig = go.Figure()     
            for term in custom_tax["Contexto"]:
                fig.add_trace(go.Scatter(
                    x=yearly_cum.index,
                    y=yearly_cum[term],
                    mode="lines",
                    name=term
                ))
            fig.update_layout(title="Evolução das Patentes - Contexto")    
            st.plotly_chart(fig, use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            term_year_df_pat = term_df_pat.copy()
            term_year_df_pat["Year"] = df_pat["Year"].values
            yearly_terms = term_year_df_pat.groupby("Year").sum().sort_index()
            yearly_cum = yearly_terms.cumsum()
            # top 10 termos mais frequentes
            top_terms = term_df_pat.sum().sort_values(ascending=False).head(10).index
            fig = go.Figure()  
            for term in custom_tax["Objeto"]:
                fig.add_trace(go.Scatter(
                    x=yearly_cum.index,
                    y=yearly_cum[term],
                    mode="lines",
                    name=term
                ))
            fig.update_layout(title="Evolução das Patentes - Objeto")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            term_year_df_pat = term_df_pat.copy()
            term_year_df_pat["Year"] = df_pat["Year"].values         
            yearly_terms = term_year_df_pat.groupby("Year").sum().sort_index()
            yearly_cum = yearly_terms.cumsum()  
            # top 10 termos mais frequentes
            top_terms = term_df_pat.sum().sort_values(ascending=False).head(10).index    
            fig = go.Figure()     
            for term in custom_tax["Fenômeno"]:
                fig.add_trace(go.Scatter(
                    x=yearly_cum.index,
                    y=yearly_cum[term],
                    mode="lines",
                    name=term
                ))
            fig.update_layout(title="Evolução das Patentes - Fenômeno")    
            st.plotly_chart(fig, use_container_width=True)
            
        col1, col2 = st.columns(2)
        with col1:
            term_year_df_pat = term_df_pat.copy()
            term_year_df_pat["Year"] = df_pat["Year"].values
            yearly_terms = term_year_df_pat.groupby("Year").sum().sort_index()
            yearly_cum = yearly_terms.cumsum()
            # top 10 termos mais frequentes
            top_terms = term_df_pat.sum().sort_values(ascending=False).head(10).index
            fig = go.Figure()  
            for term in custom_tax["Indicador"]:
                fig.add_trace(go.Scatter(
                    x=yearly_cum.index,
                    y=yearly_cum[term],
                    mode="lines",
                    name=term
                ))
            fig.update_layout(title="Evolução das Patentes - Indicador")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            term_year_df_pat = term_df_pat.copy()
            term_year_df_pat["Year"] = df_pat["Year"].values         
            yearly_terms = term_year_df_pat.groupby("Year").sum().sort_index()
            yearly_cum = yearly_terms.cumsum()  
            # top 10 termos mais frequentes
            top_terms = term_df_pat.sum().sort_values(ascending=False).head(10).index    
            fig = go.Figure()     
            for term in custom_tax["Materiais"]:
                fig.add_trace(go.Scatter(
                    x=yearly_cum.index,
                    y=yearly_cum[term],
                    mode="lines",
                    name=term
                ))
            fig.update_layout(title="Evolução das Patentes - Materiais")    
            st.plotly_chart(fig, use_container_width=True)
        
        
    
        # =====================================================
        # PAÍSES
        # =====================================================
    
        #countries = []
        df_pat["Country"] = df_pat["Jurisdiction"].apply(safe_iso)
        # Ranking geral
        country_counts = df_pat["Country"].value_counts()
        # Top 10
        top10 = country_counts.head(10)
        # Posição do Brasil
        if "Brazil" in country_counts.index:
            brasil_rank = country_counts.index.get_loc("Brazil") + 1
            brasil_label = f"Brazil ({brasil_rank}º)"
            brasil_value = country_counts["Brazil"]
        else:
            brasil_rank = None
            brasil_label = None
            brasil_value = None
                
                
    
        # =====================================================
        # CUMULATIVO POR PAÍS
        # =====================================================
        st.subheader("Análise de Patentes produzida por países")
        col1, col2 = st.columns(2)
        with col1:
            #st.subheader("Produção Científica acumulada por país")
            country_year = df_pat.groupby(["Country","Year"]).size().reset_index(name="Count")
            fig = go.Figure()
            # Lista de países: Top 10 + Brasil (se não estiver no top 10)
            selected_countries = list(top10.index)
            
            if "Brazil" in country_counts.index and "Brazil" not in selected_countries:
                selected_countries.append("Brazil")
            
            for c in selected_countries:
                data = country_year[country_year["Country"] == c].sort_values("Year")
            
                name = c
                if c == "Brazil" and brasil_rank:
                    name = brasil_label
            
                fig.add_trace(go.Scatter(
                    x=data["Year"],
                    y=data["Count"].cumsum(),
                    name=name
                ))
            fig.update_layout(title="Produção Científica acumulada por país")  
            st.plotly_chart(fig, use_container_width=True)
            
            
            
        with col2:
            #st.subheader("Países com mais produções Científicas")
            bar_data = top10.copy()

            if "Brazil" in country_counts.index and "Brazil" not in bar_data.index:
                bar_data[brasil_label] = brasil_value
            elif "Brazil" in bar_data.index:
                # substitui nome para incluir posição
                bar_data.rename(index={"Brazil": brasil_label}, inplace=True)
        
            # Converter para dataframe
            bar_df_pat = bar_data.reset_index()
            bar_df_pat.columns = ["Country", "Count"]
            
            fig_bar = go.Figure(go.Bar(
                x=bar_df_pat["Count"],
                y=bar_df_pat["Country"],
                orientation='h'
            ))
            
            fig_bar.update_layout(
                yaxis=dict(autorange="reversed")  # maior no topo
            )
            fig_bar.update_layout(title="Países com mais produções Científicas")
            st.plotly_chart(fig_bar, use_container_width=True)
            
 
        col1, col2 = st.columns(2)
        
        with col1:
        
            # =====================================================
            # 📊 PROTEÇÃO POR PAÍS (EXTENDED FAMILY) - EM %
            # =====================================================
    
            # total de patentes
            total_patents = df_pat.shape[0]
    
            # calcular porcentagem
            family_pct = (family_counts / total_patents) * 100
    
            # ordenar
            family_pct = family_pct.sort_values(ascending=False)
    
            # =====================================================
            # TOP N + BRASIL
            # =====================================================
    
            top_n = 10
            top_data = family_pct.head(top_n).copy()
    
            # posição do Brasil
            if "Brazil" in family_pct.index:
                br_rank = family_pct.index.get_loc("Brazil") + 1
                br_label = f"Brazil ({br_rank}º)"
                br_value = family_pct["Brazil"]
    
                if "Brazil" not in top_data.index:
                    top_data[br_label] = br_value
                else:
                    top_data.rename(index={"Brazil": br_label}, inplace=True)
    
            # ordenar para gráfico horizontal
            data = top_data.sort_values()
    
            # =====================================================
            # GRÁFICO
            # =====================================================
    
            fig = go.Figure(go.Bar(
                x=data.values,
                y=data.index,
                orientation='h'
            ))
    
            fig.update_traces(
                text=[f"{v:.1f}%" for v in data.values],
                textposition="outside"
            )
    
            fig.update_layout(
                title="Países com maior proteção de patentes (Extended Family)",
                xaxis_title="% de patentes protegidas",
                yaxis=dict(autorange="reversed")
            )
    
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # =====================================================
            # 📊 LEGAL STATUS
            # =====================================================
            st.subheader("📊 Status Legal das Patentes")
            status_counts = df_pat["Legal Status"].fillna("Unknown").value_counts()
            fig = go.Figure(go.Bar(
                x=status_counts.index,
                y=status_counts.values
            ))
            fig.update_layout(
                title="Distribuição por Status Legal",
                xaxis_title="Status",
                yaxis_title="Número de Patentes"
            )
            st.plotly_chart(fig, use_container_width=True)
                    
        
        # =====================================================
        # 🏢 TOP DEPOSITANTES (OWNERS)
        # =====================================================
        st.subheader("🏢 Top 10 Depositantes (Owners)")
        # ⚠️ ajuste conforme nome da coluna do Lens
        # limpar
        df_pat["Owners"] = df_pat["Owners"].fillna("Unknown")

        # =====================================================
        # TOP 10 OWNERS
        # =====================================================
        owner_series = df_pat["Owners"].dropna()
        owner_series = owner_series[owner_series.str.strip() != ""]
        owner_series = owner_series[owner_series.str.lower() != "Unknown"]
        owner_counts = owner_series.value_counts()
        #owner_counts = df_pat["Owners"].value_counts()
        top_owners = owner_counts.head(10)
        # =====================================================
        # EXPANDIR FAMILY (países de proteção)
        # =====================================================
        df_family = df_pat.copy()
        df_family = df_family.explode("family_list")
        df_family = df_family[df_family["family_list"] != ""]
        # converter para nome do país
        df_family["Country"] = df_family["family_list"].apply(safe_iso)
        # remover inválidos
        df_family = df_family.dropna(subset=["Country"])
        # =====================================================
        # CALCULAR DISTRIBUIÇÃO POR OWNER
        # =====================================================
        rows = []
        for Owners in top_owners.index:
            subset = df_family[df_family["Owners"] == Owners]
            total = owner_counts[Owners]
            #Avaliar isso aqui
            country_counts = subset["Country"].value_counts() #subset.groupby("Country")["id"].nunique().sort_values(ascending=False)
            # pegar top 3 países
            top_countries = country_counts.head(3)
            # formatar string com %
            country_info = []
            for c, v in top_countries.items():
                pct = (v / total) * 100
                country_info.append(f"{c} ({pct:.0f}%)")
            rows.append({
                "Owner": Owners,
                "Patentes": total,
                "Principais Mercados": ", ".join(country_info)
            })
        # =====================================================
        # DATAFRAME FINAL
        # =====================================================
        owners_df = pd.DataFrame(rows)
        # =====================================================
        # EXIBIR
        # =====================================================     
        st.dataframe(owners_df, use_container_width=True)
        
        
                
         
        col1, col2 = st.columns(2)
        
        with col1:
            # =====================================================
            # 🔎 TOP 10 CPC
            # =====================================================
            
            st.subheader("🔎 Top 10 CPC")
            
            cpc_col = "CPC Classifications"  # ajuste se necessário
    
            # expandir CPC (geralmente separados por ;)
            df_cpc = df_pat.copy()
            df_cpc[cpc_col] = df_cpc[cpc_col].fillna("")
            
            df_cpc["CPC_list"] = df_cpc[cpc_col].apply(
                lambda x: [i.strip() for i in str(x).split(";") if i.strip()]
            )
            df_cpc = df_cpc.explode("CPC_list")
            # top 10
            cpc_counts = df_cpc["CPC_list"].value_counts()
            top_cpc = cpc_counts.head(10)
            # expandir países
            df_cpc = df_cpc.explode("family_list")
            df_cpc = df_cpc[df_cpc["family_list"] != ""]
            df_cpc["Country"] = df_cpc["family_list"].apply(safe_iso)
            df_cpc = df_cpc.dropna(subset=["Country"])
            rows = []
            for cpc in top_cpc.index:
                subset = df_cpc[df_cpc["CPC_list"] == cpc]
                total = cpc_counts[cpc]
                country_counts = subset["Country"].value_counts().head(3)
                country_info = []
                for c, v in country_counts.items():
                    pct = (v / total) * 100
                    country_info.append(f"{c} ({pct:.0f}%)")
                rows.append({
                    "CPC": cpc,
                    "Patentes": total,
                    "Principais Mercados": ", ".join(country_info)
                })      
            cpc_df = pd.DataFrame(rows)           
            st.dataframe(cpc_df, use_container_width=True)
        
        with col2:
            # =====================================================
            # 🔎 TOP 10 IPCR
            # =====================================================
            
            st.subheader("🔎 Top 10 IPCR")
            
            ipc_col = "IPCR Classifications"  # ou "IPCR"
            
            df_ipc = df_pat.copy()
            df_ipc[ipc_col] = df_ipc[ipc_col].fillna("")
            
            df_ipc["IPC_list"] = df_ipc[ipc_col].apply(
                lambda x: [i.strip() for i in str(x).split(";") if i.strip()]
            )
            
            df_ipc = df_ipc.explode("IPC_list")
            
            ipc_counts = df_ipc["IPC_list"].value_counts()
            top_ipc = ipc_counts.head(10)
            
            df_ipc = df_ipc.explode("family_list")
            df_ipc = df_ipc[df_ipc["family_list"] != ""]
            df_ipc["Country"] = df_ipc["family_list"].apply(safe_iso)
            df_ipc = df_ipc.dropna(subset=["Country"])
            
            rows = []
            
            for ipc in top_ipc.index:
            
                subset = df_ipc[df_ipc["IPC_list"] == ipc]
                total = ipc_counts[ipc]  
                country_counts = subset["Country"].value_counts().head(3) 
                country_info = []
                for c, v in country_counts.items():
                    pct = (v / total) * 100
                    country_info.append(f"{c} ({pct:.0f}%)")
                rows.append({
                    "IPCR": ipc,
                    "Patentes": total,
                    "Principais Mercados": ", ".join(country_info)
                })     
            ipc_df = pd.DataFrame(rows)
            st.dataframe(ipc_df, use_container_width=True)
        
        
       


        # =====================================================
        # FLOW (AGORA FILTRADO CORRETAMENTE)
        # =====================================================
    
        st.subheader("Diagrama do Fluxo Taxonômico")
    
        threshold2 = st.sidebar.slider("Flow threshold Patentes", 1, 20, 5)
    
        # garantir só dados numéricos
        term_numeric = term_df_pat.select_dtypes(include=["number"])
        
        co_df_pat = term_numeric.T @ term_numeric
    
        flows = []
    
        # hierarchy correta com custom_tax
    
        for a in custom_tax["Ação"]:
            for o in custom_tax["Objeto"]:
                if a in co_df_pat.index and o in co_df_pat.columns:
                    if co_df_pat.loc[a,o] > threshold2:
                        flows.append((a,o,co_df_pat.loc[a,o]))
    
        for o in custom_tax["Objeto"]:
            for c in custom_tax["Contexto"]:
                if o in co_df_pat.index and c in co_df_pat.columns:
                    if co_df_pat.loc[o,c] > threshold2:
                        flows.append((o,c,co_df_pat.loc[o,c]))
    
        for c in custom_tax["Contexto"]:
            for p in custom_tax["Fenômeno"]:
                if c in co_df_pat.index and p in co_df_pat.columns:
                    if co_df_pat.loc[c,p] > threshold2:
                        flows.append((c,p,co_df_pat.loc[c,p]))
    
        for p in custom_tax["Fenômeno"]:
            for i in custom_tax["Indicador"]:
                if p in co_df_pat.index and i in co_df_pat.columns:
                    if co_df_pat.loc[p,i] > threshold2:
                        flows.append((p,i,co_df_pat.loc[p,i]))
    
        for i in custom_tax["Indicador"]:
            for m in custom_tax["Materiais"]:
                if i in co_df_pat.index and m in co_df_pat.columns:
                    if co_df_pat.loc[i,m] > threshold2:
                        flows.append((i,m,co_df_pat.loc[i,m]))
    
        if flows:
    
            nodes = list(set([f[0] for f in flows] + [f[1] for f in flows]))
            idx = {n:i for i,n in enumerate(nodes)}
    
            fig = go.Figure(data=[go.Sankey(
                node=dict(label=nodes, pad=20, thickness=15),
                link=dict(
                    source=[idx[f[0]] for f in flows],
                    target=[idx[f[1]] for f in flows],
                    value=[f[2] for f in flows]
                )
            )])
    
            st.plotly_chart(fig, use_container_width=True)
    
        else:
            st.warning("No flows detected")
     
    
    else:
        st.info("Upload your CSV file")