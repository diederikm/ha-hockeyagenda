# Hockey Agenda voor Home Assistant

Volg de wedstrijden van elk Nederlands veldhockey team rechtstreeks in Home Assistant. Werkt voor alle clubs en teams die zijn aangesloten bij de KNHB.

---

## Wat het doet

Na installatie krijg je per team:

- **Sensor** — toont datum en tijd van de eerstvolgende wedstrijd als state, met alle details als attributes (tegenstander, locatie, veld, thuis/uit)
- **Kalender** — het volledige seizoensschema zichtbaar in de Home Assistant agenda
- **Lovelace card** — een mooie kaart met de club logo's, datum, tijd en locatie

---

## Installatie via HACS

1. Ga in Home Assistant naar **HACS → Integraties**
2. Klik op de drie puntjes (⋮) rechtsboven → **Custom repositories**
3. Voeg toe: `https://github.com/diederikm/ha-hockeyagenda` — categorie: **Integration**
4. Zoek op **Hockey Agenda** en klik op **Downloaden**
5. Herstart Home Assistant

---

## Configuratie

1. Ga naar **Instellingen → Apparaten & diensten → Integratie toevoegen**
2. Zoek op **Hockey Agenda**
3. Typ de naam van de club (bijv. `Amsterdam`)
4. Selecteer het team
5. Geef optioneel een weergavenaam (bijv. de naam van je kind)
6. Herhaal voor meerdere teams

---

## De Lovelace card toevoegen

De card wordt automatisch geregistreerd bij installatie. Voeg hem toe aan je dashboard:

```yaml
type: custom:hockey-nl-card
entity: sensor.hockey_thomas
```

Optioneel een eigen titel:

```yaml
type: custom:hockey-nl-card
entity: sensor.hockey_thomas
title: Thomas - JO12
```

---

## Sensor attributes

| Attribuut | Voorbeeld |
|---|---|
| `date` | `2026-03-28T09:40:00+01:00` |
| `is_home` | `false` |
| `home_team` | `HBS JO12-2` |
| `away_team` | `Bloemendaal JO12-3` |
| `opponent` | `HBS JO12-2` |
| `opponent_logo` | `https://...` |
| `facility_name` | `Sportpark 'Bleek en Berg'` |
| `facility_address` | `Bergweg 1, Bloemendaal` |
| `field_name` | `KG 3 Veld 3` |
| `field_type` | `Waterveld` |
| `round` | `4` |
| `score_home` | `0` |
| `score_away` | `0` |
| `status` | `scheduled` |

---

## Automation voorbeeld

Stuur een melding twee uur voor de wedstrijd:

```yaml
automation:
  alias: "Herinnering hockeywedstrijd Thomas"
  trigger:
    - platform: template
      value_template: >
        {% set match = states('sensor.hockey_thomas') %}
        {% if match not in ['unknown', 'unavailable'] %}
          {{ (as_datetime(match) - now()).total_seconds() | int == 7200 }}
        {% endif %}
  action:
    - service: notify.mobile_app
      data:
        title: "Hockeywedstrijd!"
        message: >
          {{ state_attr('sensor.hockey_thomas', 'is_home') | bool
            | ternary('Thuiswedstrijd', 'Uitwedstrijd') }}
          tegen {{ state_attr('sensor.hockey_thomas', 'opponent') }}
          om {{ as_datetime(states('sensor.hockey_thomas')).strftime('%H:%M') }}
          op {{ state_attr('sensor.hockey_thomas', 'facility_name') }}
```

---

## Hoe het werkt

De integratie haalt wedstrijddata op via de API van [HockeyWeerelt](https://app.hockeyweerelt.nl), het platform achter hockey.nl en de officiële KNHB app. De data wordt elke 10 minuten vernieuwd.

Ondersteunt alle Nederlandse veldhockeycompetities: jeugd, senioren, zaal en veld.

---

## Bijdragen

Issues en pull requests zijn welkom op [GitHub](https://github.com/diederikm/ha-hockeyagenda).
