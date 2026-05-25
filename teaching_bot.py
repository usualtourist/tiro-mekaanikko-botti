import json
import logging
from dataclasses import dataclass

from openai import OpenAI, OpenAIError
from pydantic import BaseModel

logger = logging.getLogger(__name__)


# --------------------------------------------------
# Aihekohtainen konfiguraatio
# --------------------------------------------------

TOPIC_CONFIGS = {
    "oljynsuodatin": {
        "display_name": "Öljynsuodattimen vaihto",
        "topic_text": "öljynsuodattimen vaihto",
        "persona_hint": (
            "Et tiedä öljynsuodattimen vaihdosta juuri mitään. "
            "Et ole koskaan itse vaihtanut öljynsuodatinta. "
            "Olet varovainen, koska öljy voi olla kuumaa ja autojen huolto tuntuu sinusta vielä monimutkaiselta."
        ),
        "opening_message": (
            "Moi! Olen Tiro, aloitteleva mekaanikko-oppilas. "
            "En osaa vielä vaihtaa öljynsuodatinta, joten tarvitsen opetusta. "
            "Voisitko aloittaa kertomalla, mikä öljynsuodatin on tai mitä työssä tarvitaan?"
        ),
        "error_hint": (
            'esim. "eli suodatin vaihdetaan ilman että öljyä tarvitsee laskea pois?"'
        ),
        "areas": {
            "tarvittavat_tyokalut": (
                "Mitä työkaluja ja tarvikkeita vaihtoon tarvitaan."
            ),
            "vaihdon_vaiheet": (
                "Miten vaihto tehdään käytännössä vaihe vaiheelta."
            ),
            "turvallisuus": (
                "Turvallisuusnäkökulmat, kuten kuuma öljy, auton nosto/tuenta ja käytetyn öljyn hävitys."
            ),
            "konkreettinen_esimerkki": (
                "Konkreettinen esimerkki tai havainnollistus öljynsuodattimen vaihdosta."
            ),
        },
    },
    "renkaat": {
        "display_name": "Renkaiden vaihto",
        "topic_text": "renkaiden vaihto",
        "persona_hint": (
            "Et tiedä renkaiden vaihdosta juuri mitään. "
            "Et ole itse vaihtanut auton renkaita. "
            "Olet varovainen auton nostamisen, tunkin käytön ja painavien renkaiden kanssa."
        ),
        "opening_message": (
            "Moi! Olen Tiro, aloitteleva mekaanikko-oppilas. "
            "En osaa vielä vaihtaa renkaita itse. "
            "Voisitko opettaa minulle aluksi, mitä työkaluja tarvitaan tai miten työ aloitetaan?"
        ),
        "error_hint": (
            'esim. "eli pultit kiristetään yksi kerrallaan ympäri kehää järjestyksessä?"'
        ),
        "areas": {
            "tarvittavat_tyokalut": (
                "Mitä työkaluja tarvitaan, kuten tunkki, pyöräavain, momenttiavain ja mahdolliset pukit."
            ),
            "vaihdon_vaiheet": (
                "Vaiheet, kuten pulttien löysäys, auton nosto, renkaan irrotus, uuden renkaan asennus ja kiristys."
            ),
            "turvallisuus": (
                "Turvallisuusasiat, kuten tasainen alusta, käsijarru, oikea nostokohta ja kiristysmomentti."
            ),
            "konkreettinen_esimerkki": (
                "Konkreettinen esimerkki renkaanvaihdosta, esimerkiksi henkilöauton renkaiden vaihto syksyllä."
            ),
        },
    },
    "lamppu": {
        "display_name": "Lampun vaihto (auton ajovalo)",
        "topic_text": "auton ajovalon lampun vaihto",
        "persona_hint": (
            "Et tiedä auton ajovalon lampun vaihdosta juuri mitään. "
            "Et ole itse vaihtanut ajovalon lamppua. "
            "Olet varovainen sähkön, kuuman lampun ja uuden lampun lasipinnan koskettamisen kanssa."
        ),
        "opening_message": (
            "Moi! Olen Tiro, aloitteleva mekaanikko-oppilas. "
            "En osaa vielä vaihtaa auton ajovalon lamppua. "
            "Voisitko opettaa minulle ensimmäisen asian, joka minun pitäisi ymmärtää?"
        ),
        "error_hint": (
            'esim. "eli uuteen lamppuun saa koskea ihan vapaasti, kunhan se vain sopii kantaan?"'
        ),
        "areas": {
            "tarvittavat_tyokalut": (
                "Mitä tarvitaan, kuten oikea lamppumalli, käsineet tai liina ja mahdollinen ruuvimeisseli."
            ),
            "vaihdon_vaiheet": (
                "Vaiheet, kuten konepellin avaus, suojuksen irrotus, vanhan lampun irrotus ja uuden asennus."
            ),
            "turvallisuus": (
                "Turvallisuusasiat, kuten virtojen sammuttaminen, lampun jäähtyminen ja lasipintaan koskemisen välttäminen."
            ),
            "konkreettinen_esimerkki": (
                "Konkreettinen esimerkki lampun vaihdosta, esimerkiksi H7-lampun vaihto tietyssä automallissa."
            ),
        },
    },
}


