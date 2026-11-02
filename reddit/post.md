## Title

[OC] Every Tour de France stage since 1903, start to finish. For 30 years it was one unbroken lap of France's edges; now 88% of stages start somewhere other than the last finish

## Body

I mapped all 2,427 stages of the men's Tour de France (1903 to 2026) as straight lines from start town to finish town, coloured by decade. The early Tours really were a tour: in the 1920s, 92% of the French towns the race stopped in were within 50 km of the coast or a border, and every stage started where the last one ended. The longest Tour was 5,745 km in 1926; the 2026 race was 3,333 km and won at a record 45.1 km/h. Paris (161 starts and finishes), Bordeaux (137) and Pau (133) are the most used towns, and 27 Tours have started abroad, 14 of the 27 since 2000. Caveats: lines are not roads; summit finishes with no village in their name (Puy de Dôme, Mont Ventoux) are left off; 95.8% of starts and finishes are located. Interactive map with a play button that draws each Tour in order: https://maps.tristanhotham.com/tour-de-france/

## Source comment

Source: LeTourDataSet by Thomas Camminady (MIT licence, github.com/thomascamminady/LeTourDataSet), compiled from the official letour.fr pages: every stage's start and finish town, every Tour's distance and the winners' times. Town locations: GeoNames cities1000 (CC BY 4.0), matched by name with a hand-checked table for French exonyms (Londres, Gand), venues and ski stations. Outlines: Natural Earth. Winners' nationalities added by hand.

Tools: Python (pandas, shapely, pyproj, matplotlib); MapLibre for the interactive map.

Interactive version: https://maps.tristanhotham.com/tour-de-france/
Paper: https://doi.org/10.5281/zenodo.23873013
Blog post: https://blog.tristanhotham.com/2026/10/31/tour-de-france/
