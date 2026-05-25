import json
import logging
from dataclasses import dataclass
from openai import OpenAI, OpenAIError
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ---------- Aihekohtainen konfiguraatio ----------

TOPIC_CONFIGS = {
    "oljynsuodatin": {
        "display_name": "Öljynsuodattimen vaihto",
        "topic_text": "öljynsuodattimen vaihto",
        "persona_hint": (
            "Et tiedä öljynsuodattimen vaihdosta juuri mitään. "
            "Käytät analogioita kuten kahvinsuodatin tai vesihana. "
            "Olet varovainen kuuman öljyn suhteen."
        ),
        "opening_message": (
            "Moi! Olen Tiro, aloitteleva mekaanikko-oppilas. "
            "Olen kuullut, että autossa pitää joskus vaihtaa öljynsuodatin, "
            "mutta en ole ihan varma mikä se edes on. "
            "Voisitko opettaa minulle, mistä aloitetaan?"
        ),
        "error_hint": (
            'esim. "eli suodatin vaihdetaan ilman että öljyä tarvitsee laskea pois?"'
        ),
        "areas": {
            "tarvittavat_tyokalut": "Mitä työkaluja ja tarvikkeita vaihtoon tarvitaan.",
            "vaihdon_vaiheet": "Miten vaihto tehdään käytännössä vaihe vaiheelta.",
            "turvallisuus": "Turvallisuusnäkökulmat (kuuma öljy, nosto, hävitys).",
            "konkreettinen_esimerkki": "Esimerkki tai havainnollistus.",
        },
    },
    "renkaat": {
        "display_name": "Renkaiden vaihto",
        "topic_text": "renkaiden vaihto",
        "persona_hint": (
            "Et tiedä renkaiden vaihdosta juuri mitään. "
            "Käytät analogioita kuten polkupyörän rengas. "
            "Olet varovainen auton nostamisen ja painavien renkaiden suhteen."
        ),
        "opening_message": (
            "Moi! Olen Tiro, aloitteleva mekaanikko-oppilas. "
            "Olen kuullut, että renkaat pitää vaihtaa kaksi kertaa vuodessa "
            "kesä- ja talvirenkaisiin, mutta en tiedä miten se tehdään. "
            "Mistä aloitetaan?"
        ),
        "error_hint": (
            'esim. "eli pultit kiristetään yksi kerrallaan ympäri kehää järjestyksessä?"'
        ),
        "areas": {
            "tarvittavat_tyokalut": "Mitä työkaluja tarvitaan (tunkki, pyöräavain, momenttiavain, pukit).",
            "vaihdon_vaiheet": "Vaiheet (pulttien löysäys, nosto, irrotus, asennus, kiristys).",
            "turvallisuus": "Turvallisuus (tasainen alusta, käsijarru, oikea nostokohta, kiristysmomentti).",
            "konkreettinen_esimerkki": "Esimerkki (esim. henkilöauton renkaanvaihto syksyllä).",
        },
    },
    "lamppu": {
        "display_name": "Lampun vaihto (auton ajovalo)",
        "topic_text": "auton ajovalon lampun vaihto",
        "persona_hint": (
            "Et tiedä ajovalon lampun vaihdosta juuri mitään. "
            "Käytät analogioita kuten kotilampun vaihto. "
            "Olet varovainen, koska et halua koskea uuteen lamppuun paljain käsin."
        ),
        "opening_message": (
            "Moi! Olen Tiro, aloitteleva mekaanikko-oppilas. "
            "Auton ajovalo paloi rikki ja minulle sanottiin, että lampun "
            "voi vaihtaa itse. Mutta miten se eroaa kotona vaihdettavasta "
            "lampusta? Mistä aloitetaan?"
        ),
        "error_hint": (
            'esim. "eli uuteen lamppuun saa koskea ihan vapaasti, kunhan se vain sopii kantaan?"'
        ),
        "areas": {
            "tarvittavat_tyokalut": "Mitä tarvitaan (oikea lamppumalli, käsineet/liina, mahd. ruuvimeisseli).",
            "vaihdon_vaiheet": "Vaiheet (konepellin avaus, suojuksen irrotus, vanhan lampun irrotus, uuden asennus).",
            "turvallisuus": "Turvallisuus (virrat pois, lampun jäähtyminen, lasiin ei kosketa paljain käsin).",
            "konkreettinen_esimerkki": "Esimerkki (esim. H7-lampun vaihto tietyssä automallissa).",
        },
    },
}


class KnowledgeMap(BaseModel):
    """Dynaaminen knowledge map: hyväksyy mitkä tahansa avaimet."""
    model_config = {"extra": "allow"}

    @classmethod
    def from_areas(cls, area_names: list[str]) -> "KnowledgeMap":
        return cls(**{name: "tuntematon" for name in area_names})

    def completion_ratio(self) -> float:
        values = list(self.model_dump().values())
        if not values:
            return 0.0
        mastered = sum(1 for v in values if v == "hallussa")
        return mastered / len(values)

    def is_complete(self) -> bool:
        return self.completion_ratio() >= 1.0