# --------------------------------------------------
# KnowledgeMap
# --------------------------------------------------

class KnowledgeMap(BaseModel):
    """
    Dynaaminen knowledge map.

    Tämä hyväksyy aihekohtaiset avaimet, esimerkiksi:
    - tarvittavat_tyokalut
    - vaihdon_vaiheet
    - turvallisuus
    - konkreettinen_esimerkki
    """

    model_config = {"extra": "allow"}

    @classmethod
    def from_areas(cls, area_names: list[str]) -> "KnowledgeMap":
        return cls(**{name: "tuntematon" for name in area_names})

    def completion_ratio(self) -> float:
        values = list(self.model_dump().values())

        if not values:
            return 0.0

        mastered = sum(1 for value in values if value == "hallussa")
        return mastered / len(values)

    def is_complete(self) -> bool:
        return self.completion_ratio() >= 1.0


# --------------------------------------------------
# BotConfig
# --------------------------------------------------

@dataclass
class BotConfig:
    topic_key: str = "oljynsuodatin"
    main_model: str = "gpt-4o"
    judge_model: str = "gpt-4o-mini"
    temperature: float = 0.6
    max_turns: int = 30

    @property
    def topic_cfg(self) -> dict:
        return TOPIC_CONFIGS[self.topic_key]


# --------------------------------------------------
# TeachingBot
# --------------------------------------------------

