# FEC Audit FR

**Outil open source, gratuit, local et en lecture seule** pour effectuer des contrôles préliminaires sur les fichiers des écritures comptables (FEC) français.

Il aide notamment les cabinets, comptables et petites entreprises à repérer rapidement des défauts de structure et des déséquilibres avant une revue humaine.

## Fonctionnalités (v0.1.0)

- Vérification des **18 premières colonnes** réglementaires et de leur ordre ; colonnes additionnelles autorisées si nommées.
- Lecture des fichiers texte séparés par tabulation, `|` ou `;`, en UTF-8 ou Windows-1252.
- Vérification de dates `AAAAMMJJ` conformément au format FEC réglementaire.
- Validation des champs débit/crédit, des montants numériques et des montants en devise.
- Contrôle arithmétique de chaque écriture par couple **journal + numéro d'écriture**, puis du fichier entier.
- Rapport texte ou JSON et codes de retour pratiques pour l'automatisation.
- **Aucune connexion réseau ; aucune altération du fichier source.**

## Exemple rapide

Avec Python 3.10 ou supérieur, depuis ce dossier :

```bash
PYTHONPATH=src python -m fec_audit_fr exemples/exemple_fec.txt
PYTHONPATH=src python -m fec_audit_fr exemples/exemple_fec.txt --json
```

Installation en environnement virtuel (facultatif) :

```bash
python -m venv .venv
# Windows : .venv\\Scripts\\activate
# Linux/macOS : source .venv/bin/activate
python -m pip install -e .
fec-audit exemples/exemple_fec.txt
```

Test :

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

Sur Windows PowerShell, remplacer `PYTHONPATH=src` par `$env:PYTHONPATH='src';` avant la commande.

## Signification des résultats

- **0** : pas d'erreur détectée sur les contrôles implémentés ; des alertes peuvent subsister.
- **1** : au moins une erreur détectée.
- **2** : problème technique de lecture.

`ok: true` ne vaut **pas** certification de conformité d'un FEC : ce projet ne vérifie pas toutes les exigences fiscales ni l'exactitude des pièces comptables.

## Protection des données

Les données comptables peuvent être confidentielles. **Ne publiez jamais vos vrais FEC, documents clients, identités, transactions ou numéros de compte sur GitHub.** L'exemple inclus est totalement fictif. Le programme fonctionne localement et n'envoie aucune information à un serveur.

## Références officielles

- [Article A. 47 A-1 du Livre des procédures fiscales](https://www.legifrance.gouv.fr/codes/section_lc/LEGITEXT000006069583/LEGISCTA000006084349/2026-07-01/)
- [Arrêté du 29 juillet 2013 — norme FEC](https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000027788276)
- [BOFiP — Contrôle des comptabilités informatisées](https://bofip.impots.gouv.fr/bofip/9028-PGP.html)

## Limites connues et feuille de route

La v0.1 vérifie des propriétés syntaxiques et arithmétiques seulement. Elle ne contrôle pas encore le séquencement chronologique, la continuité de numérotation, l'ensemble des règles métier, ni la cohérence des pièces avec la comptabilité.

Contributions souhaitées : prise en charge de grands volumes en streaming, contrôles avancés documentés, fixtures réalistes mais **entièrement fictives**, documentation et traductions. Merci d'ouvrir une issue décrivant le besoin avant une modification majeure.

## Licence

MIT — voir `LICENSE`.
