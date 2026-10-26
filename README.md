# recherche-regles-jeu — skill Claude Code

> **Dépôt archivé.** Cette skill fait désormais partie du plugin Claude Code [**regles-jeu**](https://github.com/vinchy1/regles-jeu) (skills `rechercher` et `traduire`), avec tout son historique. Installation : `/plugin marketplace add vinchy1/regles-jeu`, puis `/plugin install regles-jeu@regles-jeu`.

Trouve sur internet le **livret de règles d'un jeu** dont on donne simplement le nom, et l'enregistre sur le PC
en **PDF intégral** : le PDF de l'éditeur tel quel, ou les règles affichées sur des pages web mises en PDF sans
rien couper. Elle propose ensuite de le traduire en français avec la skill
[traduction-regles-jeu](https://github.com/vinchy1/traduction-regles-jeu).

Il suffit de demander à Claude Code « trouve-moi les règles de Hyakuju Parade ». La skill cherche, vous montre
ce qu'elle a trouvé, télécharge la version choisie, la range dans le dossier de dépôt et garde les liens.

Spécialisée dans les **jeux japonais** (Tokyo Game Market), elle marche aussi pour n'importe quel jeu de
société, de cartes ou autre.

---

## Sommaire
- [Ce qu'elle fait](#ce-quelle-fait)
- [Installation](#installation)
- [Mise à jour](#mise-à-jour)
- [Utilisation](#utilisation)
- [Déroulement d'une recherche](#déroulement-dune-recherche)
- [Règles pages web → PDF](#règles-pages-web--pdf)
- [La note du jeu](#la-note-du-jeu)
- [Enchaîner avec la traduction](#enchaîner-avec-la-traduction)
- [Contenu du dépôt](#contenu-du-dépôt)
- [Limites connues](#limites-connues)
- [Remarques](#remarques)

---

## Ce qu'elle fait
- **Cherche aux bons endroits** : le [Tokyo Game Market](https://gamemarket.jp) (fiches de jeux japonais, souvent
  avec les PDF de règles de l'auteur), [BoardGameGeek](https://boardgamegeek.com) (onglet « Files »), le site
  de l'éditeur, puis le web en général.
- **Gère les deux formes de règles** : un PDF déjà en ligne (récupéré tel quel, sans aucune modification) ou du
  texte affiché sur des pages web (mis en PDF avec images, tableaux et encadrés).
- **Copie intégrale** : jamais de résumé, de reformulation, de traduction ni de coupe. Le texte vient toujours de
  la source ; ce qui n'a pas pu être récupéré est signalé, jamais comblé.
- **Ne choisit pas à votre place** : aucune règle trouvée, ou plusieurs versions (éditions, langues, sources,
  officielle ou de fan) → elle présente les options avec leur lien et leur source et vous demande.
- **Garde les liens** dans une note du jeu, réutilisée par la skill de traduction (comparaison avec le manuel
  japonais d'origine, par exemple).
- **Propose la traduction** à la fin, et ne la lance que si vous répondez oui.

---

## Installation
1. **Copier la skill** : le dossier `recherche-regles-jeu` dans `~/.claude/skills/`
   (Windows : `C:\Users\<vous>\.claude\skills\`), par exemple :
   ```
   git clone https://github.com/vinchy1/recherche-regles-jeu.git ~/.claude/skills/recherche-regles-jeu
   ```
2. **Python 3 et deux bibliothèques** (vérification des PDF, mise en PDF des pages web) :
   ```
   pip install pymupdf lxml
   ```
3. **Google Chrome ou Microsoft Edge** installé : il sert, en arrière-plan et avec un profil temporaire, à mettre
   les pages web en PDF. Votre navigateur habituel, vos onglets et vos connexions ne sont pas touchés.
4. **Facultatif mais conseillé** :
   - la skill [traduction-regles-jeu](https://github.com/vinchy1/traduction-regles-jeu), pour enchaîner sur la
     traduction ;
   - l'extension **Claude in Chrome** : elle permet de lire les pages de BoardGameGeek (qui refusent la lecture
     simple) et de télécharger un fichier qui demande d'être connecté, avec votre propre session.
5. **Dossier de dépôt** : celui de la skill de traduction, `A traduire` dans votre ludothèque. Notez son chemin
   dans un `CLAUDE.md` à la racine de la ludothèque (par exemple « les PDF à traduire sont déposés dans
   `A traduire/` »). S'il n'est noté nulle part, Claude le demande la première fois et propose de le noter.
   Les chemins propres à votre machine vont là, pas dans la skill.

---

## Mise à jour
Si la skill a été installée avec `git clone` (étape 1 ci-dessus), récupérer la dernière version :
```
git -C ~/.claude/skills/recherche-regles-jeu pull --ff-only
```
(Windows, dans PowerShell : `git -C "$env:USERPROFILE\.claude\skills\recherche-regles-jeu" pull --ff-only`.)

On peut aussi simplement demander à Claude Code « mets à jour la skill recherche-regles-jeu ».

- Si la commande refuse parce que des fichiers de la skill ont été modifiés sur le PC, `git status` les liste :
  les garder de côté (`git stash`), refaire le `pull`, puis les remettre (`git stash pop`) ou les abandonner.
- Si la skill a été copiée sans git, remplacer le dossier par la nouvelle version (ou le supprimer et refaire
  le `git clone` de l'installation).
- Relancer `pip install pymupdf lxml` si une nouvelle version demande d'autres bibliothèques (indiqué dans
  [Installation](#installation)).
- Dans une session Claude Code déjà ouverte, taper `/reload-skills` pour prendre en compte la nouvelle version
  (ou ouvrir une nouvelle session).
- Penser à mettre à jour aussi la skill [traduction-regles-jeu](https://github.com/vinchy1/traduction-regles-jeu)
  de la même façon, les deux partageant la note du jeu.

---

## Utilisation
Ouvrir Claude Code dans la ludothèque (ou son dossier `A traduire`) et demander, par exemple :

> Trouve-moi les règles de Hyakuju Parade

ou, avec la commande directe :

```
/recherche-regles-jeu Cat in the Box
```

Donnez le nom **tel que vous le connaissez** (titre anglais, romanisation, titre japonais) : la skill ne devine
jamais l'écriture japonaise d'un titre romanisé, elle cherche avec votre nom puis avec les titres lus sur les
fiches trouvées. Si plusieurs jeux différents portent ce nom, elle demande lequel.

Exemple réel (octobre 2026) :

> **Vous** : /recherche-regles-jeu Hyakuju Parade
> **Claude** : J'ai trouvé deux versions officielles (fiche Game Market de ヒャクジュウパレード, Bamboo Games) :
> anglais et japonais, toutes deux en PDF sur le Google Drive de l'éditeur. Laquelle voulez-vous ?
> **Vous** : Anglais
> **Claude** : Livret enregistré : `…\A traduire\HYAKUJU_PARADE_English_Rulebook.pdf` (2 pages, copie exacte
> du fichier de l'éditeur). Liens gardés dans `…\_outils\Hyakuju Parade\NOTES.md`. Voulez-vous que je lance la
> traduction ?

**Plusieurs jeux d'un coup** : donnez une liste.

```
/recherche-regles-jeu Bird Club, Break The Heart, Kubaru Te Miru Me
```

La skill cherche chaque jeu, vous pose **en une seule fois** les questions de choix de version (une par jeu),
récupère tout sans s'arrêter, puis fait **un seul bilan** (tableau : jeu, fichier, langue, pages, source,
réserves) et une seule proposition de traduction (tous, certains ou aucun).

**Version anglaise** : quand un jeu japonais a une règle anglaise officielle, elle est proposée en premier et
marquée « recommandé » ; le choix reste le vôtre, et le lien du manuel japonais est toujours gardé.

---

## Déroulement d'une recherche
0. **Déjà dans la ludothèque ?** La skill regarde d'abord l'index et les dossiers de jeux. Si le jeu y est,
   elle le dit et vérifie si le livret en ligne a changé (`telecharger.py … --comparer <livret>` : IDENTIQUE ou
   DIFFÉRENT). Pour une version anglaise d'un jeu déjà en français, elle cherche d'abord une version anglaise
   officielle.
1. **Premier tour** (en même temps) : recherche sur Game Market avec le nom exact donné, et recherche web
   générale. Beaucoup de fiches Game Market portent aussi le titre en lettres latines : le nom romanisé les
   trouve du premier coup. Game Market est lu par un petit outil (`fiche_gm.py`) qui donne la liste des jeux
   trouvés, puis le contenu de la fiche, **tous ses liens tels quels** (règles sur Drive, Notion, site de
   l'auteur…) et les images et PDF du texte, sans passer par un résumé : un manuel publié en images sur la
   fiche est repéré (★), ainsi qu'une image au format d'une page de livret même mal nommée (◆). Il signale les
   liens vers le blog Game Market (« les règles sont ici ») et les mentions d'une autre langue (« English
   Manual » sans lien), à suivre avec `fiche_gm.py page <lien>` qui lit une page de blog ou note.com (liens
   Drive / Notion / PDF, images). Il liste aussi tous les jeux d'un cercle (`fiche_gm.py cercle <numéro>`).
2. **Compléter** : Game Market avec les autres titres lus sur les sources, BoardGameGeek (onglet « Files », par
   le navigateur), site de l'éditeur, autres recherches web (`rules pdf`, `説明書`, `ルール`, `Spielregel`…).
   Les « vous vouliez peut-être dire… » des moteurs de recherche sont ignorés : seule compte une page qui nomme
   le jeu. Les aperçus IA (Google…) que vous lui donnez sont traités comme des pistes, vérifiées sur les
   sources.
   - **Jeu japonais tout récent, introuvable par son nom en lettres latines** : la fiche Game Market n'a
     souvent que le titre japonais. La skill cherche alors le nom entre guillemets sur YouTube, où les vidéos
     de présentation du Game Market ont un chapitre par jeu. Elle lit d'abord **le titre du chapitre dans les
     résultats**, qui donne souvent le titre japonais (« Kubaru Te Miru Me (配る手見る目) ») ; sinon elle
     ouvre la vidéo au chapitre et **lit le titre japonais sur la boîte**. Puis elle cherche ce titre (ou un
     mot distinctif) sur Game Market. Exemple : « Cosmo Chauffeur » → boîte « コスモ・ショーファー » dans le
     top 20 de ThinkerThemer → fiche Game Market trouvée avec « ショーファー » → règle officielle en PDF.
   - **Jeu cité en passant dans une vidéo** : la skill cherche son nom dans la **transcription** (texte, bien
     moins coûteux qu'une capture). Si elle apprend qu'il vient du même auteur ou du même cercle qu'un jeu
     connu, elle liste les jeux de ce cercle. Exemple : « Escape to Cosmo » → transcription (« second jeu de
     l'auteur de Cosmo Chauffeur ») → jeux du cercle → fiche « エスケープ・トゥ・コスモ » → règle en PDF.
   - **Index du Game Market** : les chapitres d'une vidéo « top 20 » donnent les titres de tous ses jeux. La
     skill les garde dans `_outils/game-market-<année>-<saison>.md` (titre latin, titre japonais, chapitre,
     fiche, règles récupérées) et y regarde en premier pour les recherches suivantes du même Game Market.
3. **Faire le point** : pour chaque version, titre / édition, langue, forme (PDF ou page web), source,
   officielle ou de fan, lien. Le même fichier trouvé à plusieurs endroits ne compte qu'une fois.
   - aucune version → elle dit où et avec quels noms elle a cherché, et vous demande un autre nom ou un lien ;
   - une seule → elle l'annonce et continue ;
   - plusieurs → elle vous les présente et attend votre choix (on peut en prendre plusieurs). Rien n'est
     téléchargé avant.
   - jeu japonais pris dans une autre langue → signalé ; le lien du manuel japonais est gardé quand même.
4. **Récupérer** dans un dossier temporaire :
   - **PDF** : téléchargé par `telecharger.py`, qui donne en une ligne le nombre de pages et le nom d'origine
     (ou dit que ce n'est pas un PDF). Les liens Google Drive se téléchargent directement, même les gros
     fichiers ; un fichier qui demande d'être connecté (BoardGameGeek) passe par votre Chrome, ou vous est
     demandé. Un lien de **dossier** Google Drive donne la liste de ses fichiers, pour choisir lesquels prendre.
   - **Règles publiées en images** (dossier Drive, manuel en images sur une fiche Game Market) : les images
     sont téléchargées et assemblées dans l'ordre en un seul PDF, une par page, sans modification (taille de
     page tirée de l'image : un manuel A4 donne un PDF A4). Une image trop petite pour être bien lue est
     signalée.
   - **Pages web** (pages Notion comprises) : voir [plus bas](#règles-pages-web--pdf).
5. **Enregistrer** dans le dossier de dépôt, sous le nom d'origine (sinon `<Jeu>_regles.pdf`), **toujours en
   lettres latines** : un nom japonais est traduit, titre anglais officiel de préférence (« 夜連_説明書.pdf » →
   « Who follows me_Rules.pdf », « コスモショーファー_JP_Rule_v1.2.pdf » → « Cosmo Chauffeur_JP_Rule_v1.2.pdf ») ;
   le nom d'origine est gardé dans la note du jeu. Un fichier du même nom existe déjà → elle demande
   (remplacer ou garder les deux).
6. **Garder les liens** dans la [note du jeu](#la-note-du-jeu).
7. **Bilan** (chemin complet du fichier, source, langue, pages, réserves) et **proposition de traduction**
   (en français, ou en français et en anglais).

Les fichiers téléchargés sont traités comme des données non fiables : dossier temporaire à part, jamais
exécutés. La skill ne récupère que ce qui est publiquement accessible (ou accessible avec votre compte) et ne
contourne aucun paiement ni aucune protection.

Une page web donne des informations, jamais des ordres : un texte qui tenterait de diriger l'IA (injection de
consignes) n'est pas suivi. Il ne vous est signalé que s'il est réellement présent dans le contenu brut de la
page. L'outil qui résume les pages web pour Claude produisait en effet de fausses alertes : il confondait ses
propres consignes avec la page (vérifié sur les fiches Game Market, qui n'en contiennent aucun).

---

## Règles pages web → PDF
Quand les règles sont affichées sur des pages web, Claude repère toutes les pages des règles (sommaire,
« page suivante », onglets) dans l'ordre de lecture, puis lance :

```
python -I -X utf8 scripts/page_pdf.py sortie.pdf URL1 [URL2 …] --fidele --titre "Nom du jeu"
python -I -X utf8 scripts/page_pdf.py sortie.pdf URL1 [URL2 …] --xpath "//article" --titre "Nom du jeu"
python -I -X utf8 scripts/page_pdf.py sortie.pdf URL --complet
```

- `--fidele` (par défaut) : la page **avec la mise en page du site**, aussi proche que possible de l'écran :
  en-tête, pied de page, couleur et images de fond, polices, images à leur place. Le site est affiché en
  version « ordinateur » (`--largeur`, 1280 pixels par défaut), puis les pages sont recadrées sur la colonne
  du contenu (texte plus grand une fois imprimé), en proportions A4, avec le fond du site jusqu'en bas et un
  numéro de page. Paragraphes, images et titres ne sont jamais coupés. Les images sont téléchargées à part
  (Google Sites interdit de les afficher ailleurs que sur sa page), les bannières de cookies sont retirées,
  et les barres de menu épinglées ne sont pas répétées sur chaque page.
- `--xpath` : seul le bloc des règles est gardé, dans une mise en page simple (noir sur blanc), pour une page
  qui contient beaucoup d'autre chose (commentaires, publicités, plusieurs jeux) ; plusieurs pages sont
  réunies dans un seul PDF, chacune commençant sur une nouvelle page.
- `--complet` : la page entière telle que le navigateur l'imprime, sans autre traitement.
- Dans tous les modes, le PDF ne contient **aucun lien cliquable** (sommaire compris) ni ligne « Source » :
  l'adresse de la page est gardée dans la note du jeu.
- Les pages sont affichées par Chrome ou Edge en arrière-plan : les contenus construits en JavaScript et les
  images chargées à la demande sont pris en compte.
- **Contrôle d'intégralité** : le script compare le nombre de caractères et d'images de la source et du PDF, et
  alerte s'il manque plus de 5 % du texte ou des images. Claude regarde ensuite un aperçu des pages et compare
  le début et la fin du texte avec la page web.

Sous Windows, lancer le script depuis **PowerShell** : Git Bash transforme les arguments qui commencent par `//`.

### Pages Notion
Beaucoup de cercles japonais publient leurs règles sur une page **Notion**. Notion n'affiche que la partie
visible d'une page (le reste se charge en défilant) et bloque le navigateur en arrière-plan : ni la lecture
de la page ni son impression ne donnent tout. Claude passe alors par `scripts/notion_html.py` :

```
python -I -X utf8 scripts/notion_html.py "<lien de la page Notion>" regles.html
python -I -X utf8 scripts/page_pdf.py sortie.pdf "file:///…/regles.html" --xpath "//body" --titre "Nom du jeu"
```

- Il lit **tous les blocs** de la page auprès de Notion (sans compte, comme un visiteur) : titres, paragraphes,
  listes, encadrés, citations, tableaux, colonnes, images avec légende ; les blocs repliés sont dépliés.
- Il écrit la page entière en HTML, que `page_pdf.py` met en PDF avec le même
  contrôle d'intégralité.
- Il signale les **sous-pages** non incluses (Claude les ajoute comme des pages de plus) et tout bloc d'un type
  qu'il ne connaît pas (son texte est gardé).

Exemple réel : *Break The Heart!* (OneMoreGame, Game Market automne 2026), règle publiée sur Notion → PDF de
9 pages avec ses 13 illustrations, du résumé jusqu'aux crédits.

---

## La note du jeu
Les liens trouvés sont gardés dans `<Ludothèque>/_outils/<Jeu>/NOTES.md`, le fichier de notes de la skill de
traduction, dans une section « Sources » :

```
# Hyakuju Parade

## Sources (recherche-regles-jeu, 2026-10-17)
- Jeu : ヒャクジュウパレード (Hyakuju Parade), カサギケイタ, バンブーゲームズ (Bamboo Games), Game Market 2026 automne
- Fiche Game Market : https://gamemarket.jp/game/188738
- Livret enregistré : HYAKUJU_PARADE_English_Rulebook.pdf — anglais, officiel — <lien>
- Manuel d'origine (jeu japonais) : <lien>
```

Si la note existe déjà, seule la section « Sources » est ajoutée ou complétée. Même si vous ne traduisez pas
tout de suite, la traduction faite plus tard retrouve ces liens sans refaire la recherche.

---

## Enchaîner avec la traduction
À la fin, Claude demande : « Voulez-vous que je lance maintenant la traduction de ce livret en français ? »
- **Oui** : la skill `traduction-regles-jeu` démarre avec le chemin du PDF, le nom du jeu et la note des liens.
- **Non** : le PDF reste prêt dans `A traduire/` ; il suffira plus tard de demander « traduis Hyakuju Parade ».

Pour que la traduction relise la note des liens, utilisez une version de `traduction-regles-jeu` qui connaît la
section « Sources » de `NOTES.md` (sinon elle refait simplement la recherche des sources).

---

## Contenu du dépôt
```
recherche-regles-jeu/
├── SKILL.md            instructions suivies par Claude (le déroulement courant)
├── README.md           ce fichier
├── references/         instructions lues seulement dans le cas concerné
│   ├── pages-web.md      règles sur des pages web (et Notion) → PDF
│   ├── introuvable.md    jeu japonais introuvable par son nom latin (YouTube, boîte, index)
│   ├── telechargement.md BoardGameGeek, Drive de l'utilisateur, règles en images, téléchargement refusé
│   └── plusieurs-jeux.md liste de plusieurs jeux d'un coup
└── scripts/
    ├── telecharger.py  téléchargement d'un PDF (Google Drive compris), liste d'un dossier Drive, images → PDF,
    │                   comparaison avec un livret déjà sur le PC (--comparer)
    ├── page_pdf.py     pages web → PDF, avec contrôle d'intégralité
    ├── notion_html.py  page Notion → HTML complet (tous les blocs), à passer ensuite à page_pdf.py
    └── fiche_gm.py     Game Market : recherche par mot, lecture d'une fiche (texte, liens, images, mentions d'une
                        autre langue), jeux d'un cercle, liens d'une autre page (blog Game Market, note.com…)
```

`SKILL.md` est relu en entier à chaque recherche : il ne garde que l'essentiel, et les cas particuliers sont
dans `references/`, lus seulement quand ils servent (moins de tokens consommés). Dans le navigateur, les pages
sont lues en texte plutôt qu'en captures d'écran, pour la même raison.

---

## Limites connues
- **BoardGameGeek** refuse la lecture simple de ses pages : sans l'extension Claude in Chrome, ses fichiers ne
  sont pas consultables, et ceux qui demandent d'être connecté doivent être téléchargés à la main.
- **Jeux tout juste sortis** (dernier Game Market) : souvent absents de BoardGameGeek et des moteurs de
  recherche ; la fiche Game Market est alors la meilleure source. Si elle n'a que le titre japonais, la
  recherche passe par les vidéos de présentation (extension Claude in Chrome nécessaire).
- **Google Drive** : un fichier dont le téléchargement est bloqué (lecture seule) n'est récupéré qu'en images,
  avec votre accord, par la méthode de la skill de traduction (`references/en-ligne.md`) : le résultat est un
  livret scanné.
- **Pages web** : le rendu suit la mise en page du navigateur, pas celle du site ; les vidéos et animations ne
  passent pas dans le PDF.
- **Notion** : la page est mise en forme simplement (pas la présentation exacte de Notion) ; l'outil s'appuie
  sur l'interface publique de Notion, qui peut changer. Une page privée ou protégée n'est pas lisible.
- Testée sous **Windows** (Chrome, PowerShell) ; le script cherche aussi Chrome et Edge sur macOS et Linux.

---

## Remarques
- **Usage personnel** : les livrets restent la propriété de leurs éditeurs ; ne les rediffusez qu'avec leur
  accord.
- Compagnon de [traduction-regles-jeu](https://github.com/vinchy1/traduction-regles-jeu), par
  [vinchy1](https://github.com/vinchy1).
