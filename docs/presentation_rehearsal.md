# Presentation Rehearsal Notes

## Short project story (about 5-7 minutes)

### 1. Problem

This project helps an expansion director decide where to start looking for a
new coworking location in Lisbon. The goal is not to choose a final building.
The goal is to identify one priority parish and two alternatives for detailed
site research.

### 2. Data

I compare all 24 Lisbon parishes. I use public data from official Lisbon
sources, INE Census 2021, OpenStreetMap and official coworking operator
websites. I also use a pilot sample of commercial asking rents for the ten
leading candidates. The main processed datasets are in the `data/processed`
folder, and every source and limitation is documented in `docs`.

### 3. Method

I built a transparent Opportunity Score. It combines demand, public transport,
low observed coworking competition and rent affordability. The final weights
are 35 percent for demand, 25 percent for transport, 25 percent for competition
opportunity and 15 percent for rent. This is a screening model, not a machine
learning forecast.

I also tested different weight combinations 5,000 times with a fixed random
seed. This checks whether the result depends too much on one set of weights.

### 4. Main findings

The verified dataset contains 48 active coworking locations. Ten of the 24
parishes have no verified active coworking location. Existing supply is quite
concentrated: Santo António, Arroios and Santa Maria Maior contain 22 of the 48
locations.

The final rent-inclusive shortlist ranks Areeiro first, Lumiar second and
Arroios third. Areeiro has strong demand, good transport and no verified active
coworking location. It ranks first in 92.76 percent of 5,000 simulations and is
in the top three in 99.96 percent.

### 5. Recommendation

My recommendation is to start site-level due diligence in Areeiro, especially
near Areeiro, Alameda and Roma-Areeiro stations. The next step is to inspect
available 300-800 square metre offices and validate rent, competitor coverage
and unit economics.

Lumiar is the lower-rent alternative, but its demand signal is weaker and needs
local validation. Arroios has very strong demand and transport, but it already
has seven verified competitors, so it needs a detailed competitor review.

### 6. Limitations and close

Public sources can miss locations, asking rents are not transaction rents, and
rent data currently covers only the ten leading candidates. The model helps
decide where to investigate first; it does not make the final lease decision.

Our recommendation is Areeiro - happy to take questions.

## GitHub walkthrough

- `README.md`: problem, data, method, findings and recommendations.
- `notebooks/`: cleaning, EDA, deeper analysis, recommendations and final charts.
- `data/processed/`: analysis-ready tables.
- `reports/figures/`: exported charts used in the presentation.
- `reports/tables/final_shortlist.csv`: final three candidates and stability results.
- `docs/methodology.md`: score formula, assumptions and limitations.

## Likely questions and short answers

**Why Areeiro?** It has a strong balance of demand, transport and low observed
competition. The result is also stable when the model weights change.

**Why not Arroios if its demand is higher?** Arroios already has seven verified
coworking locations. It is attractive, but the competitive gap is smaller.

**Why is Lumiar second?** It combines zero verified supply, good transport and
lower pilot rent, but its weaker demand signal needs local validation.

**How did you choose the weights?** I used a clear business-priority structure:
35 percent demand, 25 percent transport, 25 percent competition and 15 percent
rent. I then tested many alternative combinations to check stability.

**Is this machine learning?** No. It is a transparent multi-criteria decision
model. With only 24 parishes, a complex predictive model would create false
precision.

**What does zero coworking mean?** It means no active location was verified in
the current public-source dataset. It does not prove that there is no coworking
space or that demand exists.

**What would you do next?** Expand rent coverage, inspect available buildings,
check competitor capacity and prices, and build site-level unit economics.

## Required 8-slide deck draft

1. Title and problem: where should a coworking operator investigate next?
2. Dataset: 24 parishes, 48 verified locations and public-source indicators.
3. Finding: Lisbon coworking supply is concentrated in three central parishes.
4. Finding: Areeiro combines strong demand and transport with no verified supply.
5. Finding: Areeiro remains stable when weights change.
6. SCR recommendation: start four-week site due diligence in Areeiro.
7. SCR alternatives: validate Lumiar demand and map Arroios competitors.
8. Conclusion and next steps: Areeiro first; validate sites and unit economics.
