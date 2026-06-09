"""
╔══════════════════════════════════════════════════════════════╗
║     Potion Craft - Archives Magiques du Ministère            ║
║     Projet : py-potion-craft-BOTELLA                         ║
║     Dashboard Streamlit                                      ║
╚══════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx
from itertools import combinations
from collections import Counter

# ============================================================
# CONFIGURATION PAGE
# ============================================================
st.set_page_config(
    page_title="⚗️ Archives Magiques",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# CSS PERSONNALISÉ
# ============================================================
st.markdown("""
<style>
    .main-title {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(90deg, #2E86DE, #8E44AD);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1rem 0;
    }
    .section-title {
        font-size: 1.4rem;
        font-weight: 700;
        color: #2E86DE;
        border-left: 4px solid #8E44AD;
        padding-left: 0.6rem;
        margin: 1.5rem 0 0.8rem 0;
    }
    .metric-card {
        background: linear-gradient(135deg, #1a1a2e, #16213e);
        border-radius: 12px;
        padding: 1rem;
        border: 1px solid #2E86DE;
        text-align: center;
    }
    .stDataFrame { border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# CONSTANTES
# ============================================================
FICHIER = "potions-craft.xlsx"

COULEURS_MAGIE = {
    "Bleue":   "#2E86DE",
    "Rouge":   "#E74C3C",
    "Noire":   "#2C3E50",
    "Blanche": "#BDC3C7",
    "Verte":   "#27AE60",
    "Pourpre": "#8E44AD",
    "Inconnu": "#95A5A6",
}

COULEURS_LIGNEE = {
    "Black":         "#E74C3C",
    "Rogue":         "#2C3E50",
    "De Kelliwic'h": "#27AE60",
    "De Kamelott":   "#2E86DE",
    "Strange":       "#8E44AD",
    "Jedusor":       "#E67E22",
    "Inconnue":      "#95A5A6",
}

INGREDIENTS_MANQUANTS = pd.DataFrame([
    {"ingredients": "Cheveux de sorcière",    "poids_pincee": 25,  "prix": 12, "type": "Ingrédient secret"},
    {"ingredients": "Plumes de fenix",        "poids_pincee": 30,  "prix": 18, "type": "Ingrédient secret"},
    {"ingredients": "Baguette enchantée",     "poids_pincee": 45,  "prix": 15, "type": "Matériel magique"},
    {"ingredients": "Ongles de lutin",        "poids_pincee": 20,  "prix": 10, "type": "Ingrédient secret"},
    {"ingredients": "Eau bénite",             "poids_pincee": 38,  "prix": 14, "type": "Matériel non magique"},
    {"ingredients": "Écu en acier",           "poids_pincee": 11,  "prix": 15, "type": "Matériel magique"},
    {"ingredients": "Ecu en acier de maître", "poids_pincee": 68,  "prix": 12, "type": "Matériel non magique"},
])

# ============================================================
# UTILITAIRES
# ============================================================
def normalise(s):
    """Normalise les apostrophes et espaces."""
    if pd.isna(s):
        return s
    s = str(s).strip()
    s = s.replace("\u2019", "'").replace("`", "'")
    return s

def nettoyer_lignee(s):
    """Corrige les variantes de lignée."""
    if pd.isna(s):
        return "Inconnue"
    s = normalise(s)
    correctifs = {"Bl'ack": "Black"}
    return correctifs.get(s, s)

def nettoyer_colonnes(df):
    """Supprime les espaces dans les noms de colonnes."""
    df.columns = [c.strip().replace(" ", "_") for c in df.columns]
    return df

# ============================================================
# CHARGEMENT ET NETTOYAGE DES DONNÉES
# ============================================================
@st.cache_data
def charger_donnees():
    # ── 1. INGRÉDIENTS ──────────────────────────────────────
    ingredients = pd.read_excel(FICHIER, sheet_name="liste-ingredients")
    ingredients = nettoyer_colonnes(ingredients)
    ingredients["ingredients"] = ingredients["ingredients"].apply(normalise)

    # Ajout des ingrédients manquants
    manquants_filtres = INGREDIENTS_MANQUANTS[
        ~INGREDIENTS_MANQUANTS["ingredients"].isin(ingredients["ingredients"].tolist())
    ]
    if not manquants_filtres.empty:
        ingredients = pd.concat([ingredients, manquants_filtres], ignore_index=True)

    # ── 2. INVENTEURS ───────────────────────────────────────
    inventeurs = pd.read_excel(FICHIER, sheet_name="liste-inventeurs")
    inventeurs = nettoyer_colonnes(inventeurs)
    inventeurs["pseudo"] = inventeurs["pseudo"].apply(normalise)
    inventeurs["lignee"] = inventeurs["lignee"].apply(nettoyer_lignee)

    # ── 3. TYPES DE MAGIE ───────────────────────────────────
    magies = pd.read_excel(FICHIER, sheet_name="liste-types-de-magie")
    magies = nettoyer_colonnes(magies)
    magies.columns = [c.lower().replace("-", "_") for c in magies.columns]
    if "type_de_magie" not in magies.columns:
        magies.columns = ["type_de_magie", "competences"]
    magies["type_de_magie"] = magies["type_de_magie"].apply(normalise)
    magies["competences"]   = magies["competences"].apply(normalise)

    # ── 4. POTIONS-INVENTEURS ───────────────────────────────
    pot_inv = pd.read_excel(FICHIER, sheet_name="potions-inventeurs")
    pot_inv = nettoyer_colonnes(pot_inv)
    pot_inv.columns = [c.lower().replace("-", "_") for c in pot_inv.columns]
    pot_inv["potion"]    = pot_inv["potion"].apply(normalise)
    pot_inv["inventeur"] = pot_inv["inventeur"].apply(
        lambda x: normalise(x) if not pd.isna(x) else "Inconnu"
    )
    type_col = [c for c in pot_inv.columns if "type" in c and "magie" in c]
    if type_col:
        pot_inv = pot_inv.rename(columns={type_col[0]: "type_magie_potion"})
    pot_inv["type_magie_potion"] = pot_inv["type_magie_potion"].apply(normalise)

    # ── 5. RECETTES ─────────────────────────────────────────
    recettes = pd.read_excel(FICHIER, sheet_name="potions")
    recettes = nettoyer_colonnes(recettes)
    recettes["potion"] = recettes["potion"].apply(normalise)
    recettes.columns   = [c.replace("__", "_") for c in recettes.columns]

    return recettes, ingredients, inventeurs, magies, pot_inv

# ============================================================
# CALCUL DU COÛT
# ============================================================
def calculer_cout_potion(row, ingredients):
    """
    Calcule le coût total d'une recette.
    coût = somme(quantité_i × prix_unitaire_i)
    Le prix dans liste-ingredients = prix par unité de l'ingrédient.
    """
    cout = 0.0
    for i in range(1, 5):
        ing_col = f"ingredient_{i}"
        qte_col = f"quantite_{i}"

        ing_nom = row.get(ing_col)
        if pd.isna(ing_nom) or str(ing_nom).strip() in ("", "nan"):
            continue

        ing_nom = normalise(ing_nom)
        qte     = row.get(qte_col, 0)

        match = ingredients[ingredients["ingredients"] == ing_nom]
        if match.empty:
            match = ingredients[
                ingredients["ingredients"].str.lower() == ing_nom.lower()
            ]

        if not match.empty:
            prix_unit = float(match.iloc[0]["prix"])
            try:
                qte_float = float(qte)
            except (ValueError, TypeError):
                qte_float = 0.0
            cout += prix_unit * qte_float

    return round(cout, 2)

# ============================================================
# CONSTRUCTION DU DATAFRAME PRINCIPAL
# ============================================================
@st.cache_data
def construire_dataframe_principal(_recettes, _ingredients, _inventeurs,
                                    _magies, _pot_inv):
    df = _recettes.copy()

    # Calcul coût et bénéfice
    df["cout"]     = df.apply(lambda row: calculer_cout_potion(row, _ingredients), axis=1)
    df["prix"]     = pd.to_numeric(df["prix"], errors="coerce").fillna(0)
    df["benefice"] = df["prix"] - df["cout"]

    # Jointure potions-inventeurs
    df = df.merge(_pot_inv[["potion", "type_magie_potion", "inventeur"]],
                  on="potion", how="left")
    df["inventeur"]         = df["inventeur"].fillna("Inconnu")
    df["type_magie_potion"] = df["type_magie_potion"].fillna("Inconnu")

    # Jointure inventeurs → lignée
    df = df.merge(
        _inventeurs[["pseudo", "lignee"]],
        left_on="inventeur", right_on="pseudo",
        how="left"
    )
    df["lignee"] = df["lignee"].fillna("Inconnue")

    # Jointure types de magie → compétences
    df = df.merge(
        _magies[["type_de_magie", "competences"]],
        left_on="type_magie_potion", right_on="type_de_magie",
        how="left"
    )
    df["competences"] = df["competences"].fillna("Inconnue")

    return df

# ============================================================
# GRAPHIQUES
# ============================================================

def graph_top10_potions(df):
    """Bar chart horizontal — Top 10 potions les plus rentables."""
    top10 = (
        df[["potion", "benefice", "type_magie_potion"]]
        .sort_values("benefice", ascending=False)
        .head(10)
        .sort_values("benefice", ascending=True)
    )
    couleurs = [COULEURS_MAGIE.get(t, "#95A5A6") for t in top10["type_magie_potion"]]

    fig = go.Figure(go.Bar(
        x=top10["benefice"],
        y=top10["potion"],
        orientation="h",
        marker=dict(color=couleurs, line=dict(width=0)),
        text=[f"{v:,.0f} 🪙" for v in top10["benefice"]],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Bénéfice : %{x:,.0f} 🪙<extra></extra>",
    ))
    fig.update_layout(
        title="🏆 Top 10 des Potions les plus Rentables",
        xaxis_title="Bénéfice (pièces d'or)",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0.05)",
        font=dict(color="white"),
        height=450,
        margin=dict(l=200, r=80),
        xaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
    )
    return fig


def graph_sunburst(df, magies):
    """Sunburst 2 niveaux : type de magie → compétence (sans les potions)."""
    rows = []
    for _, row in df.iterrows():
        type_magie      = row["type_magie_potion"] if not pd.isna(row["type_magie_potion"]) else "Inconnu"
        competences_raw = row["competences"]        if not pd.isna(row["competences"])        else "Inconnue"

        competences = [c.strip() for c in str(competences_raw).split(";")]
        for comp in competences:
            rows.append({
                "type_magie": type_magie,
                "competence": comp,
            })

    sun_df = pd.DataFrame(rows)

    # Agrégation : nombre de potions par couple type_magie / compétence
    sun_df = (
        sun_df.groupby(["type_magie", "competence"])
        .size()
        .reset_index(name="valeur")
    )

    couleur_map = {t: c for t, c in COULEURS_MAGIE.items()}

    fig = px.sunburst(
        sun_df,
        path=["type_magie", "competence"],
        values="valeur",
        color="type_magie",
        color_discrete_map=couleur_map,
        title="🌀 Répartition des Potions : Type de Magie → Compétence",
    )
    fig.update_traces(
        textfont=dict(size=12),
        hovertemplate="<b>%{label}</b><br>Potions : %{value}<extra></extra>",
        insidetextorientation="radial",
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        height=600,
    )
    return fig


def graph_kiviat(df):
    """Kiviat — nombre de potions par compétence."""
    comp_counter = Counter()
    for _, row in df.iterrows():
        competences_raw = row["competences"] if not pd.isna(row["competences"]) else "Inconnue"
        for comp in str(competences_raw).split(";"):
            comp_counter[comp.strip()] += 1

    if not comp_counter:
        return go.Figure()

    labels = list(comp_counter.keys())
    values = list(comp_counter.values())
    # Fermeture du polygone
    labels_closed = labels + [labels[0]]
    values_closed = values + [values[0]]

    fig = go.Figure(go.Scatterpolar(
        r=values_closed,
        theta=labels_closed,
        fill="toself",
        fillcolor="rgba(46,134,222,0.25)",
        line=dict(color="#2E86DE", width=2),
        hovertemplate="<b>%{theta}</b><br>Potions : %{r}<extra></extra>",
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                color="rgba(255,255,255,0.5)",
                gridcolor="rgba(255,255,255,0.15)",
            ),
            angularaxis=dict(
                color="white",
                gridcolor="rgba(255,255,255,0.15)",
            ),
            bgcolor="rgba(0,0,0,0.1)",
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        title="🕸️ Kiviat : Nombre de Potions par Compétence",
        height=500,
        showlegend=False,
    )
    return fig


def graph_heatmap_cooccurrence(df):
    """Heatmap de cooccurrence des ingrédients."""
    recettes_ingredients = {}
    for _, row in df.iterrows():
        potion = row["potion"]
        ings   = []
        for i in range(1, 5):
            ing = row.get(f"ingredient_{i}")
            if not pd.isna(ing) and str(ing).strip() not in ("", "nan"):
                ings.append(normalise(str(ing).strip()))
        if ings:
            recettes_ingredients[potion] = ings

    all_ings = sorted(set(
        ing for ings in recettes_ingredients.values() for ing in ings
    ))
    cooc = pd.DataFrame(0, index=all_ings, columns=all_ings)

    for ings in recettes_ingredients.values():
        for a, b in combinations(set(ings), 2):
            cooc.loc[a, b] += 1
            cooc.loc[b, a] += 1
        for a in ings:
            cooc.loc[a, a] += 1

    fig = go.Figure(go.Heatmap(
        z=cooc.values,
        x=cooc.columns.tolist(),
        y=cooc.index.tolist(),
        colorscale="Blues",
        hovertemplate="<b>%{y}</b> + <b>%{x}</b><br>Cooccurrences : %{z}<extra></extra>",
    ))
    fig.update_layout(
        title="🔥 Heatmap de Cooccurrence des Ingrédients",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white", size=10),
        height=650,
        xaxis=dict(tickangle=-45),
    )
    return fig


def graph_reseau(df, inventeurs):
    """Graphe réseau inventeurs ↔ potions."""
    G = nx.Graph()

    nb_potions_inv = df.groupby("inventeur")["potion"].count().to_dict()
    
    # ✅ FIX : Ajouter SEULEMENT les inventeurs qui ont des potions
    inventeurs_actifs = df[df["inventeur"] != "Inconnu"]["inventeur"].unique()
    
    for inv_nom in inventeurs_actifs:
        # Chercher les infos dans le dataframe inventeurs
        match = inventeurs[inventeurs["pseudo"].apply(normalise) == inv_nom]
        
        if not match.empty:
            lignee = nettoyer_lignee(match.iloc[0]["lignee"])
        else:
            lignee = "Inconnue"
        
        nb = nb_potions_inv.get(inv_nom, 0)
        G.add_node(inv_nom,
                   type="inventeur",
                   lignee=lignee,
                   nb_potions=nb,
                   color=COULEURS_LIGNEE.get(lignee, "#95A5A6"))
    
    # Gérer le cas "Inconnu"
    if "Inconnu" in df["inventeur"].values:
        nb_inconnu = nb_potions_inv.get("Inconnu", 0)
        if nb_inconnu > 0:  # ✅ Ajouter seulement s'il y a des potions
            G.add_node("Inconnu", type="inventeur", lignee="Inconnue",
                       nb_potions=nb_inconnu,
                       color="#95A5A6")

    # Nœuds potions + arêtes
    for _, row in df.iterrows():
        potion    = row["potion"]
        inventeur = row["inventeur"]
        type_mag  = row["type_magie_potion"]

        if not G.has_node(potion):
            G.add_node(potion,
                       type="potion",
                       type_magie=type_mag,
                       color=COULEURS_MAGIE.get(type_mag, "#95A5A6"))
        G.add_edge(inventeur, potion)

    pos = nx.spring_layout(G, seed=42, k=2.5)

    # ─── Reste du code identique ───
    edge_x, edge_y = [], []
    for u, v in G.edges():
        x0, y0 = pos[u]; x1, y1 = pos[v]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        mode="lines",
        line=dict(width=0.5, color="rgba(255,255,255,0.2)"),
        hoverinfo="none",
    )

    # Nœuds inventeurs
    inv_nodes  = [n for n, d in G.nodes(data=True) if d.get("type") == "inventeur"]
    inv_x      = [pos[n][0] for n in inv_nodes]
    inv_y      = [pos[n][1] for n in inv_nodes]
    inv_colors = [G.nodes[n]["color"] for n in inv_nodes]
    inv_sizes  = [max(15, G.nodes[n].get("nb_potions", 1) * 5) for n in inv_nodes]
    inv_texts  = [
        f"<b>🧙 {n}</b><br>Lignée : {G.nodes[n].get('lignee','?')}"
        f"<br>Potions : {G.nodes[n].get('nb_potions',0)}"
        for n in inv_nodes
    ]
    inv_trace = go.Scatter(
        x=inv_x, y=inv_y,
        mode="markers",
        marker=dict(
            size=inv_sizes,
            color=inv_colors,
            symbol="diamond",
            line=dict(width=1, color="white"),
        ),
        hovertext=inv_texts,
        hoverinfo="text",
        name="Inventeurs",
    )

    # Nœuds potions
    pot_nodes  = [n for n, d in G.nodes(data=True) if d.get("type") == "potion"]
    pot_x      = [pos[n][0] for n in pot_nodes]
    pot_y      = [pos[n][1] for n in pot_nodes]
    pot_colors = [G.nodes[n]["color"] for n in pot_nodes]
    pot_texts  = [
        f"<b>🧪 {n}</b><br>Magie : {G.nodes[n].get('type_magie','?')}"
        for n in pot_nodes
    ]
    pot_trace = go.Scatter(
        x=pot_x, y=pot_y,
        mode="markers",
        marker=dict(
            size=10,
            color=pot_colors,
            line=dict(width=1, color="rgba(255,255,255,0.3)"),
        ),
        hovertext=pot_texts,
        hoverinfo="text",
        name="Potions",
    )

    fig = go.Figure(data=[edge_trace, inv_trace, pot_trace])
    fig.update_layout(
        title="🕸️ Réseau Inventeurs ↔ Potions",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0.05)",
        font=dict(color="white"),
        height=700,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        legend=dict(
            bgcolor="rgba(0,0,0,0.3)",
            bordercolor="rgba(255,255,255,0.2)",
            borderwidth=1,
        ),
    )
    return fig


