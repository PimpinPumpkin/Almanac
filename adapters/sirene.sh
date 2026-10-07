#!/usr/bin/env bash
# France, SIRENE (INSEE): registered business establishments, as open evidence.
#
# sirene  one row per active establishment (SIRET, administrative state A),
#         open as of dateDebut, the day its current entry in the register
#         began: its creation, or the last change to its name, activity or
#         address. That is the last day something is known to have happened.
#         The register's processing date is not used: nearly every record
#         carries one from the last year, and dated that way an "active"
#         entry overrode 159 closures that OSM mappers had tagged by hand.
#
# Closed establishments (state F) are not emitted. A SIRET closes when the
# shop changes owner or legal form, and the shop carries on under a new
# one. Measured in the Paris box on places whose newest record was a
# closure: independent evidence said still open 1,082 times and closed 647.
# Even records joined by the SIRET tagged in OSM failed (130 to 40).
#
# Only rows the register marks as freely diffusible are read. A sole trader
# is a natural person, often registered at home, so those rows are used only
# when they carry a shop sign (enseigne). The name is the sign, else the
# establishment's usual name, else the company name. Rows are evidence for
# places that are already listed; nothing here creates a place.
#
# Reads the monthly parquet files in place over HTTP. SIRENE_DEPARTEMENTS
# limits the read to some departements ("75 92 93 94"); blank reads France.
#
# Licence Ouverte 2.0 (Etalab). Source: INSEE, base Sirene.
# https://www.data.gouv.fr/datasets/base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret
source "$(dirname "$0")/../lib/common.sh"

API=https://www.data.gouv.fr/api/1/datasets/base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret/
META="$(curl -fsSL -A "$UA" "$API")"
url() { jq -r --arg k "$1" '.resources[] | select(.url | endswith($k)) | .url' <<<"$META" | head -1; }
ETAB="$(url stock-stocketablissement-parquet.parquet)"
UNIT="$(url stock-stockunitelegale-parquet.parquet)"
[ -n "$ETAB" ] && [ -n "$UNIT" ] || { echo "SIRENE parquet files not found in the dataset listing" >&2; exit 1; }

WHERE=""
if [ -n "${SIRENE_DEPARTEMENTS:-}" ]; then
  WHERE="and substr(codeCommuneEtablissement, 1, 2) in ($(printf "'%s'," $SIRENE_DEPARTEMENTS | sed 's/,$//'))"
fi

mkdir -p "$CACHE/evidence/fr"
duck <<SQL
copy (
  with e as (
    select siren, siret, etatAdministratifEtablissement as etat, dateDebut,
           dateDernierTraitementEtablissement::date as touched,
           coalesce(enseigne1Etablissement, denominationUsuelleEtablissement) as sign,
           trim(concat_ws(' ', numeroVoieEtablissement, typeVoieEtablissement, libelleVoieEtablissement)) as street,
           codePostalEtablissement as cp, libelleCommuneEtablissement as commune,
           try_cast(coordonneeLambertAbscisseEtablissement as double) as x,
           try_cast(coordonneeLambertOrdonneeEtablissement as double) as y
    from read_parquet('$ETAB')
    where statutDiffusionEtablissement = 'O' and etatAdministratifEtablissement = 'A' $WHERE
  ),
  u as (
    select siren, denominationUniteLegale as company,
           categorieJuridiqueUniteLegale::varchar like '1%' as person
    from read_parquet('$UNIT')
    where siren in (select siren from e)
  ),
  j as (
    select e.*, coalesce(e.sign, case when not u.person then u.company end) as name,
           st_transform(st_point(e.x, e.y), 'EPSG:2154', 'EPSG:4326', always_xy := true) as g
    from e left join u using (siren)
  )
  select 'sirene' as source, siret as source_id, name,
         concat_ws(', ', street, commune, cp) as address,
         round(st_y(g), 6) as lat, round(st_x(g), 6) as lng,
         'open' as state, dateDebut as date
  from j
  where name is not null and x is not null and dateDebut is not null
) to '$CACHE/evidence/fr/sirene.parquet.part' (format parquet, compression zstd);
SQL
mv "$CACHE/evidence/fr/sirene.parquet.part" "$CACHE/evidence/fr/sirene.parquet"
duckdb -c "select state, count(*) as records, min(date), max(date) from '$CACHE/evidence/fr/sirene.parquet' group by 1"
