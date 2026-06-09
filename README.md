#  Potion Craft — Atelier Reporting & Datavisualisation

Tableau de bord interactif d'analyse du catalogue de potions du **Département des Archives Magiques du Ministère**.

##  Équipe
- Guillaume BOTELLA

##  Objectif
Transformer un grimoire numérique désorganisé (fichiers Excel multi-feuilles) en un **rapport interactif Streamlit** permettant d'analyser :
- la rentabilité des potions,
- la répartition par type de magie et compétence,
- les compétences les plus exploitées,
- les cooccurrences d'ingrédients,
- le réseau inventeurs / potions.

##  Lancement

```bash
# 1. Cloner le repo
git clone https://github.com/<user>/py-potion-craft-BOTELLA.git
cd py-potion-craft-BOTELLA

# 2. Créer un environnement virtuel
python -m venv env
# Windows
env\Scripts\activate
# Linux/Mac
source env/bin/activate

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Lancer l'application
streamlit run potion_craft.py
```

##  Choix technologiques

| Besoin | Technologie | Justification |
|---|---|---|
| Manipulation des données | **Pandas** | Standard de l'écosystème Python, parfait pour ces volumes modestes (~40 lignes), excellente gestion de l'Excel multi-feuilles via `openpyxl`. |
| Visualisations interactives | **Plotly Express / Graph Objects** | Intégration native avec Streamlit, interactivité (hover, zoom) sans configuration. Sunburst, Radar (Scatterpolar) et Heatmap sont prêts à l'emploi. |
| Graphe de réseau | **NetworkX + Plotly** | NetworkX pour le layout (`spring_layout`), Plotly pour le rendu interactif (hover, taille variable). |
| Dashboard | **Streamlit** | Imposé par le sujet, idéal pour un POC : sidebar de filtres, mise en page en colonnes, cache des données via `@st.cache_data`. |

##  Nettoyage des données

- Normalisation des **apostrophes typographiques** (`’` → `'`).
- Correction des **variantes de lignées** (ex. `Bl'ack` → `Black`).
- Gestion des **inventeurs manquants** via un nœud **Inconnu** dans le graphe.
- Strip systématique des espaces dans les noms de colonnes (le fichier source contient `quantite_ 2` avec un espace parasite).
- **Conversion des unités** vers la pincée à partir de la table `unites.xlsx` :
  - 1 Soufle = 7 Pincées
  - 1 Nuage = 5 Soufles = 35 Pincées
  - 1 Poignée = 3 Nuages = 105 Pincées
  - 1 Once = 2 Poignées = 210 Pincées

##  Calcul de rentabilité

```
coût  = Σ (quantité_en_pincées × prix_unitaire_ingrédient)
bénéfice = prix_de_vente − coût
```

Le diluant n'est pas comptabilisé (non listé dans les ingrédients).

##  Sections du tableau de bord

1. **Top 10 des potions les plus rentables** — bar chart horizontal coloré par type de magie.
2. **Sunburst à 3 niveaux** — type de magie → compétence → potion.
3. **Kiviat des compétences** — nombre de potions par compétence.
4. **Heatmap de cooccurrence** — matrice symétrique des ingrédients partagés.
5. **Graphe inventeurs ↔ potions** — taille = productivité, couleur = lignée.

##  Structure du projet

```
Potion_Craft/
├── potion_craft.py
├── requirements.txt
├── README.md
├── liste-ingredients.xlsx
├── liste-inventeurs.xlsx
├── liste-types-de-magie.xlsx
├── potions.xlsx
├── potions-craft.xlsx
├── potions-inventeurs.xlsx
└── unites.xlsx
```

##  Améliorations possibles
- Export PDF des graphiques.
- Détection automatique des anomalies orthographiques (fuzzy matching).
- Recommandation de recettes optimales par algorithme génétique.
- Authentification multi-utilisateurs.
