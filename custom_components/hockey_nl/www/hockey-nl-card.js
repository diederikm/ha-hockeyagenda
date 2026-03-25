class HockeyNlCard extends HTMLElement {
  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  setConfig(config) {
    if (!config.entity) throw new Error("Definieer een entity");
    this._config = config;
  }

  getCardSize() {
    return 3;
  }

  _render() {
    if (!this._hass || !this._config) return;

    const stateObj = this._hass.states[this._config.entity];
    const title = this._config.title ||
      (stateObj && stateObj.attributes.display_name) ||
      "Hockey";

    if (!stateObj || ["unavailable", "unknown"].includes(stateObj.state)) {
      this.innerHTML = `
        <ha-card>
          <div style="padding:16px;text-align:center;color:var(--secondary-text-color)">
            Geen aanstaande wedstrijden
          </div>
        </ha-card>`;
      return;
    }

    const a = stateObj.attributes;
    const date = new Date(stateObj.state);
    const dateStr = date.toLocaleDateString("nl-NL", {
      weekday: "long", day: "numeric", month: "long"
    });
    const timeStr = date.toLocaleTimeString("nl-NL", {
      hour: "2-digit", minute: "2-digit"
    });

    const fallback = `data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Ccircle cx='12' cy='12' r='10' fill='%23e0e0e0'/%3E%3C/svg%3E`;
    const homeLogoErr = `this.src='${fallback}'`;
    const awayLogoErr = `this.src='${fallback}'`;

    const address = (a.facility_address || "").replace(/\n/g, ", ");

    this.innerHTML = `
      <ha-card>
        <style>
          .hn-header {
            background: var(--primary-color, #0057a8);
            color: #fff;
            padding: 10px 16px;
            font-size: 13px;
            font-weight: 600;
            letter-spacing: 0.5px;
            text-transform: uppercase;
            display: flex;
            align-items: center;
            gap: 8px;
            border-radius: var(--ha-card-border-radius,12px) var(--ha-card-border-radius,12px) 0 0;
          }
          .hn-badge {
            margin-left: auto;
            font-size: 11px;
            font-style: italic;
            font-weight: 400;
            text-transform: none;
            letter-spacing: 0;
            opacity: 0.85;
          }
          .hn-datetime {
            font-size: 18px;
            font-weight: 700;
            color: var(--primary-text-color);
            text-align: center;
            padding: 12px 16px 4px;
          }
          .hn-match {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 12px 16px;
            gap: 8px;
          }
          .hn-team {
            display: flex;
            flex-direction: column;
            align-items: center;
            flex: 1;
            gap: 6px;
            min-width: 0;
          }
          .hn-team img {
            width: 52px;
            height: 52px;
            object-fit: contain;
            background: #f5f5f5;
            border-radius: 6px;
            padding: 4px;
          }
          .hn-team-name {
            font-size: 12px;
            font-weight: 600;
            text-align: center;
            color: var(--primary-text-color);
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            width: 100%;
          }
          .hn-vs {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 6px;
            flex-shrink: 0;
            padding: 0 4px;
          }
          .hn-vs-text {
            font-size: 20px;
            font-weight: 700;
            color: var(--secondary-text-color);
          }
          .hn-pill {
            font-size: 10px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            padding: 2px 10px;
            border-radius: 99px;
            background: var(--primary-color, #0057a8);
            color: #fff;
          }
          .hn-pill.uit {
            background: var(--secondary-text-color, #757575);
          }
          .hn-info {
            border-top: 1px solid var(--divider-color, #e0e0e0);
            padding: 10px 16px 14px;
            display: flex;
            flex-direction: column;
            gap: 5px;
          }
          .hn-info-row {
            display: flex;
            align-items: flex-start;
            gap: 8px;
            font-size: 13px;
            color: var(--secondary-text-color);
            line-height: 1.4;
          }
          .hn-icon {
            font-size: 15px;
            flex-shrink: 0;
            margin-top: 1px;
          }
        </style>

        <div class="hn-header">
          🏑 ${title}
          ${a.round ? `<span class="hn-badge">Ronde ${a.round}</span>` : ""}
        </div>

        <div class="hn-datetime">${dateStr} &bull; ${timeStr}</div>

        <div class="hn-match">
          <div class="hn-team">
            <img src="${a.home_logo || fallback}" alt="${a.home_team}" onerror="${homeLogoErr}">
            <div class="hn-team-name">${a.home_team || ""}</div>
          </div>
          <div class="hn-vs">
            <span class="hn-vs-text">–</span>
            <span class="hn-pill ${a.is_home ? 'thuis' : 'uit'}">${a.is_home ? "Thuis" : "Uit"}</span>
          </div>
          <div class="hn-team">
            <img src="${a.away_logo || fallback}" alt="${a.away_team}" onerror="${awayLogoErr}">
            <div class="hn-team-name">${a.away_team || ""}</div>
          </div>
        </div>

        ${a.facility_name ? `
        <div class="hn-info">
          ${a.facility_name ? `
          <div class="hn-info-row">
            <span class="hn-icon">📍</span>
            <span>${a.facility_name}${address ? " — " + address : ""}</span>
          </div>` : ""}
          ${a.field_name ? `
          <div class="hn-info-row">
            <span class="hn-icon">🌿</span>
            <span>${a.field_name}${a.field_type ? " (" + a.field_type + ")" : ""}</span>
          </div>` : ""}
          ${a.remarks ? `
          <div class="hn-info-row">
            <span class="hn-icon">ℹ️</span>
            <span>${a.remarks}</span>
          </div>` : ""}
        </div>` : ""}
      </ha-card>`;
  }
}

customElements.define("hockey-nl-card", HockeyNlCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "hockey-nl-card",
  name: "Hockey NL Card",
  description: "Toont de volgende wedstrijd van een Nederlands hockeyteam",
  preview: false,
});
