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
    layout="centered",
)


# --------------------------------------------------
# Mekaanikkoteema: luettavampi vaalea työpajateema
# + hitaasti pyörivä hammasratas
# --------------------------------------------------

st.markdown(
    """
    <style>
    /* --------------------------------------------------
       Värit
    -------------------------------------------------- */

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

    /* --------------------------------------------------
       Yleinen sivupohja
    -------------------------------------------------- */

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
        background-color: rgba(255, 255, 255, 0.78);
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

    /* --------------------------------------------------
       Sivupalkki
    -------------------------------------------------- */

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

    /* --------------------------------------------------
       Yläbanneri
    -------------------------------------------------- */

    .tiro-workshop-banner {
        background: linear-gradient(90deg, #fff8ed, #ffffff);
        border: 1px solid var(--workshop-border);
        border-left: 7px solid var(--workshop-orange);
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 5px 18px rgba(31, 41, 51, 0.07);
        color: var(--workshop-text);
        line-height: 1.55;
    }

    .tiro-workshop-banner b {
        color: var(--workshop-dark);
    }

    /* --------------------------------------------------
       Chat-viestit
    -------------------------------------------------- */

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

    /* --------------------------------------------------
       Napit
    -------------------------------------------------- */

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

    /* --------------------------------------------------
       Syötteet, valikot ja chat input
    -------------------------------------------------- */

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

    /* --------------------------------------------------
       Progress bar
    -------------------------------------------------- */

    [data-testid="stProgress"] {
        background-color: #eee3d1;
        border-radius: 999px;
    }

    [data-testid="stProgressBar"] > div > div {
        background: linear-gradient(90deg, #e67e22, #f5b041) !important;
    }

    /* --------------------------------------------------
       Expanderit, alertit ja erotinviivat
    -------------------------------------------------- */

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

    /* --------------------------------------------------
       Opeteltavat asiat -kortit
    -------------------------------------------------- */

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
        font-size: 1.05rem;
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
    }

    /* --------------------------------------------------
       Hitaasti pyörivä hammasratas taustalla
    -------------------------------------------------- */

    .gear-background {
        position: fixed;
        right: -90px;
        bottom: -90px;
        width: 360px;
        height: 360px;
        z-index: 0;
        pointer-events: none;
        opacity: 0.085;
        animation: rotateGear 42s linear infinite;
    }

    .gear-background svg {
        width: 100%;
        height: 100%;
        fill: #263238;
    }

    @keyframes rotateGear {
        from {
            transform: rotate(0deg);
        }
        to {
            transform: rotate(360deg);
        }
    }

    [data-testid="stAppViewContainer"],
    [data-testid="stHeader"],
    [data-testid="stToolbar"],
    [data-testid="stSidebar"] {
        position: relative;
        z-index: 1;
    }

    @media (max-width: 768px) {
        .gear-background {
            width: 220px;
            height: 220px;
            right: -65px;
            bottom: -65px;
            opacity: 0.06;
        }

        .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }
    }
    </style>

    <div class="gear-background" aria-hidden="true">
        <svg viewBox="0 0 512 512">
            <path d="M487.4 315.7l-42.6-24.6c2.4-11.4 3.7-23.1 3.7-35.1s-1.3-23.7-3.7-35.1l42.6-24.6c7.8-4.5 11.2-14 8.1-22.4l-21.4-58.7c-3.1-8.4-11.9-13.3-20.7-11.5l-48.1 9.8c-16.9-20.1-37.9-36.9-61.8-49.2L338.4 16c-.9-9-8.4-16-17.5-16h-64c-9.1 0-16.6 7-17.5 16l-5.1 48.3c-23.9 12.3-44.9 29.1-61.8 49.2l-48.1-9.8c-8.8-1.8-17.6 3.1-20.7 11.5l-21.4 58.7c-3.1 8.4.3 17.9 8.1 22.4l42.6 24.6c-2.4 11.4-3.7 23.1-3.7 35.1s1.3 23.7 3.7 35.1l-42.6 24.6c-7.8 4.5-11.2 14-8.1 22.4l21.4 58.7c3.1 8.4 11.9 13.3 20.7 11.5l48.1-9.8c16.9 20.1 37.9 36.9 61.8 49.2l5.1 48.3c.9 9 8.4 16 17.5 16h64c9.1 0 16.6-7 17.5-16l5.1-48.3c23.9-12.3 44.9-29.1 61.8-49.2l48.1 9.8c8.8 1.8 17.6-3.1 20.7-11.5l21.4-58.7c3.1-8.4-.3-17.9-8.1-22.4zM288.9 336c-44.2 0-80-35.8-80-80s35.8-80 80-80 80 35.8 80 80-35.8 80-80 80z"/>
        </svg>
    </div>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# API-avain
# --------------------------------------------------

def get_api_key() -> str | None:
    """
    Hakee API-avaimen ensisijaisesti Streamlit secretsistä.
    Jos secrets.toml puuttuu, käytetään .env-tiedostoa / ympäristömuuttujaa.
    """
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
        temperature=st.session_state.get("temperature", 0.8),
        max_turns=st.session_state.get("max_turns", 30),
    )

    return TeachingBot(client, config)


def reset_session(topic_key: str) -> None:
    """
    Aloittaa uuden opetussession valitulla aiheella.
    """
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
    ("temperature", 0.8),
    ("max_turns", 30),
]:
    if key not in st.session_state:
        st.session_state[key] = default


# --------------------------------------------------
# Sivupalkki
# --------------------------------------------------

with st.sidebar:
    st.markdown("## 🔧 Työpaja")

    with st.expander("📖 Käyttöohjeet", expanded=False):
        st.markdown(
            """
**Mikä Tiro on?**

Tiro on opetettava mekaanikko-oppilas. Hän ei tiedä aiheesta juuri mitään,
vaan oppii sen, mitä sinä hänelle opetat.

**Näin käytät bottia:**

1. Valitse opeteltava aihe.
2. Lue Tiron aloitusviesti.
3. Kirjoita opetuksesi keskustelukenttään.
4. Vastaa Tiron jatkokysymyksiin.
5. Korjaa Tiroa, jos hän tekee virhepäätelmän.
6. Seuraa oppimisedistymistä keskustelun alla.
7. Kun haluat, pyydä Tiroa kokeilemaan taitojaan.

**Tavoite:**

Opeta Tirolle kaikki opeteltavat osa-alueet niin selkeästi, että
oppimisedistyminen saavuttaa 100 %.
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

Päämalli on kielimalli, jota Tiro käyttää vastatessaan keskustelussa.

- `gpt-4o` — laadukkaampi, usein parempi päättelyssä.
- `gpt-4o-mini` — nopeampi ja edullisempi, mutta hieman yksinkertaisempi.

**🌡️ Lämpötila**

Lämpötila säätää, kuinka vaihtelevasti ja luovasti Tiro vastaa.

- `0.0–0.3` — hyvin vakaa ja johdonmukainen.
- `0.4–0.7` — tasapainoinen.
- `0.8–1.0` — uteliaampi ja vaihtelevampi.
- `1.0–1.2` — voi olla luova, mutta myös rönsyilevä.

**🔁 Maks. vuoroja**

Yksi vuoro tarkoittaa yhtä käyttäjän viestiä ja yhtä Tiron vastausta.

Tämä raja suojaa API-kustannuksilta. Kun raja tulee täyteen,
Tiro ei enää vastaa ennen uuden keskustelun aloittamista.

**Huomio:**

Jos muutat asetuksia kesken keskustelun, ne tulevat varmasti käyttöön,
kun aloitat uuden keskustelun.
            """
        )

    st.session_state["main_model"] = st.selectbox(
        "🧠 Päämalli",
        ["gpt-4o", "gpt-4o-mini"],
        index=["gpt-4o", "gpt-4o-mini"].index(st.session_state["main_model"]),
        help=(
            "Kielimalli, jota Tiro käyttää. "
            "gpt-4o on laadukkaampi, gpt-4o-mini nopeampi ja edullisempi."
        ),
    )

    st.session_state["temperature"] = st.slider(
        "🌡️ Lämpötila",
        min_value=0.0,
        max_value=1.2,
        value=float(st.session_state["temperature"]),
        step=0.1,
        help=(
            "Säätää Tiron luovuutta. "
            "Matala arvo tekee vastauksista vakaampia, korkea vaihtelevampia."
        ),
    )

    st.session_state["max_turns"] = st.number_input(
        "🔁 Maks. vuoroja",
        min_value=5,
        max_value=100,
        value=int(st.session_state["max_turns"]),
        step=5,
        help=(
            "Kuinka monta käyttäjän viestiä sessiossa sallitaan. "
            "Tämä auttaa rajaamaan kustannuksia."
        ),
    )

    st.caption(
        "Asetusmuutokset vaikuttavat varmimmin, kun aloitat uuden keskustelun."
    )

    st.divider()

    if st.button("🔄 Aloita uusi keskustelu", use_container_width=True):
        reset_session(st.session_state.current_topic)
        st.rerun()

    st.divider()

    st.caption("🔩 Tiro v1.0 — opetettava mekaanikko-oppilas")


# --------------------------------------------------
# Alusta botti, jos sitä ei vielä ole
# --------------------------------------------------

if st.session_state.bot is None:
    reset_session(st.session_state.current_topic)


bot: TeachingBot = st.session_state.bot
topic_cfg = bot.config.topic_cfg
km = bot.knowledge_map
ratio = km.completion_ratio()


# --------------------------------------------------
# Otsikko ja kuvaus
# --------------------------------------------------

st.markdown("# 🔩 TIRO")
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

st.write("")


# --------------------------------------------------
# Keskustelu
# --------------------------------------------------

st.markdown("### 💬 Keskustelu työpajalla")

for msg in st.session_state.messages:
    avatar = "🔧" if msg["role"] == "assistant" else "👷"

    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])


# --------------------------------------------------
# Käyttäjän syöte
# --------------------------------------------------

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


# --------------------------------------------------
# Toiminnot
# --------------------------------------------------

st.divider()
st.markdown("### 🛠️ Toiminnot")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button(
        "📝 Pyydä yhteenveto",
        use_container_width=True,
        disabled=len(st.session_state.messages) < 2,
    ):
        with st.spinner("Tiro tekee yhteenvetoa..."):
            st.session_state.summary = bot.final_summary()

        st.rerun()

with col2:
    if st.button(
        "🎯 Tiro kokeilee taitojaan",
        use_container_width=True,
        disabled=len(st.session_state.messages) < 2,
    ):
        with st.spinner("Tiro kokoaa ajatuksiaan..."):
            st.session_state.skill_test = bot.skill_test()

        st.rerun()

with col3:
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

    filename = (
        f"tiro_{st.session_state.current_topic}_"
        f"{datetime.now().strftime('%Y%m%d_%H%M')}.md"
    )

    st.download_button(
        label="💾 Vie keskustelu (.md)",
        data=build_export_md(),
        file_name=filename,
        mime="text/markdown",
        use_container_width=True,
        disabled=len(st.session_state.messages) < 2,
    )


# --------------------------------------------------
# Oppimisedistyminen ja opeteltavat asiat
# --------------------------------------------------

st.divider()
st.markdown("### 📊 Tiron oppimisedistyminen")

km = bot.knowledge_map
ratio = km.completion_ratio()

st.progress(
    ratio,
    text=f"Edistyminen: {int(ratio * 100)} %",
)

with st.expander("🔧 Opeteltavat asiat", expanded=True):
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


# --------------------------------------------------
# Oppimisen tilaviesti
# --------------------------------------------------

if km.is_complete():
    st.success("🎉 Tiro on oppinut kaikki osa-alueet. Hyvää työtä, mestari.")
elif ratio >= 0.5:
    st.info("🔧 Tiro on oppimassa hyvin. Jatka opettamista.")
else:
    st.warning("🛠️ Tirolla on vielä paljon opittavaa.")


# --------------------------------------------------
# Taitokoe ja yhteenveto
# --------------------------------------------------

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
