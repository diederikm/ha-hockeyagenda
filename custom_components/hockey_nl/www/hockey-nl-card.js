import {
  LitElement,
  html,
  css,
} from "https://unpkg.com/lit@2/index.js?module";

class HockeyNlCard extends LitElement {
  static get properties() {
    return {
      hass: { type: Object },
      config: { type: Object },
    };
  }

  setConfig(config) {
    if (!config.entity) {
      throw new Error("Please define an entity");
    }
    this.config = config;
  }

  getCardSize() {
    return 3;
  }

  static get styles() {
    return css`
      :host {
        --card-bg: var(--card-background-color, #fff);
        --primary: var(--primary-color, #0057a8);
        --text: var(--primary-text-color, #212121);
        --secondary-text: var(--secondary-text-color, #757575);
        --divider: var(--divider-color, #e0e0e0);
      }

      ha-card {
        overflow: hidden;
        font-family: var(--paper-font-body1_-_font-family, sans-serif);
      }

      .header {
        background: var(--primary);
        color: #fff;
        padding: 10px 16px;
        font-size: 13px;
        font-weight: 600;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        display: flex;
        align-items: center;
        gap: 8px;
      }

      .header ha-icon {
        --mdc-icon-size: 18px;
      }

      .match-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 16px;
        gap: 8px;
      }

      .team {
        display: flex;
        flex-direction: column;
        align-items: center;
        flex: 1;
        gap: 8px;
        min-width: 0;
      }

      .team img {
        width: 56px;
        height: 56px;
        object-fit: contain;
        border-radius: 4px;
        background: #f5f5f5;
        padding: 4px;
        flex-shrink: 0;
      }

      .team img.placeholder {
        opacity: 0.3;
      }

      .team-name {
        font-size: 13px;
        font-weight: 600;
        text-align: center;
        color: var(--text);
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        width: 100%;
      }

      .versus {
        display: flex;
        flex-direction: column;
        align-items: center;
        flex-shrink: 0;
        gap: 4px;
        padding: 0 8px;
      }

      .vs-text {
        font-size: 18px;
        font-weight: 700;
        color: var(--secondary-text);
      }

      .home-away-badge {
        font-size: 10px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        padding: 2px 8px;
        border-radius: 99px;
        background: var(--primary);
        color: #fff;
      }

      .home-away-badge.uit {
        background: var(--secondary-text);
      }

      .info {
        padding: 0 16px 16px;
        display: flex;
        flex-direction: column;
        gap: 6px;
        border-top: 1px solid var(--divider);
        padding-top: 12px;
      }

      .info-row {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 13px;
        color: var(--secondary-text);
      }

      .info-row ha-icon {
        --mdc-icon-size: 16px;
        flex-shrink: 0;
        color: var(--primary);
      }

      .date-time {
        font-size: 20px;
        font-weight: 700;
        color: var(--text);
        text-align: center;
        padding: 8px 16px 0;
      }

      .no-match {
        padding: 24px 16px;
        text-align: center;
        color: var(--secondary-text);
        font-size: 14px;
      }

      .round-badge {
        font-size: 11px;
        color: var(--secondary-text);
        font-style: italic;
      }
    `;
  }

  render() {
    const stateObj = this.hass.states[this.config.entity];
    if (!stateObj) {
      return html`<ha-card><div class="no-match">Entiteit niet gevonden: ${this.config.entity}</div></ha-card>`;
    }

    const attrs = stateObj.attributes;
    const title = this.config.title || attrs.display_name || "Hockey";

    if (!stateObj.state || stateObj.state === "unavailable" || stateObj.state === "unknown") {
      return html`
        <ha-card>
          <div class="header"><ha-icon icon="mdi:hockey-sticks"></ha-icon>${title}</div>
          <div class="no-match">Geen aanstaande wedstrijden</div>
        </ha-card>
      `;
    }

    const date = new Date(stateObj.state);
    const dateStr = date.toLocaleDateString("nl-NL", { weekday: "long", day: "numeric", month: "long" });
    const timeStr = date.toLocaleTimeString("nl-NL", { hour: "2-digit", minute: "2-digit" });

    const isHome = attrs.is_home;
    const homeLogo = attrs.home_logo;
    const awayLogo = attrs.away_logo;
    const fallback = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath fill='%23ccc' d='M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z'/%3E%3C/svg%3E";

    return html`
      <ha-card>
        <div class="header">
          <ha-icon icon="mdi:hockey-sticks"></ha-icon>
          ${title}
          ${attrs.round ? html`<span class="round-badge" style="margin-left:auto">Ronde ${attrs.round}</span>` : ""}
        </div>

        <div class="date-time">${dateStr} &bull; ${timeStr}</div>

        <div class="match-row">
          <div class="team">
            <img src="${homeLogo || fallback}" alt="${attrs.home_team}"
              @error="${(e) => { e.target.src = fallback; }}" />
            <div class="team-name">${attrs.home_team}</div>
          </div>

          <div class="versus">
            <span class="vs-text">-</span>
            <span class="home-away-badge ${isHome ? 'thuis' : 'uit'}">${isHome ? 'Thuis' : 'Uit'}</span>
          </div>

          <div class="team">
            <img src="${awayLogo || fallback}" alt="${attrs.away_team}"
              @error="${(e) => { e.target.src = fallback; }}" />
            <div class="team-name">${attrs.away_team}</div>
          </div>
        </div>

        <div class="info">
          ${attrs.facility_name ? html`
            <div class="info-row">
              <ha-icon icon="mdi:map-marker"></ha-icon>
              <span>${attrs.facility_name}${attrs.facility_address ? html` &mdash; ${attrs.facility_address.replace(/\n/g, ", ")}` : ""}</span>
            </div>
          ` : ""}
          ${attrs.field_name ? html`
            <div class="info-row">
              <ha-icon icon="mdi:grass"></ha-icon>
              <span>${attrs.field_name} (${attrs.field_type})</span>
            </div>
          ` : ""}
          ${attrs.remarks ? html`
            <div class="info-row">
              <ha-icon icon="mdi:information-outline"></ha-icon>
              <span>${attrs.remarks}</span>
            </div>
          ` : ""}
        </div>
      </ha-card>
    `;
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
