# ════════════════════════════════════════════════════════
# DASHBOARD — Assurance Data 360
# ════════════════════════════════════════════════════════

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Assurance Data 360",
    page_icon="🏛️",
    layout="wide"
)

st.markdown("""
<style>
    [data-testid="metric-container"] {
        background-color: #f0fff4;
        border: 1px solid #9ae6b4;
        border-radius: 12px;
        padding: 16px;
    }
    [data-testid="stMetricValue"] { color: #276749; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    clients      = pd.read_csv("data/clients.csv")
    interactions = pd.read_csv("data/interactions.csv")
    contrats     = pd.read_csv("data/contrats.csv")
    sinistres    = pd.read_csv("data/sinistres.csv")
    golden       = pd.read_csv("data/golden_record.csv")
    kpis         = pd.read_csv("data/kpis_mensuels.csv")
    ml           = pd.read_csv("data/ml_resultats.csv")
    profil       = pd.read_csv("data/profil_clients_enrichi.csv")
    interactions["date"] = pd.to_datetime(interactions["date"])
    return clients, interactions, contrats, sinistres, golden, kpis, ml, profil

clients, interactions, contrats, sinistres, golden, kpis, ml, profil = load_data()

# ── Sidebar ──────────────────────────────────────────────
st.sidebar.markdown("### 🏛️ Assurance Data 360")
st.sidebar.markdown("*Analytics omnicanal · 2024*")
st.sidebar.markdown("---")
page = st.sidebar.radio("Navigation", [
    "🏠 Vue globale",
    "📊 Parcours & Frictions",
    "🎯 Segmentation clients",
    "⚠️ Churn & NBA",
    "📈 KPIs mensuels",
    "🔍 Qualité données"
])
st.sidebar.markdown("---")
st.sidebar.markdown("*Développé par Rafika Cervera*")

# ════════════════════════════════════════════════════════
# PAGE 1 — VUE GLOBALE
# ════════════════════════════════════════════════════════
if page == "🏠 Vue globale":
    st.markdown("# 🏛️ Assurance Data 360")
    st.markdown("**Tableau de bord analytics omnicanal · Décembre 2024**")
    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Clients actifs", f"{len(clients[clients['statut']=='client_actif']):,}",
                f"{len(clients[clients['statut']=='client_actif'])/len(clients)*100:.1f}%")
    col2.metric("Interactions totales", f"{len(interactions):,}")
    col3.metric("Contrats actifs", f"{len(contrats[contrats['statut_contrat']=='actif']):,}")
    col4.metric("Taux de churn", f"{len(clients[clients['statut']=='résilié'])/len(clients)*100:.1f}%")

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Répartition des statuts clients**")
        fig = px.pie(
            clients["statut"].value_counts().reset_index(),
            values="count", names="statut",
            hole=0.45, template="plotly_white",
            color_discrete_sequence=["#2D6A4F","#48BB78","#9AE6B4","#C53030"]
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("**Interactions par canal**")
        canal_stats = interactions.groupby("canal").agg(
            nb=("interaction_id","count"),
            satisfaction=("satisfaction","mean")
        ).reset_index()
        fig = px.bar(
            canal_stats.sort_values("nb", ascending=False),
            x="canal", y="nb",
            color="satisfaction",
            color_continuous_scale="Greens",
            template="plotly_white",
            labels={"nb":"Interactions","satisfaction":"Satisfaction"}
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("**Évolution mensuelle des interactions**")
    interactions["mois"] = interactions["date"].dt.strftime("%Y-%m")
    evol = interactions.groupby(["mois","canal"])["interaction_id"].count().reset_index()
    evol.columns = ["mois","canal","nb"]
    fig = px.line(evol, x="mois", y="nb", color="canal",
                  template="plotly_white",
                  labels={"nb":"Interactions","mois":"Mois"})
    fig.update_xaxes(tickangle=45)
    st.plotly_chart(fig, use_container_width=True)

# ════════════════════════════════════════════════════════
# PAGE 2 — PARCOURS & FRICTIONS
# ════════════════════════════════════════════════════════
elif page == "📊 Parcours & Frictions":
    st.markdown("# 📊 Parcours clients & Frictions")
    st.markdown("---")

    # Taux d'abandon par canal
    frictions = interactions.groupby("canal").agg(
        nb_total=("interaction_id","count"),
        nb_abandon=("resultat", lambda x: (x=="abandon").sum()),
        satisfaction=("satisfaction","mean")
    ).reset_index()
    frictions["taux_abandon"] = (frictions["nb_abandon"]/frictions["nb_total"]*100).round(2)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Taux d'abandon par canal (%)**")
        fig = px.bar(
            frictions.sort_values("taux_abandon", ascending=False),
            x="canal", y="taux_abandon",
            color="taux_abandon", color_continuous_scale="Reds",
            text="taux_abandon", template="plotly_white"
        )
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("**Satisfaction vs Taux d'abandon**")
        fig = px.scatter(
            frictions, x="satisfaction", y="taux_abandon",
            text="canal", size="nb_total", color="canal",
            template="plotly_white"
        )
        fig.update_traces(textposition="top center")
        st.plotly_chart(fig, use_container_width=True)

    # Top frictions par type
    st.markdown("**Top types d'interactions abandonnées**")
    top_frictions = interactions.groupby("type_interaction").agg(
        nb_total=("interaction_id","count"),
        nb_abandon=("resultat", lambda x: (x=="abandon").sum()),
        satisfaction=("satisfaction","mean")
    ).reset_index()
    top_frictions["taux_abandon"] = (top_frictions["nb_abandon"]/top_frictions["nb_total"]*100).round(2)
    fig = px.bar(
        top_frictions.sort_values("taux_abandon", ascending=False).head(8),
        x="taux_abandon", y="type_interaction", orientation="h",
        color="satisfaction", color_continuous_scale="RdYlGn",
        text="taux_abandon", template="plotly_white"
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    st.plotly_chart(fig, use_container_width=True)

# ════════════════════════════════════════════════════════
# PAGE 3 — SEGMENTATION
# ════════════════════════════════════════════════════════
elif page == "🎯 Segmentation clients":
    st.markdown("# 🎯 Segmentation clients — K-Means")
    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)
    for i, (seg, color) in enumerate(zip(
        ["Clients basiques seniors","Clients premium jeunes",
         "Clients premium matures","Clients basiques matures"],
        [col1, col2, col3, col4]
    )):
        nb = len(ml[ml["segment_nom"]==seg])
        ltv = ml[ml["segment_nom"]==seg]["ltv_estimee"].mean()
        color.metric(seg.replace("Clients ",""), f"{nb:,}", f"LTV: {ltv:,.0f}€")

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Répartition des segments**")
        seg_counts = ml["segment_nom"].value_counts().reset_index()
        seg_counts.columns = ["segment","nb"]
        fig = px.pie(seg_counts, values="nb", names="segment",
                     hole=0.4, template="plotly_white",
                     color_discrete_sequence=["#2D6A4F","#0077B6","#553C9A","#C05621"])
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("**LTV moyenne par segment**")
        ltv_seg = ml.groupby("segment_nom")["ltv_estimee"].mean().reset_index()
        ltv_seg.columns = ["segment","ltv"]
        fig = px.bar(
            ltv_seg.sort_values("ltv", ascending=False),
            x="segment", y="ltv",
            color="ltv", color_continuous_scale="Greens",
            text="ltv", template="plotly_white"
        )
        fig.update_traces(texttemplate="%{text:,.0f}€", textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("**Profil détaillé par segment**")
    seg_choisi = st.selectbox("Choisir un segment", ml["segment_nom"].unique())
    seg_data = ml[ml["segment_nom"]==seg_choisi]
    col1, col2, col3 = st.columns(3)
    col1.metric("Clients", f"{len(seg_data):,}")
    col2.metric("Age moyen", f"{seg_data['age'].mean():.0f} ans")
    col3.metric("Satisfaction moy.", f"{seg_data['satisfaction_moy'].mean():.2f}/10")

# ════════════════════════════════════════════════════════
# PAGE 4 — CHURN & NBA
# ════════════════════════════════════════════════════════
elif page == "⚠️ Churn & NBA":
    st.markdown("# ⚠️ Churn & Next Best Action")
    st.markdown("---")

    # Seuil de risque
    seuil = st.slider("Seuil de risque churn", 0.3, 0.9, 0.6, 0.05)
    clients_risque = ml[ml["score_churn"] >= seuil]

    col1, col2, col3 = st.columns(3)
    col1.metric("Clients à risque", f"{len(clients_risque):,}",
                f"seuil ≥ {seuil:.0%}")
    col2.metric("Score churn moyen", f"{clients_risque['score_churn'].mean():.2f}")
    col3.metric("LTV à risque", f"{clients_risque['ltv_estimee'].sum():,.0f}€")

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Distribution du score de churn**")
        fig = px.histogram(
            ml, x="score_churn", nbins=40,
            color_discrete_sequence=["#C53030"],
            template="plotly_white"
        )
        fig.add_vline(x=seuil, line_dash="dash", line_color="orange",
                      annotation_text=f"Seuil {seuil:.0%}")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("**Next Best Action — Répartition**")
        nba_counts = ml["nba_produit"].value_counts().reset_index()
        nba_counts.columns = ["produit","nb"]
        fig = px.bar(
            nba_counts, x="produit", y="nb",
            color="nb", color_continuous_scale="Blues",
            text="nb", template="plotly_white"
        )
        fig.update_traces(textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("**Top 20 clients à risque**")
    top_risque = ml[ml["score_churn"] >= seuil].nlargest(20, "score_churn")[
        ["client_id","statut","age","score_churn","ltv_estimee","nba_produit","segment_nom"]
    ]
    st.dataframe(top_risque, use_container_width=True)

# ════════════════════════════════════════════════════════
# PAGE 5 — KPIs MENSUELS
# ════════════════════════════════════════════════════════
elif page == "📈 KPIs mensuels":
    st.markdown("# 📈 KPIs mensuels")
    st.markdown("---")

    # Dernière période
    dernier = kpis.iloc[-1]
    avant_dernier = kpis.iloc[-2]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Satisfaction", f"{dernier['satisfaction_moy']:.2f}/10",
                f"{dernier['satisfaction_moy']-avant_dernier['satisfaction_moy']:.2f}")
    col2.metric("Conversion", f"{dernier['taux_conversion']:.1f}%",
                f"{dernier['taux_conversion']-avant_dernier['taux_conversion']:.1f}%")
    col3.metric("Abandon", f"{dernier['taux_abandon']:.1f}%",
                f"{dernier['taux_abandon']-avant_dernier['taux_abandon']:.1f}%")
    col4.metric("Souscriptions", f"{dernier['nb_souscriptions']:.0f}",
                f"{dernier['nb_souscriptions']-avant_dernier['nb_souscriptions']:.0f}")

    st.markdown("---")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=kpis["mois"], y=kpis["satisfaction_moy"],
                             mode="lines+markers", name="Satisfaction",
                             line=dict(color="#2D6A4F", width=2)))
    fig.add_hline(y=7.0, line_dash="dash", line_color="orange",
                  annotation_text="Objectif 7.0")
    fig.update_layout(title="Évolution de la satisfaction mensuelle",
                      template="plotly_white")
    fig.update_xaxes(tickangle=45)
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        fig = px.line(kpis, x="mois", y=["taux_conversion","taux_abandon"],
                      title="Conversion vs Abandon (%)",
                      template="plotly_white")
        fig.update_xaxes(tickangle=45)
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = px.bar(kpis, x="mois", y="nb_souscriptions",
                     title="Souscriptions mensuelles",
                     color="nb_souscriptions",
                     color_continuous_scale="Greens",
                     template="plotly_white")
        fig.update_xaxes(tickangle=45)
        st.plotly_chart(fig, use_container_width=True)

# ════════════════════════════════════════════════════════
# PAGE 6 — QUALITÉ DONNÉES
# ════════════════════════════════════════════════════════
elif page == "🔍 Qualité données":
    st.markdown("# 🔍 Qualité des données")
    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Score Clients", "100/100", "✅")
    col2.metric("Score Interactions", "100/100", "✅")
    col3.metric("Score Contrats", "100/100", "✅")
    col4.metric("Score Sinistres", "100/100", "✅")

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Score qualité par table**")
        scores_df = pd.DataFrame({
            "table": ["Clients","Interactions","Contrats","Sinistres"],
            "score": [100, 100, 100, 100]
        })
        fig = px.bar(scores_df, x="table", y="score",
                     color="score", color_continuous_scale="Greens",
                     text="score", template="plotly_white",
                     labels={"score":"Score /100"})
        fig.update_traces(texttemplate="%{text}/100", textposition="outside")
        fig.update_layout(yaxis_range=[0,115], showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("**Distribution LTV clients**")
        fig = px.histogram(
            golden[golden["ltv_estimee"]>0],
            x="ltv_estimee", nbins=40,
            color_discrete_sequence=["#2D6A4F"],
            template="plotly_white",
            labels={"ltv_estimee":"LTV estimée (€)"}
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("**Golden Record — Aperçu**")
    cols = ["client_id","statut","age","region","nb_contrats_actifs",
            "prime_totale_annuelle","satisfaction_moy","ltv_estimee"]
    st.dataframe(golden[cols].head(20), use_container_width=True)

# Footer
st.markdown("---")
st.markdown("*🏛️ Assurance Data 360 · Rafika Cervera — Data Manager & IA · 2026*")