# 🗄️ DB Manager — Gestionnaire SQLite

Application desktop Python pour créer et gérer des bases de données SQLite.

## Prérequis

- Python 3.8 ou supérieur
- Tkinter (inclus par défaut avec Python sur Windows/macOS)

### Installation de Tkinter sur Linux (si absent)

```bash
# Ubuntu / Debian
sudo apt-get install python3-tk

# Fedora
sudo dnf install python3-tkinter
```

## Lancement

```bash
python app.py
```

Aucune dépendance externe requise — uniquement la bibliothèque standard Python.

---

## Fonctionnalités

### Gestion des bases de données
- **Créer** une nouvelle base SQLite (`.db`)
- **Ouvrir** une base existante
- **Fermer** la base active

### Gestion des tables
- **Créer** une table avec colonnes personnalisées (nom, type, PK, NOT NULL)
- **Renommer** une table
- **Supprimer** une table
- **Voir le schéma** complet (colonnes, types, contraintes, SQL de création)

### Gestion des données (onglet Données)
- **Ajouter** une ligne via formulaire
- **Modifier** une ligne (double-clic ou bouton)
- **Supprimer** une ligne
- **Rechercher** dans toutes les colonnes
- **Pagination** (100 lignes par page)

### Éditeur SQL (onglet SQL)
- Éditeur de requêtes avec coloration monospace
- **Exécuter** avec `F5` ou `Ctrl+Entrée`
- Résultats affichés en tableau
- **Historique** des requêtes exécutées

### Import / Export CSV
- **Exporter** une table en fichier `.csv`
- **Importer** des lignes depuis un fichier `.csv`

---

## Structure du code

```
app.py
├── COLORS               — Palette de couleurs
├── DatabaseManager      — Couche d'accès SQLite
├── StyledButton         — Bouton personnalisé
├── LabeledEntry         — Champ avec label
├── CreateTableDialog    — Dialogue création de table
├── RowDialog            — Dialogue ajout/édition de ligne
├── DataPanel            — Vue données + CRUD + CSV
├── SQLPanel             — Éditeur SQL + résultats
├── SchemaPanel          — Vue schéma de la table
└── App                  — Fenêtre principale + navigation
```

---

## Types de colonnes supportés

| Type    | Description              |
|---------|--------------------------|
| INTEGER | Entier                   |
| TEXT    | Chaîne de caractères     |
| REAL    | Nombre décimal           |
| BLOB    | Données binaires         |
| NUMERIC | Numérique flexible       |

---

## Raccourcis clavier

| Raccourci      | Action                          |
|----------------|---------------------------------|
| `Ctrl+N`       | Nouvelle base de données        |
| `Ctrl+O`       | Ouvrir une base                 |
| `Ctrl+T`       | Nouvelle table                  |
| `F5`           | Exécuter la requête SQL         |
| `Ctrl+Entrée`  | Exécuter la requête SQL         |
