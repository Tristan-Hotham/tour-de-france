"""Hand-made geocoding table for stage names that do not match a GeoNames cities1000 name directly.

ALIAS maps the stage name exactly as LeTourDataSet spells it to a GeoNames place (name, country, departement or other
admin2 code, or None when the name and country are enough), with the kind of link:
  exonym   the French name of a foreign town (Londres = London, Gand = Gent)
  variant  another spelling, an older name or a short form of the same town (Luchon = Bagnères-de-Luchon)
  part     a district, venue or seafront inside that town (Malo = Malo-les-Bains, part of Dunkirk; Futuroscope is
           in Chasseneuil-du-Poitou; Paris Champs-Élysées = Paris)
  station  a ski station or summit finish named after the village it belongs to (Alpe d'Huez = Huez,
           Saint-Lary-Soulan Col du Portet = Saint-Lary-Soulan). Only where the link is obvious from the name.
ALIAS_ANY lists names that stand for more than one place in the source; the nearer to the neighbouring stage towns is
used. NOPLACE lists names deliberately left without a place, with the reason. Everything else is matched by name in
02_geo.py, with ambiguous names settled by the nearest neighbouring stage town."""

ALIAS = [
    # French names of foreign towns
    ("Genève", "Geneva", "CH", None, "exonym"), ("Bruxelles", "Brussels", "BE", None, "exonym"), ("Brussel", "Brussels", "BE", None, "exonym"),
    ("Barcelone", "Barcelona", "ES", None, "exonym"), ("Saint-Sébastien", "Donostia / San Sebastián", "ES", None, "exonym"),
    ("Andorre", "Andorra la Vella", "AD", None, "exonym"), ("Andorre-la-Vieille", "Andorra la Vella", "AD", None, "exonym"),
    ("Seo de Urgel", "La Seu d'Urgell", "ES", None, "exonym"), ("Sestrières", "Sestriere", "IT", None, "exonym"),
    ("Gand", "Gent", "BE", None, "exonym"), ("Bâle", "Basel", "CH", None, "exonym"), ("Francfort", "Frankfurt am Main", "DE", None, "exonym"),
    ("Londres", "London", "GB", None, "exonym"), ("Douvres", "Dover", "GB", None, "exonym"), ("Herenthals", "Herentals", "BE", None, "exonym"),
    ("Louvain", "Leuven", "BE", None, "exonym"), ("Anvers", "Antwerp", "BE", None, "exonym"), ("Ypres", "Ieper", "BE", None, "exonym"),
    ("San Remo", "Sanremo", "IT", None, "exonym"), ("Vitoria", "Gasteiz / Vitoria", "ES", None, "exonym"),
    ("Vitoria-Gasteiz", "Gasteiz / Vitoria", "ES", None, "exonym"), ("Pampelune", "Pamplona", "ES", None, "exonym"),
    ("Copenhague", "Copenhagen", "DK", None, "exonym"), ("Saint-Willebrord", "Sint Willebrord", "NL", None, "exonym"),
    ("Sarrelouis", "Saarlouis", "DE", None, "exonym"), ("Sarrebruck", "Saarbrücken", "DE", None, "exonym"), ("Coblence", "Koblenz", "DE", None, "exonym"),
    ("Gérone", "Girona", "ES", None, "exonym"), ("Tarragone", "Tarragona", "ES", None, "exonym"), ("Aoste", "Aosta", "IT", None, "exonym"), ("Cologne", "Köln", "DE", None, "exonym"), ("Berne", "Bern", "CH", None, "exonym"),
    ("Saint-Vincent d'Aoste", "Saint-Vincent", "IT", "AO", "exonym"), ("Beringen", "Beringen", "BE", "VLI", "variant"),
    ("Fribourg-en-Brisgau", "Freiburg", "DE", "083", "exonym"), ("Saint-Nicolas", "Sint-Niklaas", "BE", None, "exonym"),
    ("Plaisance", "Piacenza", "IT", "PC", "exonym"), ("Bologne", "Bologna", "IT", "BO", "exonym"), ("La Haye", "The Hague", "NL", None, "exonym"),
    ("Enniscothy", "Enniscorthy", "IE", None, "exonym"), ("Martigny", "Martigny-Ville", "CH", None, "exonym"),
    ("Escaldes-Engordany", "les Escaldes", "AD", None, "exonym"), ("Pas de la Case", "Pas de la Casa", "AD", None, "exonym"),
    ("Molenbeek", "Molenbeek-Saint-Jean", "BE", None, "exonym"), ("Dunkerque", "Dunkirk", "FR", None, "exonym"),
    # variants, older names and short forms
    ("Luchon", "Bagnères-de-Luchon", "FR", None, "variant"), ("Les Sables", "Les Sables-d'Olonne", "FR", None, "variant"),
    ("Thonon", "Thonon-les-Bains", "FR", None, "variant"), ("Divonne", "Divonne-les-Bains", "FR", None, "variant"),
    ("Chamonix", "Chamonix-Mont-Blanc", "FR", None, "variant"), ("Chalons-sur-Marne", "Châlons-en-Champagne", "FR", None, "variant"),
    ("Trouville", "Trouville-sur-Mer", "FR", None, "variant"), ("Montereau", "Montereau-Fault-Yonne", "FR", None, "variant"),
    ("Montpon-Monesterol", "Montpon-Ménestérol", "FR", None, "variant"), ("La Guerche", "La Guerche-de-Bretagne", "FR", None, "variant"),
    ("Sablé", "Sablé-sur-Sarthe", "FR", None, "variant"), ("Port Barcarès", "Le Barcarès", "FR", None, "variant"),
    ("Oloron", "Oloron-Sainte-Marie", "FR", None, "variant"), ("Besse-en-Ch.", "Besse-et-Saint-Anastaise", "FR", None, "variant"),
    ("Besse", "Besse-et-Saint-Anastaise", "FR", None, "variant"), ("Veurey", "Veurey-Voroize", "FR", None, "variant"),
    ("Cosne", "Cosne-Cours-sur-Loire", "FR", None, "variant"), ("La Haye Fouassière", "La Haie-Fouassière", "FR", None, "variant"),
    ("Ruelle", "Ruelle-sur-Touvre", "FR", None, "variant"), ("Saint Orens de G.", "Saint-Orens-de-Gameville", "FR", None, "variant"),
    ("Carhaix", "Carhaix-Plouguer", "FR", None, "variant"), ("Malemort", "Malemort-sur-Corrèze", "FR", None, "variant"),
    ("Saint-Gervais", "Saint-Gervais-les-Bains", "FR", None, "variant"), ("Saint-Gervais Mont-Blanc", "Saint-Gervais-les-Bains", "FR", None, "variant"),
    ("Valence d'Agen", "Valence", "FR", "82", "variant"), ("Canet-Plage", "Canet-en-Roussillon", "FR", None, "variant"),
    ("La Baule", "La Baule-Escoublac", "FR", None, "variant"), ("Le Perreux", "Le Perreux-sur-Marne", "FR", None, "variant"),
    ("Cherbourg-en-Cotentin", "Cherbourg", "FR", None, "variant"),
    ("Saint-Trivier", "Saint-Trivier-de-Courtes", "FR", None, "variant"),
    ("Mazé-Montgeoffroy", "Mazé", "FR", "49", "variant"), ("Belleville-en-Beaujolais", "Belleville", "FR", "69", "variant"),
    ("Frontignan-La-Peyrade", "Frontignan", "FR", None, "variant"), ("Cazères-sur-Garonne", "Cazères", "FR", None, "variant"),
    ("Amorebieta-Etxano", "Amorebieta", "ES", None, "variant"), ("Laissac-Sévérac l'Église", "Laissac", "FR", None, "variant"),
    ("MONTIGNAC-LASCAUX", "Montignac", "FR", "24", "variant"), ("Vire Normandie", "Vire", "FR", None, "variant"),
    ("Mouilleron-Saint-Germain", "Mouilleron-en-Pareds", "FR", None, "variant"),
    ("Vielha Val d'Aran", "Vielha", "ES", None, "variant"), ("Annonay Davézieux", "Annonay", "FR", None, "variant"),
    ("Le Markstein Fellering", "Fellering", "FR", None, "variant"), ("Anvers Brasschaat", "Brasschaat", "BE", None, "variant"),
    ("Station des Rousses", "Les Rousses", "FR", None, "variant"), ("Font Romeu", "Font-Romeu-Odeillo-Via", "FR", None, "variant"),
    ("Modane Valfréjus", "Modane", "FR", None, "variant"), ("Mûr-de-Bretagne Guerlédan", "Mûr-de-Bretagne", "FR", None, "variant"),
    ("Villars-les-Dombes Parc des Oiseaux", "Villars-les-Dombes", "FR", None, "variant"), ("Maubourguet Pays du Val d'Adour", "Maubourguet", "FR", None, "variant"),
    ("Morzine Les Portes du Soleil", "Morzine", "FR", None, "variant"), ("Châtel Les Portes du Soleil", "Châtel", "FR", None, "variant"),
    ("Les Gets les portes du soleil", "Les Gets", "FR", None, "variant"), ("Bourg-Saint-Maurice Les Arcs", "Bourg-Saint-Maurice", "FR", None, "variant"),
    ("Annecy - Semnoz", "Annecy", "FR", None, "variant"),
    ("Foix Prat d'Albis", "Foix", "FR", None, "variant"), ("Cauterets-Cambasque", "Cauterets", "FR", None, "variant"),
    ("TOURMALET BAGNÈRES-DE-BIGORRE", "Bagnères-de-Bigorre", "FR", None, "variant"), ("Aime (La Plagne)", "Aime", "FR", None, "variant"),
    ("Chasseneuil-du-Poitou  Futuroscope", "Chasseneuil-du-Poitou", "FR", None, "variant"),
    # districts, venues and seafronts inside a town
    ("Paris Champs-Élysées", "Paris", "FR", "75", "part"), ("Champs-Élysées", "Paris", "FR", "75", "part"), ("Champs-Elysées", "Paris", "FR", "75", "part"),
    ("Paris Tour Eiffel", "Paris", "FR", "75", "part"), ("Paris La Défense Arena", "Nanterre", "FR", None, "part"), ("La Défense", "Puteaux", "FR", None, "part"),
    ("Lille Métropole", "Lille", "FR", "59", "part"), ("Amiens Métropole", "Amiens", "FR", None, "part"), ("Arras Citadelle", "Arras", "FR", None, "part"),
    ("Arras Communauté Urbaine", "Arras", "FR", None, "part"), ("Laval Espace Mayenne", "Laval", "FR", "53", "part"),
    ("Nice Moyen Pays", "Nice", "FR", None, "part"), ("Nice Haut Pays", "Nice", "FR", None, "part"),
    ("Sèvres - Grand Paris Seine Ouest", "Sèvres", "FR", None, "part"), ("Bruxelles Palais Royal", "Brussels", "BE", None, "part"),
    ("Brussel Atomium", "Brussels", "BE", None, "part"), ("Malo", "Dunkirk", "FR", None, "part"),
    ("Futuroscope", "Chasseneuil-du-Poitou", "FR", None, "part"), ("Puy-du-Fou", "Les Epesses", "FR", None, "part"),
    ("Disneyland-Paris", "Chessy", "FR", "77", "part"), ("Eurotunnel", "Coquelles", "FR", None, "part"),
    ("Pont du Gard", "Vers-Pont-du-Gard", "FR", None, "part"), ("Vulcania", "Saint-Ours", "FR", None, "part"),
    ("Circuit Nevers Magny-Cours", "Magny-Cours", "FR", None, "part"), ("La Caverne du Pont-d'Arc", "Vallon-Pont-d'Arc", "FR", None, "part"),
    ("Arenberg Porte du Hainaut", "Wallers", "FR", None, "part"), ("Merlin-Plage", "Saint-Hilaire-de-Riez", "FR", None, "part"),
    ("Carnon", "Mauguio", "FR", None, "part"), ("Fromentine", "La Barre-de-Monts", "FR", None, "part"),
    ("Beaulieu", "Valentigney", "FR", None, "part"), ("Lac Saint Point - Malbuisson", None, None, None, "none"),
    # ski stations and summit finishes named after their village
    ("L'Alpe-d'Huez", "Huez", "FR", None, "station"), ("Alpe d'Huez", "Huez", "FR", None, "station"),
    ("Superbagnères", "Bagnères-de-Luchon", "FR", None, "station"), ("Luchon-Superbagnères", "Bagnères-de-Luchon", "FR", None, "station"),
    ("Saint-Lary-Soulan Col du Portet", "Saint-Lary-Soulan", "FR", None, "station"), ("Saint-Lary-Soulan Pla d'Adet", "Saint-Lary-Soulan", "FR", None, "station"),
    ("Luz-Ardiden", "Luz-Saint-Sauveur", "FR", None, "station"), ("Luz Ardiden", "Luz-Saint-Sauveur", "FR", None, "station"),
    ("Ax 3 Domaines", "Ax-les-Thermes", "FR", None, "station"), ("Superbesse", "Besse-et-Saint-Anastaise", "FR", None, "station"),
    ("Super-Besse", "Besse-et-Saint-Anastaise", "FR", None, "station"), ("Super-Besse Sancy", "Besse-et-Saint-Anastaise", "FR", None, "station"),
    ("La Plagne", "Mâcot-la-Plagne", "FR", None, "station"), ("Méribel Col de la Loze", "Méribel", "FR", None, "station"),
    ("Courchevel Col de la Loze", "Courchevel", "FR", None, "station"),
]
ALIAS = {a[0]: a[1:] for a in ALIAS if a[4] != "none"}