# ============================================================
# SIDEBAR
# ============================================================
def sidebar(df):
    st.sidebar.markdown("## ⚗️ Filtres Magiques")

    types_magie      = ["Tous"] + sorted(df["type_magie_potion"].dropna().unique().tolist())
    filtre_magie     = st.sidebar.selectbox("🔮 Type de Magie", types_magie)

    inventeurs_liste = ["Tous"] + sorted(df["inventeur"].dropna().unique().tolist())
    filtre_inventeur = st.sidebar.selectbox("🧙 Inventeur", inventeurs_liste)

    ben_min = int(df["benefice"].min())
    ben_max = int(df["benefice"].max())
    filtre_benefice = st.sidebar.slider(
        "💰 Bénéfice minimum (pièces d'or)",
        min_value=ben_min,
        max_value=ben_max,
        value=ben_min,
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 Statistiques rapides")
    st.sidebar.metric("Total Potions",     len(df))
    st.sidebar.metric("Inventeurs actifs", df[df["inventeur"] != "Inconnu"]["inventeur"].nunique())
    st.sidebar.metric("Bénéfice moyen",    f"{df['benefice'].mean():,.0f} 🪙")
    st.sidebar.markdown("---")
    st.sidebar.caption("py-potion-craft-BOTELLA | Archives Magiques")

    return filtre_magie, filtre_inventeur, filtre_benefice


def appliquer_filtres(df, filtre_magie, filtre_inventeur, filtre_benefice):
    df_f = df.copy()
    if filtre_magie != "Tous":
        df_f = df_f[df_f["type_magie_potion"] == filtre_magie]
    if filtre_inventeur != "Tous":
        df_f = df_f[df_f["inventeur"] == filtre_inventeur]
    df_f = df_f[df_f["benefice"] >= filtre_benefice]
    return df_f

# ============================================================
# APPLICATION PRINCIPALE
# ============================================================
def main():
    with st.spinner("Chargement du grimoire numérique..."):
        recettes, ingredients, inventeurs, magies, pot_inv = charger_donnees()
        df = construire_dataframe_principal(
            recettes, ingredients, inventeurs, magies, pot_inv
        )

    st.markdown(
        '<h1 class="main-title">⚗️ Archives Magiques — Potion Craft</h1>',
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align:center;color:#95A5A6;'>"
        "Département des Archives Magiques du Ministère · py-potion-craft-BOTELLA"
        "</p>",
        unsafe_allow_html=True,
    )

    filtre_magie, filtre_inventeur, filtre_benefice = sidebar(df)
    df_filtre = appliquer_filtres(df, filtre_magie, filtre_inventeur, filtre_benefice)

    if df_filtre.empty:
        st.warning("⚠️ Aucune potion ne correspond aux filtres sélectionnés.")
        return

    # ── KPI ─────────────────────────────────────────────────
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🧪 Potions affichées", len(df_filtre))
    col2.metric("💰 Bénéfice total",    f"{df_filtre['benefice'].sum():,.0f} 🪙")
    col3.metric("📈 Bénéfice max",      f"{df_filtre['benefice'].max():,.0f} 🪙")
    col4.metric("📉 Bénéfice min",      f"{df_filtre['benefice'].min():,.0f} 🪙")
    st.markdown("---")

    # ── SECTION 1 : TOP 10 ──────────────────────────────────
    st.markdown('<p class="section-title">🏆 Top 10 des Potions les plus Rentables</p>',
                unsafe_allow_html=True)
    st.plotly_chart(graph_top10_potions(df_filtre), use_container_width=True)

    # ── SECTION 2 : SUNBURST ────────────────────────────────
    st.markdown("---")
    st.markdown('<p class="section-title">🌀 Sunburst : Répartition par Type de Magie</p>',
                unsafe_allow_html=True)
    st.plotly_chart(graph_sunburst(df_filtre, magies), use_container_width=True)

    # ── SECTION 3 : KIVIAT ──────────────────────────────────
    st.markdown("---")
    st.markdown('<p class="section-title">🕸️ Kiviat : Potions par Compétence</p>',
                unsafe_allow_html=True)
    st.plotly_chart(graph_kiviat(df_filtre), use_container_width=True)

    # ── SECTION 4 : HEATMAP ─────────────────────────────────
    st.markdown("---")
    st.markdown('<p class="section-title">🔥 Heatmap de Cooccurrence des Ingrédients</p>',
                unsafe_allow_html=True)
    st.info("ℹ️ La diagonale représente la fréquence d'utilisation individuelle d'un ingrédient.")
    st.plotly_chart(graph_heatmap_cooccurrence(df_filtre), use_container_width=True)

    # ── SECTION 5 : RÉSEAU ──────────────────────────────────
    st.markdown("---")
    st.markdown('<p class="section-title">🌐 Réseau Inventeurs ↔ Potions</p>',
                unsafe_allow_html=True)
    st.info("💎 Les losanges = inventeurs (taille = nb potions) · Les cercles = potions (couleur = type de magie).")
    st.plotly_chart(graph_reseau(df, inventeurs), use_container_width=True)

    # ── SECTION 6 : TABLEAU ─────────────────────────────────
    st.markdown("---")
    st.markdown('<p class="section-title">📋 Tableau Détaillé des Potions</p>',
                unsafe_allow_html=True)

    cols_ok = [c for c in [
        "potion", "prix", "cout", "benefice",
        "type_magie_potion", "competences",
        "inventeur", "lignee",
    ] if c in df_filtre.columns]

    st.dataframe(
        df_filtre[cols_ok].sort_values("benefice", ascending=False),
        use_container_width=True,
        hide_index=True,
    )

    csv = df_filtre[cols_ok].to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Télécharger les données filtrées (CSV)",
        data=csv,
        file_name="potions_filtrees.csv",
        mime="text/csv",
    )


if __name__ == "__main__":
    main()