@dataclass
class BotConfig:
    topic_key: str = "oljynsuodatin"
    main_model: str = "gpt-4o"
    judge_model: str = "gpt-4o-mini"
    temperature: float = 0.8
    max_turns: int = 30

    @property
    def topic_cfg(self) -> dict:
        return TOPIC_CONFIGS[self.topic_key]


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

    def _system_prompt(self) -> str:
        cfg = self.config.topic_cfg
        return f"""
Olet Tiro — utelias mekaanikko-oppilas, joka opettelee autoalan perustaitoja.
Käyttäjä on kokeneempi mekaanikko, joka opettaa sinulle aihetta: "{cfg['topic_text']}".

PERSOONA:
- {cfg['persona_hint']}
- Käytät arkikieltä ja teet luontevia analogioita arjesta.
- Esität tarkentavia kysymyksiä ("miksi?", "mitä tapahtuu jos…?", "missä se sijaitsee?").
- Jos selitys on epäselvä, pyydät yksinkertaisempaa selitystä tai esimerkkiä.
- Käytät joskus työpajaslangia kuullessasi sitä opettajalta, mutta et keksi sitä itse.

SÄÄNNÖT:
1. ÄLÄ KOSKAAN selitä aihetta käyttäjälle valmiina tietona.
2. Älä paljasta tietäväsi enempää kuin käyttäjä on opettanut.
3. Tee toisinaan pieni looginen virhepäätelmä ({cfg['error_hint']}), jotta käyttäjä joutuu korjaamaan sinua.
4. Pidä vastaukset lyhyinä (max 3–4 lausetta).
5. Vastaa samalla kielellä kuin käyttäjä.
""".strip()

    def opening_message(self) -> str:
        return self.config.topic_cfg["opening_message"]

    def ask(self, user_input: str) -> str:
        if self.turn_count >= self.config.max_turns:
            return "[Demo on saavuttanut maksimivuoromäärän. Aloita uusi sessio.]"

        self.history.append({"role": "user", "content": user_input})
        self.turn_count += 1

        try:
            response = self.client.chat.completions.create(
                model=self.config.main_model,
                messages=self.history,
                temperature=self.config.temperature,
            )
            reply = response.choices[0].message.content
        except OpenAIError as e:
            logger.exception("OpenAI-virhe")
            return f"[Virhe Tiron vastauksessa: {e}]"

        self.history.append({"role": "assistant", "content": reply})
        self._update_knowledge_map(user_input)
        return reply

    def _update_knowledge_map(self, user_input: str) -> None:
        cfg = self.config.topic_cfg
        areas_text = "\n".join(
            f"- {name}: {desc}" for name, desc in cfg["areas"].items()
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

Sääntö: Merkitse osa-alue arvoon "hallussa" VAIN, jos käyttäjä on selittänyt
sen niin selkeästi, että aloittelija ymmärtäisi. Muuten "tuntematon" tai "osittain".

Palauta JSON, jossa ovat täsmälleen avaimet: {keys}.
"""
        try:
            res = self.client.chat.completions.create(
                model=self.config.judge_model,
                messages=[{"role": "system", "content": check_prompt}],
                response_format={"type": "json_object"},
                temperature=0.0,
            )
            data = json.loads(res.choices[0].message.content)
            cleaned = {k: data.get(k, "tuntematon") for k in self.area_names}
            self.knowledge_map = KnowledgeMap(**cleaned)
        except (OpenAIError, json.JSONDecodeError, ValueError) as e:
            logger.warning("Knowledge map -päivitys epäonnistui: %s", e)

    def final_summary(self) -> str:
        cfg = self.config.topic_cfg
        prompt = f"""
Käyttäjä on opettanut sinulle (Tirolle) aihetta "{cfg['topic_text']}".
Tee lyhyt (max 5 lausetta) yhteenveto siitä, mitä OPIT KÄYTTÄJÄLTÄ.
Käytä omaa ääntäsi (Tiro, mekaanikko-oppilas). Älä lisää mitään, mitä käyttäjä ei sanonut.
Lopuksi kiitä opettajaa.
"""
        return self._one_shot(prompt, temperature=0.5)

    def skill_test(self) -> str:
        cfg = self.config.topic_cfg
        prompt = f"""
Nyt on sinun (Tiron) vuoro kokeilla taitojasi työpajalla!
Kuvaile omin sanoin, vaihe vaiheelta, miten aihe "{cfg['topic_text']}" tehdään.

OHJEET:
- Käytä VAIN sitä tietoa, jota käyttäjä on tähän mennessä opettanut.
- Jos jokin osa-alue on jäänyt epäselväksi, sano rehellisesti "tätä en vielä osaa" tai "tästä en ole varma".
- Käytä numeroitua listaa vaiheille.
- Mainitse turvallisuusnäkökulmat, jos olet oppinut niistä.
- Lopuksi pyydä opettajaa arvioimaan, menikö oikein.
- Vastaa samalla kielellä kuin käyttäjä on käyttänyt.
"""
        return self._one_shot(prompt, temperature=0.4)

    def _one_shot(self, prompt: str, temperature: float = 0.5) -> str:
        msgs = self.history + [{"role": "user", "content": prompt}]
        try:
            res = self.client.chat.completions.create(
                model=self.config.main_model,
                messages=msgs,
                temperature=temperature,
            )
            return res.choices[0].message.content
        except OpenAIError as e:
            logger.exception("One-shot -kutsu epäonnistui")
            return f"[Virhe: {e}]"