ALIAS_ANY = {"Fribourg": [("Fribourg", "CH", "1004"), ("Freiburg", "DE", "083")]}   # Freiburg im Breisgau in 1964, 1971 and 1977, Fribourg in 1997

NOPLACE = {
    # summits and passes with no village in the name
    "Puy de Dôme": "summit", "Mont Ventoux": "summit", "Hautacam": "summit", "Col du Tourmalet": "summit", "Tourmalet Barèges": "summit",
    "Plateau de Beille": "summit", "plateau_de_beille": "summit", "La Planche des Belles Filles": "summit",
    "La Super Planche des Belles Filles": "summit", "Ballon d'Alsace": "summit", "Grand Colombier": "summit", "Col d'Aubisque": "summit",
    "gourette_col_d_aubisque": "summit", "Mont Revard": "summit", "Mont Aigoual": "summit", "Puy Mary Cantal": "summit",
    "Col de la Couillole": "summit", "Izoard": "summit", "Galibier Serre-Chevalier": "summit", "Col du Granon Serre Chevalier": "summit",
    "Plateau de Solaison": "summit", "Mont des Alouettes": "summit", "Val d'Aran - Pla-de-Beret": "summit",
    "Saint François Longchamp -  Col de la Madeleine": "summit", "Prato Nevoso": "summit",
    # ski stations not named after a village in the gazetteer
    "Orcières-Merlette": "ski station", "Avoriaz": "ski station", "Peyragudes": "ski station", "La Mongie": "ski station",
    "Pra Loup": "ski station", "Guzet-Neige": "ski station", "La Toussuire": "ski station", "Le Lioran": "ski station",
    "Super-Lioran": "ski station", "Gourette": "ski station", "Les Menuires": "ski station", "Pyrénées 2000": "ski station",
    "Chamrousse": "ski station", "Isola 2000": "ski station", "Serre-Chevalier": "ski station", "Les Arcs": "ski station",
    "Les Orres": "ski station", "Prapoutel": "ski station", "Le Pleynet": "ski station", "La Ruchère": "ski station",
    "Val Louron": "ski station", "Piau-Engaly": "ski station", "Risoul": "ski station", "Superdévoluy": "ski station",
    "La Pierre-Saint-Martin": "ski station", "La Rosière Espace San Bernardo": "ski station", "Lac de Payolle": "ski station",
    "Finhaut-Emosson": "ski station",
    # venues, lakes, capes and causeways spread over several communes, and regions
    "Lac de Vassivière": "venue", "Lac de Madine": "venue", "Domaine du Rouret": "venue", "Passage du Gois": "venue",
    "Cap Découverte": "venue", "Cap Fréhel": "venue", "Zélande": "region", "Ile d'Oléron": "region",
    "Utah Beach Sainte-Marie-du-Mont": "not in gazetteer", "Lac Saint Point - Malbuisson": "not in gazetteer",
    "Les Angles": "not in gazetteer",
    "Feldsberg": "not in gazetteer", "Woluwé-Saint-Pierre": "not in gazetteer", "ONET-LE-CHÂTEAU": "not in gazetteer",
    "Saint-Maixent-L'Ecole": "not in gazetteer", "Île de Ré Saint-Martin-de-Ré": "not in gazetteer", "Bourgoin": "not in gazetteer", "Bourgoin-Jallieu": "not in gazetteer",
    "Île d'Oléron Le Château-d'Oléron": "not in gazetteer", "Le Mont-Dore Puy de Sancy": "not in gazetteer",
}
