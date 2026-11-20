# Galerie du 20 novembre 2026 — aperçu local

Huit paires provenant des pièces jointes classées dans Outlook le 17 novembre.
Plusieurs vues reçues sont des exports ChatGPT, avec des changements de contenu
par rapport au reportage photographique de juillet 2021. La galerie conserve donc
la mention **visuels retouchés**. Enzo indique avoir réalisé les prestations mais
ne connaît plus les communes correspondant aux séries. Aucun lieu n'est inventé :
les champs `city` et `postal_code` restent vides pour ces huit vues.
Le 77, le 93 et le 94 figurent séparément dans les secteurs d'intervention.
Les deux réalisations historiques gardent Châtres et Pontault-Combault.

Les fichiers utilisés sur le site sont les photos reçues, encodées en WebP sans
recadrage ni agrandissement. Les grandes cartes ont un cadre paysage 4:3 avec
dégradé bleu, cohérent avec les deux cartes initiales. Ce cadre recadre l'affichage
des photos verticales ; un clic ouvre la fiche correspondante. Les deux photos
entières, sans rognage, sont disponibles dans la fiche et son agrandissement.
Les affiches générées ne sont pas utilisées sur le site.
Les originaux et leur inventaire de provenance sont conservés hors du site, dans
le dossier local de livraison. Aucun lien privé Outlook ni nom de personne n'est
inclus dans les données publiques de la galerie.

## Reconstruire

    python scripts/build_comparisons.py
    python scripts/build_realisations.py

Le premier construit le carrousel de l'accueil (dix cartes, habitation en premier)
et retire le bloc chantier séparé pour garder une seule rangée.
Le second utilise le même composant pour le sommaire, les deux fiches historiques
et les huit nouvelles fiches de comparaison. Il actualise aussi le sitemap.
L'en-tête et le pied de page sont harmonisés depuis les composants existants.
La reconstruction utilise Python et Pillow pour lire les dimensions des images.
Les fichiers statiques et les WebP sont prêts à servir, sans traitement serveur.

## Vérifié localement

- Accueil : une rangée de dix cartes avec défilement continu et boucle sans saut.
- Aucun bouton de lecture/pause ni flèche, conformément à la dernière demande.
- Pause au survol, au focus et pendant les gestes tactiles ; arrêt hors écran et avec mouvement réduit.
- Défilement tactile natif ; dix liens utilisables même sans JavaScript.
- Glissement au doigt dans les deux sens, maintien en pause tant que le doigt reste posé.
- Glissement à la souris avec curseurs grab/grabbing ; un glissement n'ouvre pas la fiche.
- Reprise automatique 2,5 secondes après le geste et la fin du défilement tactile inertiel.
- /realisations/ : les deux réalisations et les huit vues, soit dix cartes.
- Filtres : Grand nettoyage, Débarras, Interventions de chantier ; lien direct vers la catégorie.
- Ordinateur : après au repos, avant au survol, choix au clavier, agrandissement.
- Téléphone : boutons tactiles Avant / Après et ouverture des deux vues complètes.
- Fermeture avec le bouton ou Échap, retour du focus, défilement rétabli.
- Navigation au clavier, préférence de mouvement réduit, liens de secours sans JS.
- Cartes de même taille en 4:3 ; photos entières dans l'agrandissement (object-fit: contain).
- Aucun débordement horizontal à 390 px ; mêmes comparaisons dans les deux fiches historiques.
- Huit nouvelles fiches : seize photos complètes chargées, navigation entre les vues et retour au filtre chantier.
- Deuxième construction identique ; contenu des réalisations historiques conservé.

Les contrôles de la dernière version sont dans le dossier local de livraison,
`verifier-carrousel.cjs` et `verification-carrousel.json`, complétés par
`verifier-glissement.cjs` et `verification-glissement.json` pour les gestes et la reprise. Les rapports
`verification-format.json` et `verification-site.json` concernent les mises en page
précédentes et ne valident pas le carrousel actuel.

Rien n'a été poussé ni publié. L'aperçu local doit être examiné avant publication.
