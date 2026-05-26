import os
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

from teaching_bot import TeachingBot, BotConfig, TOPIC_CONFIGS


# --------------------------------------------------
# Perusasetukset
# --------------------------------------------------

load_dotenv()

st.set_page_config(
    page_title="Tiro — Mekaanikko-oppilas",
    page_icon="🔩",
    layout="wide",
)


# --------------------------------------------------
# Mekaanikkoteema
# --------------------------------------------------

st.markdown(
    """
    <style>
    :root {
        --workshop-bg: #f3f0e8;
        --workshop-panel: #ffffff;
        --workshop-panel-2: #fff8ed;
        --workshop-text: #1f2933;
        --workshop-muted: #5f6b76;
        --workshop-orange: #e67e22;
        --workshop-orange-dark: #b85f12;
        --workshop-yellow: #f5b041;
        --workshop-border: #d6c7aa;
        --workshop-steel: #6b7280;
        --workshop-dark: #263238;
    }

    .stApp {
        background:
            linear-gradient(
                135deg,
                rgba(255, 255, 255, 0.86),
                rgba(243, 240, 232, 0.94)
            ),
            repeating-linear-gradient(
                45deg,
                rgba(38, 50, 56, 0.035) 0px,
                rgba(38, 50, 56, 0.035) 2px,
                transparent 2px,
                transparent 18px
            );
        color: var(--workshop-text);
    }

    .block-container {
        background-color: rgba(255, 255, 255, 0.84);
        border: 1px solid rgba(214, 199, 170, 0.8);
        border-radius: 14px;
        padding-top: 2rem;
        padding-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(31, 41, 51, 0.08);
    }

    p, li, span, label, div {
        color: var(--workshop-text);
    }

    h1, h2, h3 {
        color: var(--workshop-dark) !important;
        font-family: "Segoe UI", Arial, sans-serif;
        font-weight: 800;
        letter-spacing: 0.2px;
    }

    h1 {
        border-bottom: 4px solid var(--workshop-orange);
        padding-bottom: 0.45rem;
    }

    h2, h3 {
        border-left: 5px solid var(--workshop-orange);
        padding-left: 0.55rem;
    }

    a {
        color: var(--workshop-orange-dark) !important;
        font-weight: 600;
    }

    code {
        background-color: #f2eadb;
        color: #8f470c;
        padding: 0.15rem 0.35rem;
        border-radius: 5px;
    }

    [data-testid="stSidebar"] {
        background:
            linear-gradient(
                180deg,
                #fffaf0 0%,
                #f2eadb 100%
            );
        border-right: 3px solid var(--workshop-orange);
    }

    [data-testid="stSidebar"] * {
        color: var(--workshop-text) !important;
    }

    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: var(--workshop-dark) !important;
    }

    .tiro-workshop-banner {
        background: linear-gradient(90deg, #fff8ed, #ffffff);
        border: 1px solid var(--workshop-border);
        border-left: 7px solid var(--workshop-orange);
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 5px 18px rgba(31, 41, 51, 0.07);
        color: var(--workshop-text);
        line-height: 1.55;
        margin-bottom: 1rem;
    }

    .tiro-workshop-banner b {
        color: var(--workshop-dark);
    }

    [data-testid="stChatMessage"] {
        background-color: var(--workshop-panel);
        border: 1px solid var(--workshop-border);
        border-left: 6px solid var(--workshop-orange);
        border-radius: 12px;
        padding: 0.75rem;
        box-shadow: 0 4px 12px rgba(31, 41, 51, 0.06);
    }

    [data-testid="stChatMessage"] p {
        color: var(--workshop-text) !important;
        line-height: 1.55;
    }

    .stButton button,
    .stDownloadButton button {
        background: linear-gradient(180deg, #f5b041, #e67e22) !important;
        color: #1f2933 !important;
        font-weight: 800 !important;
        border: 2px solid var(--workshop-orange-dark) !important;
        border-radius: 8px !important;
        box-shadow: 0 3px 0 var(--workshop-orange-dark);
        letter-spacing: 0.3px;
    }

    .stButton button:hover,
    .stDownloadButton button:hover {
        background: linear-gradient(180deg, #ffd27a, #f39c12) !important;
        border-color: #8f470c !important;
        transform: translateY(-1px);
    }

    .stButton button:active,
    .stDownloadButton button:active {
        transform: translateY(2px);
        box-shadow: 0 1px 0 var(--workshop-orange-dark);
    }

    .stButton button:disabled,
    .stDownloadButton button:disabled {
        background: #d7d2c7 !important;
        color: #6b7280 !important;
        border-color: #b7afa1 !important;
        box-shadow: none;
    }

    input,
    textarea,
    [data-baseweb="select"] {
        background-color: #ffffff !important;
        color: var(--workshop-text) !important;
    }

    [data-testid="stChatInput"] {
        background-color: #ffffff;
        border: 2px solid var(--workshop-orange);
        border-radius: 12px;
        box-shadow: 0 4px 14px rgba(230, 126, 34, 0.15);
    }

    [data-testid="stChatInput"] textarea {
        color: var(--workshop-text) !important;
    }

    [data-testid="stExpander"] {
        background-color: rgba(255, 255, 255, 0.75);
        border: 1px solid var(--workshop-border);
        border-radius: 10px;
    }

    .stAlert {
        background-color: #fff8ed !important;
        color: var(--workshop-text) !important;
        border-left: 6px solid var(--workshop-orange) !important;
        border-radius: 10px;
    }

    .stAlert p {
        color: var(--workshop-text) !important;
    }

    hr {
        border-color: rgba(184, 95, 18, 0.25);
        margin-top: 1.5rem;
        margin-bottom: 1.5rem;
    }

    .right-workshop-panel {
        background: rgba(255, 248, 237, 0.96);
        border: 1px solid var(--workshop-border);
        border-left: 6px solid var(--workshop-orange);
        border-radius: 14px;
        padding: 1rem;
        box-shadow: 0 6px 18px rgba(31, 41, 51, 0.08);
        margin-bottom: 1rem;
    }

    .right-workshop-panel h3 {
        border-left: none !important;
        padding-left: 0 !important;
        margin-top: 0;
        margin-bottom: 0.5rem;
    }

    .right-panel-note {
        background: #fffdf7;
        border: 1px solid var(--workshop-border);
        border-radius: 10px;
        padding: 0.75rem;
        margin-bottom: 0.75rem;
        font-size: 0.92rem;
        line-height: 1.45;
        color: var(--workshop-text);
    }

    .learning-card {
        background-color: #fffdf7;
        border: 1px solid var(--workshop-border);
        border-left: 6px solid var(--workshop-orange);
        border-radius: 10px;
        padding: 0.85rem;
        margin-bottom: 0.65rem;
        box-shadow: 0 3px 10px rgba(31, 41, 51, 0.045);
    }

    .learning-card-title {
        font-size: 1.02rem;
        font-weight: 800;
        color: var(--workshop-dark);
        margin-bottom: 0.25rem;
    }

    .learning-card-status {
        color: var(--workshop-text);
        margin-bottom: 0.25rem;
    }

    .learning-card-desc {
        color: var(--workshop-muted);
        line-height: 1.45;
        font-size: 0.93rem;
    }

    @media (max-width: 900px) {
        .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# API-avain
# --------------------------------------------------

def get_api_key() -> str | None:
    try:
        api_key = st.secrets["OPENAI_API_KEY"]
        if api_key:
            return api_key
    except Exception:
        pass

    return os.getenv("OPENAI_API_KEY")


# --------------------------------------------------
# Botin alustus
# --------------------------------------------------

def init_bot(topic_key: str) -> TeachingBot:
    api_key = get_api_key()

    if not api_key:
        st.error(
            "🔧 OPENAI_API_KEY puuttuu. Lisää se `.env`-tiedostoon "
            "tai Streamlitin secretsiin."
        )
        st.stop()

    client = OpenAI(api_key=api_key)

    config = BotConfig(
        topic_key=topic_key,
        main_model=st.session_state.get("main_model", "gpt-4o"),
        judge_model="gpt-4o-mini",
        temperature=st.session_state.get("temperature", 0.6),
        max_turns=st.session_state.get("max_turns", 30),
    )

    return TeachingBot(client, config)


def reset_session(topic_key: str) -> None:
    st.session_state.bot = init_bot(topic_key)
    st.session_state.messages = []
    st.session_state.summary = None
    st.session_state.skill_test = None
    st.session_state.current_topic = topic_key

    opening = st.session_state.bot.opening_message()

    st.session_state.bot.history.append(
        {"role": "assistant", "content": opening}
    )
    st.session_state.messages.append(
        {"role": "assistant", "content": opening}
    )


# --------------------------------------------------
# Session state
# --------------------------------------------------

for key, default in [
    ("bot", None),
    ("messages", []),
    ("summary", None),
    ("skill_test", None),
    ("current_topic", "oljynsuodatin"),
    ("main_model", "gpt-4o"),
    ("temperature", 0.6),
    ("max_turns", 30),
    ("consent_given", False),
]:
    if key not in st.session_state:
        st.session_state[key] = default


# --------------------------------------------------
# Sivupalkki vasemmalla
# --------------------------------------------------

with st.sidebar:
    st.markdown("## 🔧 Työpaja")

    st.warning(
        "🔒 **Tietoturva:** Viestit lähetetään OpenAI:lle käsiteltäväksi. "
        "Älä syötä henkilötietoja tai arkaluonteisia tietoja."
    )

    with st.expander("🔒 Lue lisää tietoturvasta", expanded=False):
        st.markdown(
            """
**Mihin viestit menevät?**

Tiro käyttää OpenAI:n kielimallia. Kaikki kirjoittamasi viestit
lähetetään OpenAI:n palveluun käsiteltäväksi vastausta varten.
Viestit voivat kulkea OpenAI:n palvelimien kautta esimerkiksi
Yhdysvalloissa.

**OpenAI:n tietoturva- ja yksityisyysperiaatteet:**  
[https://openai.com/fi-FI/security-and-privacy/](https://openai.com/fi-FI/security-and-privacy/)

**Mitä EI saa syöttää:**

- Henkilötietoja, kuten nimi, henkilötunnus, osoite, puhelinnumero,
  sähköposti tai syntymäaika.
- Tunnistettavia tietoja muista henkilöistä.
- Terveystietoja tai muita arkaluonteisia tietoja.
- Salasanoja, API-avaimia tai muita salaisuuksia.
- Salassa pidettävää työ- tai opiskelumateriaalia.

**Mitä voi syöttää:**

- Yleisiä opetustekstejä ja kuvauksia työvaiheista.
- Yleisluontoisia esimerkkejä ilman henkilöitä.
- Teknisiä termejä ja yleistä keskustelua aiheesta.

**Vinkki:**

Jos haluat käyttää esimerkkitilannetta, käytä keksittyjä henkilöitä
ja yleisiä paikkoja, esimerkiksi "asiakas tuo auton" tai
"oppilas korjaajakoulussa".

**Vastuu:**

Vastaat itse siitä, mitä syötät palveluun. Älä jaa tietoja, joita
et haluaisi ulkopuolisen näkevän.
            """
        )

    st.divider()

    with st.expander("📖 Käyttöohjeet", expanded=False):
        st.markdown(
            """
**Mikä Tiro on?**

Tiro on opetettava mekaanikko-oppilas. Hän ei ole opettaja, vaan oppilas.
Sinun tehtäväsi on opettaa hänelle valittu huoltotehtävä.

**Näin käytät bottia:**

1. Hyväksy tietoturvahuomio aloitusnäkymässä.
2. Valitse opeteltava aihe.
3. Lue Tiron aloitusviesti.
4. Kirjoita opetuksesi keskustelukenttään.
5. Vastaa Tiron jatkokysymyksiin.
6. Korjaa Tiroa, jos hän tekee virhepäätelmän.
7. Tarkista opeteltavat asiat oikeasta paneelista.
8. Pyydä Tiroa kokeilemaan taitojaan, kun olet valmis.

**Tavoite:**

Opeta Tirolle kaikki opeteltavat osa-alueet mahdollisimman selkeästi.
            """
        )

    st.divider()

    st.markdown("### 🚗 Aihe")

    topic_options = {k: v["display_name"] for k, v in TOPIC_CONFIGS.items()}

    selected_topic = st.selectbox(
        "Mitä Tiro opettelee?",
        options=list(topic_options.keys()),
        format_func=lambda k: topic_options[k],
        index=list(topic_options.keys()).index(st.session_state.current_topic),
        help=(
            "Valitse opetettava huoltotehtävä. "
            "Aiheen vaihtaminen aloittaa uuden keskustelun."
        ),
    )

    if selected_topic != st.session_state.current_topic:
        st.warning("Aihe vaihtuu vasta, kun painat alla olevaa nappia.")

        if st.button("🔄 Vaihda aihe", use_container_width=True):
            reset_session(selected_topic)
            st.rerun()

    st.divider()

    st.markdown("### ⚙️ Asetukset")

    with st.expander("ℹ️ Mitä asetukset tekevät?", expanded=False):
        st.markdown(
            """
**🧠 Päämalli**  
Valitsee, millä kielimallilla Tiro vastaa.  
`gpt-4o` on laadukkaampi, `gpt-4o-mini` nopeampi ja edullisempi.

**🌡️ Lämpötila**  
Säätää Tiron vastausten vaihtelevuutta.  
Pienempi arvo = vakaampi. Suositus Tirolle: `0.6`.

**🔁 Maks. vuoroja**  
Rajoittaa keskustelun pituutta ja auttaa hallitsemaan kustannuksia.  
Yksi vuoro = käyttäjän viesti + Tiron vastaus.
            """
        )

    st.session_state["main_model"] = st.selectbox(
        "🧠 Päämalli",
        ["gpt-4o", "gpt-4o-mini"],
        index=["gpt-4o", "gpt-4o-mini"].index(st.session_state["main_model"]),
    )

    st.session_state["temperature"] = st.slider(
        "🌡️ Lämpötila",
        min_value=0.0,
        max_value=1.2,
        value=float(st.session_state["temperature"]),
        step=0.1,
    )

    st.session_state["max_turns"] = st.number_input(
        "🔁 Maks. vuoroja",
        min_value=5,
        max_value=100,
        value=int(st.session_state["max_turns"]),
        step=5,
    )

    st.caption(
        "Asetusmuutokset vaikuttavat varmimmin, kun aloitat uuden keskustelun."
    )

    st.divider()

    if st.button("🔄 Aloita uusi keskustelu", use_container_width=True):
        if st.session_state.get("consent_given"):
            reset_session(st.session_state.current_topic)
            st.rerun()
        else:
            st.error("Hyväksy ensin tietoturvahuomio.")

    st.divider()

    st.caption("🔩 Tiro v1.0 — opetettava mekaanikko-oppilas")


# --------------------------------------------------
# Tietoturvasuostumus (näytetään ennen botin käyttöä)
# --------------------------------------------------

st.markdown("# 🔩 TIRO")

if not st.session_state.consent_given:
    st.markdown("### 🔒 Tietoturvahuomio")

    st.markdown(
        """
Tiro käyttää OpenAI:n kielimallia. Kaikki viestit, jotka kirjoitat,
**lähetetään OpenAI:n palveluun käsiteltäväksi**.

**Älä syötä:**
- henkilötietoja (oma tai muiden)
- terveystietoja tai muita arkaluonteisia tietoja
- salasanoja tai API-avaimia
- salassa pidettävää työ- tai opiskelumateriaalia

OpenAI:n tietoturva- ja yksityisyysperiaatteet löydät täältä:  
[https://openai.com/fi-FI/security-and-privacy/](https://openai.com/fi-FI/security-and-privacy/)

Vastuu siitä, mitä palveluun syötät, on käyttäjällä.
        """
    )

    consent = st.checkbox(
        "✅ Ymmärrän tietoturvaehdot ja sitoudun olemaan syöttämättä "
        "henkilötietoja tai arkaluonteisia tietoja.",
        value=False,
        key="consent_checkbox",
    )

    if st.button("🔓 Aloita käyttö", use_container_width=False):
        if consent:
            st.session_state.consent_given = True
            st.rerun()
        else:
            st.error("Sinun täytyy hyväksyä tietoturvaehdot jatkaaksesi.")

    st.stop()


# --------------------------------------------------
# Botin alustus
# --------------------------------------------------

if st.session_state.bot is None:
    reset_session(st.session_state.current_topic)


bot: TeachingBot = st.session_state.bot
topic_cfg = bot.config.topic_cfg
km = bot.knowledge_map
ratio = km.completion_ratio()


# --------------------------------------------------
# Otsikko ja banneri
# --------------------------------------------------

st.markdown(f"### `> Tehtävä: {topic_cfg['display_name']}`")

st.markdown(
    f"""
<div class="tiro-workshop-banner">
🔧 <b>Mekaanikko-oppilas Tiro</b> on tullut työpajalle oppimaan aihetta
<code>{topic_cfg['topic_text']}</code>. Sinä toimit kokeneempana opettajana.
Opeta, vastaile kysymyksiin ja korjaa Tiron virhepäätelmät.
</div>
""",
    unsafe_allow_html=True,
)


# --------------------------------------------------
# Vienti Markdowniksi
# --------------------------------------------------

def build_export_md() -> str:
    current_state = bot.knowledge_map.model_dump()
    current_ratio = bot.knowledge_map.completion_ratio()

    status_label = {
        "hallussa": "Hallussa",
        "osittain": "Osittain opittu",
        "tuntematon": "Ei vielä opetettu",
    }

    lines = [
        f"# Tiro — opetuskeskustelu: {topic_cfg['display_name']}",
        "",
        f"*Viety: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
        "",
        f"**Aihe:** {topic_cfg['topic_text']}  ",
        f"**Edistyminen:** {int(current_ratio * 100)} %  ",
        f"**Vuoroja:** {bot.turn_count}",
        "",
        "## Opeteltavat asiat",
        "",
    ]

    for area, status in current_state.items():
        readable_area = area.replace("_", " ").capitalize()
        readable_status = status_label.get(status, status)
        description = topic_cfg["areas"].get(area, area)

        lines.append(f"### {readable_area}")
        lines.append("")
        lines.append(f"- **Tila:** {readable_status}")
        lines.append(f"- **Kuvaus:** {description}")
        lines.append("")

    lines.append("## Keskustelu")
    lines.append("")

    for msg in st.session_state.messages:
        role = (
            "🔧 **Tiro**"
            if msg["role"] == "assistant"
            else "👷 **Opettaja**"
        )
        lines.append(f"### {role}")
        lines.append("")
        lines.append(msg["content"])
        lines.append("")

    if st.session_state.skill_test:
        lines.append("## Tiron taitokoe")
        lines.append("")
        lines.append(st.session_state.skill_test)
        lines.append("")

    if st.session_state.summary:
        lines.append("## Tiron yhteenveto")
        lines.append("")
        lines.append(st.session_state.summary)
        lines.append("")

    return "\n".join(lines)


# --------------------------------------------------
# Pääasettelu
# --------------------------------------------------

left_col, right_col = st.columns([2.2, 1], gap="large")


# --------------------------------------------------
# VASEN: Keskustelu
# --------------------------------------------------

with left_col:
    st.markdown("### 💬 Keskustelu työpajalla")

    st.caption(
        "🔒 Älä syötä henkilötietoja tai arkaluonteisia tietoja. "
        "Viestit lähetetään OpenAI:lle."
    )

    for msg in st.session_state.messages:
        avatar = "🔧" if msg["role"] == "assistant" else "👷"

        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Opeta Tiroa..."):
        st.session_state.messages.append(
            {"role": "user", "content": prompt}
        )

        with st.chat_message("user", avatar="👷"):
            st.markdown(prompt)

        with st.chat_message("assistant", avatar="🔧"):
            with st.spinner("⚙️ Tiro miettii..."):
                reply = bot.ask(prompt)

            st.markdown(reply)

        st.session_state.messages.append(
            {"role": "assistant", "content": reply}
        )

        st.rerun()

    if st.session_state.skill_test:
        st.divider()
        st.markdown("### 🎯 Tiron taitokoe")
        st.markdown(st.session_state.skill_test)
        st.caption(
            "Arvioi vastausta seuraavassa viestissä: kerro Tirolle, "
            "mikä meni oikein ja mitä pitää vielä opetella."
        )

    if st.session_state.summary:
        st.divider()
        st.markdown("### 📝 Tiron yhteenveto")
        st.markdown(st.session_state.summary)


# --------------------------------------------------
# OIKEA: Opeteltavat asiat ja toiminnot
# --------------------------------------------------

with right_col:
    st.markdown(
        """
        <div class="right-workshop-panel">
            <h3>🔧 Opeteltavat asiat</h3>
            <div class="right-panel-note">
                Osa-alueet, jotka Tiron pitäisi oppia tässä keskustelussa.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    status_emoji = {
        "hallussa": "✅",
        "osittain": "🟡",
        "tuntematon": "⚫",
    }

    status_label = {
        "hallussa": "Hallussa",
        "osittain": "Osittain opittu",
        "tuntematon": "Ei vielä opetettu",
    }

    state = km.model_dump()

    with st.expander("Näytä opeteltavat asiat", expanded=False):
        for area, status in state.items():
            emoji = status_emoji.get(status, "❓")
            readable_status = status_label.get(status, status)
            description = topic_cfg["areas"].get(area, area)
            readable_area = area.replace("_", " ").capitalize()

            st.markdown(
                f"""
                <div class="learning-card">
                    <div class="learning-card-title">
                        {emoji} {readable_area}
                    </div>
                    <div class="learning-card-status">
                        <b>Tila:</b> {readable_status}
                    </div>
                    <div class="learning-card-desc">
                        {description}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.caption(f"⏱️ Vuoro {bot.turn_count} / {bot.config.max_turns}")

    st.divider()

    st.markdown(
        """
        <div class="right-workshop-panel">
            <h3>🛠️ Toiminnot</h3>
            <div class="right-panel-note">
                Pyydä yhteenveto, anna Tiron kokeilla taitojaan tai vie keskustelu.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button(
        "📝 Pyydä yhteenveto",
        use_container_width=True,
        disabled=len(st.session_state.messages) < 2,
    ):
        with st.spinner("Tiro tekee yhteenvetoa..."):
            st.session_state.summary = bot.final_summary()

        st.rerun()

    if st.button(
        "🎯 Tiro kokeilee taitojaan",
        use_container_width=True,
        disabled=len(st.session_state.messages) < 2,
    ):
        with st.spinner("Tiro kokoaa ajatuksiaan..."):
            st.session_state.skill_test = bot.skill_test()

        st.rerun()

    filename = (
        f"tiro_{st.session_state.current_topic}_"
        f"{datetime.now().strftime('%Y%m%d_%H%M')}.md"
    )

    st.download_button(
        label="💾 Vie keskustelu tiedostona",
        data=build_export_md(),
        file_name=filename,
        mime="text/markdown",
        use_container_width=True,
        disabled=len(st.session_state.messages) < 2,
    )