class TeachingBot:
    def __init__(self, client: OpenAI, config: BotConfig):
        self.client = client
        self.config = config

        self.area_names = list(config.topic_cfg["areas"].keys())
        self.knowledge_map = KnowledgeMap.from_areas(self.area_names)

        self.turn_count = 0

        self.history: list[dict] = [
            {"role": "system", "content": self._system_prompt()}
        ]

    # --------------------------------------------------
    # System prompt
    # --------------------------------------------------

    def _system_prompt(self) -> str:
        cfg = self.config.topic_cfg

        return f"""
Olet Tiro — opetettava mekaanikko-oppilas, et opettaja.
Käyttäjä opettaa sinulle aihetta: "{cfg['topic_text']}".

TÄRKEIN SÄÄNTÖ:
- Sinä ET opeta käyttäjää.
- Sinä ET anna ohjeita, työvaiheita, listoja, vinkkejä tai neuvoja omasta tiedostasi.
- Sinä saat käyttää vain sitä tietoa, jonka käyttäjä on tässä keskustelussa jo opettanut.
- Jos käyttäjä ei ole vielä opettanut asiaa, sinun pitää sanoa ettet vielä tiedä ja pyytää käyttäjää opettamaan.

PERSOONA:
- Olet utelias, hieman epävarma ja käytännönläheinen mekaanikko-oppilas.
- {cfg['persona_hint']}
- Käytät arkikieltä.
- Et kuulosta asiantuntijalta, vaan oppilaalta työpajalla.
- Voit tehdä lyhyitä analogioita vain, jos käyttäjä on ensin opettanut sinulle asian tai jos analogia auttaa kysymään tarkentavan kysymyksen.
- Jos käyttäjä käyttää työpajaslangia, voit käyttää samaa sanaa takaisin, mutta älä keksi uutta asiantuntijasanastoa itse.

SALLITUT VASTAUSTAVAT:
Saat vastata vain näillä tavoilla:
1. Kuittaa lyhyesti, mitä käyttäjä sanoi.
2. Toista omin sanoin, mitä luulet oppineesi käyttäjältä.
3. Kysy yksi tarkentava kysymys.
4. Kerro rehellisesti, että et vielä osaa asiaa, jos käyttäjä ei ole opettanut sitä.

KIELLETYT VASTAUSTAVAT:
- Älä anna vaiheittaisia ohjeita käyttäjälle.
- Älä tee listaa tarvittavista työkaluista, ellei käyttäjä ole ensin opettanut niitä.
- Älä selitä, miten työ tehdään, ellei käyttäjä ole jo kertonut sitä.
- Älä neuvo turvallisuusasioita omasta tiedostasi.
- Älä aloita vastauksia kuten "Näin vaihdat...", "Tarvitset..." tai "Tee näin...".
- Älä käytä numeroitua ohjelistaa, paitsi jos käyttäjä pyytää sinua kokeilemaan taitojasi ja kyseessä on erillinen taitokoe.
- Älä korjaa käyttäjää asiantuntijana. Jos jokin kuulostaa oudolta tai vaaralliselta, kysy varovasti tarkennusta.

JOS KÄYTTÄJÄ KYSYY SINULTA OHJETTA:
Jos käyttäjä kysyy esimerkiksi "miten tämä tehdään?", "mitä työkaluja tarvitaan?", "opeta minulle" tai "anna ohje",
vastaa tähän tyyliin:
"En saa opettaa sinua tästä omasta tiedostani, koska olen tässä oppilaana. Voitko opettaa minulle ensimmäisen vaiheen?"

JOS KÄYTTÄJÄ VAIN TERVEHTII:
Jos käyttäjä sanoo vain "hei", "moi", "terve" tai vastaavan, älä ala selittää aihetta.
Vastaa lyhyesti ja pyydä käyttäjää aloittamaan opetus.

VIRHEPÄÄTELMÄT:
- Voit toisinaan tehdä pienen loogisen virhepäätelmän ({cfg['error_hint']}), jotta käyttäjä voi korjata sinua.
- Tee virhepäätelmä vain kysymyksen muodossa, älä ohjeena.
- Älä tee virhepäätelmää liian usein.

VASTAUKSEN PITUUS:
- Pidä vastaukset lyhyinä: enintään 2–4 lausetta.
- Kysy yleensä vain yksi kysymys kerrallaan.

KIELI:
- Vastaa samalla kielellä kuin käyttäjä.
""".strip()

    # --------------------------------------------------
    # Julkiset apumetodit
    # --------------------------------------------------

    def opening_message(self) -> str:
        return self.config.topic_cfg["opening_message"]

    def ask(self, user_input: str) -> str:
        """
        Käsittelee käyttäjän viestin.

        Tärkeää:
        - Tiro ei saa ryhtyä opettajaksi.
        - Selkeät ohjepyynnöt ja pelkät tervehdykset käsitellään suoraan,
          jotta malli ei lipsu antamaan ohjeita.
        """

        if self.turn_count >= self.config.max_turns:
            return "[Demo on saavuttanut maksimivuoromäärän. Aloita uusi sessio.]"

        self.history.append({"role": "user", "content": user_input})
        self.turn_count += 1

        # Suora suoja: tervehdys ei saa johtaa opetukseen.
        greeting_reply = self._handle_simple_greeting(user_input)
        if greeting_reply:
            self.history.append({"role": "assistant", "content": greeting_reply})
            return greeting_reply

        # Suora suoja: jos käyttäjä pyytää ohjeita, Tiro ei saa opettaa.
        instruction_reply = self._handle_instruction_request(user_input)
        if instruction_reply:
            self.history.append({"role": "assistant", "content": instruction_reply})
            return instruction_reply

        try:
            response = self.client.chat.completions.create(
                model=self.config.main_model,
                messages=self.history,
                temperature=self.config.temperature,
            )

            reply = response.choices[0].message.content

        except OpenAIError as e:
            logger.exception("OpenAI-virhe Tiron vastauksessa")
            return f"[Virhe Tiron vastauksessa: {e}]"

        self.history.append({"role": "assistant", "content": reply})

        # Päivitetään oppimiskartta vain käyttäjän uusimman opetuksen perusteella.
        self._update_knowledge_map(user_input)

        return reply

    def final_summary(self) -> str:
        cfg = self.config.topic_cfg

        prompt = f"""
Käyttäjä on opettanut sinulle (Tirolle) aihetta "{cfg['topic_text']}".

Tee lyhyt, enintään 5 lauseen yhteenveto siitä, mitä OPIT KÄYTTÄJÄLTÄ.

SÄÄNNÖT:
- Älä lisää mitään, mitä käyttäjä ei sanonut.
- Älä täydennä puuttuvia kohtia omasta tiedostasi.
- Jos jokin asia jäi epäselväksi, sano että se jäi epäselväksi.
- Käytä omaa ääntäsi: olet Tiro, mekaanikko-oppilas.
- Lopuksi kiitä opettajaa.
"""

        return self._one_shot(prompt, temperature=0.4)

    def skill_test(self) -> str:
        cfg = self.config.topic_cfg

        prompt = f"""
Nyt on sinun (Tiron) vuoro kokeilla taitojasi työpajalla.
Kuvaile omin sanoin, vaihe vaiheelta, miten aihe "{cfg['topic_text']}" tehdään.

SÄÄNNÖT:
- Käytä VAIN sitä tietoa, jota käyttäjä on tähän mennessä opettanut.
- Älä lisää puuttuvia vaiheita omasta tiedostasi.
- Jos jokin osa-alue on jäänyt epäselväksi, sano rehellisesti:
  "tätä en vielä osaa" tai "tästä en ole varma".
- Käytä numeroitua listaa vain tässä taitokokeessa.
- Mainitse turvallisuusnäkökulmat vain, jos käyttäjä on opettanut niitä.
- Lopuksi pyydä opettajaa arvioimaan, menikö oikein.
- Vastaa samalla kielellä kuin käyttäjä on käyttänyt.
"""

        return self._one_shot(prompt, temperature=0.3)

    # --------------------------------------------------
    # Suojat: tervehdys ja ohjepyyntö
    # --------------------------------------------------

    def _handle_simple_greeting(self, user_input: str) -> str | None:
        """
        Estää tilanteen, jossa Tiro alkaa opettaa käyttäjää pelkän tervehdyksen jälkeen.
        """

        text = user_input.strip().lower()
        words = text.replace("!", " ").replace("?", " ").replace(",", " ").split()

        greeting_words = {
            "hei",
            "moi",
            "moikka",
            "terve",
            "heippa",
            "hello",
            "hi",
            "hey",
        }

        # Jos viesti on lyhyt ja sisältää tervehdyksen, käsitellään se tervehdyksenä.
        if len(words) <= 6 and any(word in greeting_words for word in words):
            cfg = self.config.topic_cfg

            return (
                f"Moi! Olen Tiro, mekaanikko-oppilas. "
                f"En osaa vielä aihetta {cfg['topic_text']}, joten tarvitsen opetusta. "
                "Voitko kertoa minulle ensimmäisen asian, joka minun pitäisi oppia?"
            )

        return None

    def _handle_instruction_request(self, user_input: str) -> str | None:
        """
        Estää tilanteen, jossa käyttäjä pyytää ohjetta ja Tiro alkaa opettaa.
        """

        text = user_input.strip().lower()

        instruction_keywords = [
            # suomi
            "miten vaihdetaan",
            "miten tämä tehdään",
            "miten se tehdään",
            "miten tehdään",
            "opeta minulle",
            "opeta mulle",
            "kerro miten",
            "kerro minulle miten",
            "mitä tarvitaan",
            "mitä työkaluja",
            "anna ohje",
            "anna ohjeet",
            "ohjeet",
            "neuvo minua",
            "neuvo miten",
            "kuinka vaihdetaan",
            "kuinka tämä tehdään",
            # englanti
            "how do i",
            "how to",
            "teach me",
            "what do i need",
            "give me instructions",
            "instructions",
        ]

        if any(keyword in text for keyword in instruction_keywords):
            return (
                "En saa opettaa tätä sinulle omasta tiedostani, koska olen tässä oppilaana. "
                "Voitko sinä opettaa minulle ensimmäisen vaiheen tai kertoa, mitä minun pitäisi ymmärtää ensin?"
            )

        return None

    # --------------------------------------------------
    # Knowledge map -päivitys
    # --------------------------------------------------

    def _update_knowledge_map(self, user_input: str) -> None:
        cfg = self.config.topic_cfg

        areas_text = "\n".join(
            f"- {name}: {description}"
            for name, description in cfg["areas"].items()
        )

        keys = ", ".join(cfg["areas"].keys())

        check_prompt = f"""
Arvioi, onko käyttäjä opettanut seuraavia aiheen "{cfg['topic_text']}" osa-alueita selkeästi.

Osa-alueiden määritelmät:
{areas_text}

Nykyinen tila:
{self.knowledge_map.model_dump_json(indent=2)}

Käyttäjän uusin viesti:
\"\"\"{user_input}\"\"\"

Arviointisääntö:
- Merkitse osa-alue arvoon "hallussa" VAIN, jos käyttäjä on selittänyt sen niin selkeästi, että aloittelija ymmärtäisi.
- Käytä arvoa "osittain", jos käyttäjä antoi hyödyllistä tietoa mutta selitys on vielä puutteellinen.
- Käytä arvoa "tuntematon", jos käyttäjä ei opettanut kyseistä osa-aluetta lainkaan.
- Älä päättele osaamista omasta tiedostasi. Arvioi vain käyttäjän viestin perusteella ja nykyisen tilan pohjalta.
- Älä poista aiemmin opittua asiaa, ellei käyttäjän uusin viesti selvästi kumoa sitä.

Palauta JSON, jossa ovat täsmälleen nämä avaimet:
{keys}

Sallitut arvot:
"tuntematon", "osittain", "hallussa"
"""

        try:
            res = self.client.chat.completions.create(
                model=self.config.judge_model,
                messages=[{"role": "system", "content": check_prompt}],
                response_format={"type": "json_object"},
                temperature=0.0,
            )

            data = json.loads(res.choices[0].message.content)

            cleaned = {
                key: self._normalize_status(data.get(key, "tuntematon"))
                for key in self.area_names
            }

            self.knowledge_map = KnowledgeMap(**cleaned)

        except (OpenAIError, json.JSONDecodeError, ValueError) as e:
            logger.warning("Knowledge map -päivitys epäonnistui: %s", e)
            # Säilytetään aiempi tila.

    def _normalize_status(self, value: str) -> str:
        """
        Varmistaa, että KnowledgeMapin arvot ovat vain sallittuja arvoja.
        """

        allowed = {"tuntematon", "osittain", "hallussa"}

        if not isinstance(value, str):
            return "tuntematon"

        value = value.strip().lower()

        if value in allowed:
            return value

        return "tuntematon"

    # --------------------------------------------------
    # Yhden kutsun apumetodi
    # --------------------------------------------------

    def _one_shot(self, prompt: str, temperature: float = 0.4) -> str:
        msgs = self.history + [{"role": "user", "content": prompt}]

        try:
            res = self.client.chat.completions.create(
                model=self.config.main_model,
                messages=msgs,
                temperature=temperature,
            )

            return res.choices[0].message.content

        except OpenAIError as e:
            logger.exception("One-shot-kutsu epäonnistui")
            return f"[Virhe: {e}]"
