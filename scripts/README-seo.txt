MENAGEUP — PUBLICATION DE PAGES DE PRESTATION

Les contenus relus sont dans content/services.json. Le script produit du HTML
statique, les métadonnées, le fil d'Ariane et les images du sitemap. Il ne déploie pas.
Une même famille de recherches partage une page tant que son besoin reste identique.

1. Vérifier l'offre, les accès et la capacité d'intervention avant d'ajouter une prestation.
2. Ajouter un contenu original dans services.json et ses images dans assets/images.
   Image principale WebP 1536×1024 ; variantes -640.webp et -960.webp.
   Le logo officiel reste /logo-v3.png. Distinguer illustrations et vrais cas clients.
3. Exécuter : python scripts/build_services.py
   lastmod change seulement si le HTML généré change. Les anciens contenus ne sont
   pas datés artificiellement à chaque exécution. Revoir le maillage depuis une page pertinente.
4. Installer si nécessaire : python -m pip install -r scripts/requirements-seo.txt
5. Vérifier : python scripts/audit_site.py --root . --output C:/chemin/exterieur/audit.json
   Node.js doit être disponible pour la validation du JavaScript.
6. Tester le rendu sur téléphone et ordinateur, le prédevis et les cas d'échec du
   formulaire avec transports interceptés. Ne pas créer de demandes clients de test en production.
7. Montrer l'aperçu et obtenir l'accord avant publication, conformément à AGENTS.md.
8. Après publication, contrôler dans Search Console l'indexation et la canonical choisie.
   Comparer sur des périodes et filtres identiques. Compter séparément demandes,
   devis, contrats et marge. Une miniature Google ou une première position ne sont pas garanties.

Les données brutes et candidats de recherche du 77 sont dans le dossier privé
C:/Users/ez/menageup-seo/audit-2026-10-13. Ne pas publier ces rapports internes dans le site.

REALISATIONS REELLES
Les dossiers sont dans content/realisations.json. Ajouter seulement les faits
confirmés : prestation, commune, ordre des photographies et résultat visible.
Conserver les originaux privés. Ne pas transformer une illustration en preuve
client, ni inventer prix, délai, surface ou avis. Le logo réel est /logo-v3.png.
Les images WebP et leurs variantes sont dans assets/realisations/. Supprimer les
métadonnées des dérivés publics ; ne pas agrandir les photographies peu définies.
Exécuter : python scripts/build_realisations.py
Le script maintient les trois pages actuelles (hub et dossiers), leurs images
dans le sitemap et leur lastmod uniquement si le HTML change. Il conserve les
entrées des autres pages. L'audit et les contrôles visuels ci-dessus s'appliquent
également aux dossiers, avec les liens vers les services et le formulaire.

MENTIONS COMMERCIALES
Vérifier déclaration SAP et activation de l'avance immédiate avant d'en promettre
le bénéfice chez MénageUp. Sans preuve, expliquer les conditions d'éligibilité.
Les prestations de débarras, chantier et nettoyage professionnel ne reçoivent
pas la promesse fiscale du ménage au domicile d'un particulier.

CONSEILS ET MAILLAGE
Les guides de /conseils/ expliquent comment préparer une intervention. Chaque
guide garde un besoin distinct de la page de prestation vers laquelle il renvoie.
Les réalisations restent des preuves séparées : ne pas fusionner les faits ou
les photographies de deux interventions pour illustrer une prestation combinée.
Exécuter les générateurs en série, jamais simultanément :
  python scripts/build_services.py
  python scripts/build_realisations.py
  python scripts/build_guides.py
Puis lancer l'audit du site et les contrôles visuels sur l'ensemble produit.
Les trois générateurs partagent le sitemap : vérifier les liens et leurs cibles
après la dernière génération, y compris accueil, guides et réalisations.
Pour dater un lot de contenu relu, définir MENAGEUP_CONTENT_DATE au format ISO
avant la génération, par exemple dans PowerShell :
  $env:MENAGEUP_CONTENT_DATE = '2026-10-14'
Les builders services et réalisations valident cette date ; à défaut, ils utilisent
la date du système. Ils ne changent le lastmod que d'une page ajoutée ou dont le
HTML a changé. Le dernier générateur conserve les dates des autres familles.
L'accueil et l'ancienne page /nettoyage-fin-de-chantier-77/ sont édités à la main :
leur lastmod doit être actualisé séparément quand leur contenu est modifié.
Vérifier aussi les liens Conseils dans les menus desktop et mobile, les liens
contextuels en bas des services et dossiers, et l'accès aux avis Google.

GUIDES : CONTENU ET DATE
Éditer content/guides-logement.json ou content/guides-chantier.json ; tableaux,
sommaires, métadonnées et liens de devis sont produits par build_guides.py.
updated_at indique la date réelle de la dernière revue au format AAAA-MM-JJ.
published_at est facultatif : le renseigner seulement à la publication réelle,
puis reconstruire les guides. Tant qu'il est absent, aucune datePublished n'est
inventée. Les légendes distinguent toujours illustration et réalisation réelle.
quote_fields permet une trame de demande différente d'une checklist de contrôle.
Sans JavaScript, textes, sommaires, tableaux et trames restent accessibles.
Après publication, relever indexation, requêtes/pages et demandes qualifiées
avec leur page source. Le compteur de pages ou le score local de l'audit ne
mesurent ni les positions Google ni les ventes ; comparer à période égale.
