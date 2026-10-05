"""Integration tests for the query path — real providers, no fakes.

The unit suite pins ranking behaviour with `FakeEmbedding`, whose vectors are
sha256 bytes. That proves the plumbing (ingest → Chroma → retrieve → explain)
but says nothing about whether the shipped catalog is actually *retrievable*:
a method whose `use_case` is badly written would still rank fine under a hash.
These tests use the real embedding model against the real `methods/` directory,
so they fail if a method's text stops matching the problems it should match.

Deselected from the default suite via `-m "not integration"` in pyproject's
addopts. Run them explicitly:

    pytest -m integration

Requires the `local` extra (`pip install -e ".[dev,local]"`). The first run
downloads ~930MB of model weights (multilingual embedding + cross-encoder) into
the HuggingFace cache; after that it is offline. The LLM test needs a reachable backend on top of that and is opted
into separately with METHODOS_INTEGRATION_LLM=1.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from methodos.config import Settings
from methodos.mcp_tools import WEAK_MATCH_SIMILARITY
from methodos.providers import make_llm
from methodos.search import search

pytestmark = pytest.mark.integration


def _openai_models() -> list[str]:
    """Model names to probe, read from the table under test.

    Imported inside the function, not at module scope: `pytest --collect-only
    -m integration` runs in CI with only the `dev` extra, and the provider
    module must stay importable there (it lazy-imports `openai` itself).
    """
    from methodos.providers.embedding_openai import _KNOWN_DIMS

    return sorted(_KNOWN_DIMS)


REPO_ROOT = Path(__file__).parent.parent
REPO_METHODS = REPO_ROOT / "methods"


@pytest.fixture(scope="module")
def real_embedding():
    """The default local model. Skips if the `local` extra isn't installed."""
    pytest.importorskip(
        "sentence_transformers",
        reason="needs the `local` extra: pip install -e '.[dev,local]'",
    )
    from methodos.providers.embedding_local import LocalEmbedding

    return LocalEmbedding(model_name=Settings().embedding_model)


@pytest.fixture(scope="module")
def real_index(tmp_path_factory, real_embedding) -> Path:
    """Ingest the real catalog once — model load plus ingest is slow."""
    from methodos.ingest import ingest

    chroma_path = tmp_path_factory.mktemp("chroma_integration")
    summary = ingest(
        methods_dir=REPO_METHODS,
        chroma_path=chroma_path,
        embedding=real_embedding,
    )
    assert summary.count >= 3, "expected the shipped catalog to ingest"
    assert summary.dimensions == 384, f"the default model is 384d, got {summary.dimensions}"
    return chroma_path


# One probe per method, phrased as a user would state the problem — never by
# naming the method or echoing its vocabulary, which would test the query
# rather than the catalog.
#
# What each probe must achieve changed with the move to multilingual models
# (paraphrase-multilingual-MiniLM-L12-v2 + mMARCO cross-encoder). Measured
# against the 23-method catalog:
#
#                         English probes   German probes
#   old embedding only        23/23            7/23      (all-MiniLM-L6-v2)
#   new embedding only        20/23           19/23
#   new embedding + rerank    23/23           23/23
#
# The multilingual embedding is the weaker *ranker* and a far better
# *retriever*: it puts the right method at position <= 4 for every probe in
# both languages, and the cross-encoder does the ordering. So the embedding is
# now held to "on the shortlist the reranker sees", the pipeline to "first".
# The old per-probe cosine margins (0.10 over the runner-up) do not survive
# that change and were dropped rather than lowered until they passed.
#
# Rejected phrasings below were measured against the old English-only model
# and are kept so they don't get re-added without re-measuring:
#   "internal strengths and weaknesses vs external opportunities and threats"
#       -> SWOT by 0.041 over Porter's. The four-quadrant vocabulary is shared.
#   "the same defect keeps coming back after every fix"
#       -> Five_Whys by 0.110 over Ishikawa. Both are root-cause methods; the
#          probe has to name the symptom-vs-cause framing to separate them.
#   "which external forces beyond our competitors should we monitor"
#       -> PESTEL by 0.057 over Porter's. Naming the actual forces separates them.
#   "we keep spending engineering effort on infrastructure that is now a
#    standard utility" -> Wardley only reached #2. Its problem-shaped phrasings
#    lose to Porter's and PESTEL on shared market vocabulary; the build-buy-
#    outsource question is what separates it.
#   "this decision bounces between teams, nobody has authority to approve it"
#       -> was a second DACI probe, fell to 0.022 over Cynefin once Cynefin's
#          use_case was made problem-shaped ("teams that cannot agree how to
#          tackle a problem"). Dropped rather than reworded: phrasings that did
#          clear the bar all leaned on DACI's own role names. One probe per
#          method is the design; DACI's approver probe already covers it.
PROBES = [
    (
        "should we enter this industry? how defensible is the position "
        "against competitors and new entrants",
        "Porters_Five_Forces",
    ),
    (
        "strategic planning kickoff: assess our own position and the "
        "external landscape in four quadrants",
        "SWOT",
    ),
    (
        "scan the wider environment: legislation, demographics, climate "
        "exposure and macroeconomic conditions",
        "PESTEL_Analysis",
    ),
    (
        "map out how this new venture creates and captures value on one page",
        "Business_Model_Canvas",
    ),
    (
        "should we build this component ourselves, buy it off the shelf, or outsource it",
        "Wardley_Mapping",
    ),
    (
        "we cannot forecast a single number for this decade, which choices "
        "hold up across several plausible futures",
        "Scenario_Planning",
    ),
    (
        "who is the approver for this cross-functional decision",
        "DACI_Matrix",
    ),
    (
        "one group wants a detailed plan up front and another wants to start "
        "experimenting, we disagree on what kind of problem this is",
        "Cynefin_Framework",
    ),
    (
        "express the costs and the benefits in money, discount them, and "
        "compare the net present value of each option",
        "Cost_Benefit_Analysis",
    ),
    (
        "the discussion has split into advocates and critics and the same "
        "person is always the sceptic",
        "Six_Thinking_Hats",
    ),
    (
        "we keep fixing the symptom of this recurring failure instead of what actually causes it",
        "Five_Whys",
    ),
    (
        "many possible causes across people process equipment and materials, we need to map them",
        "Ishikawa_Diagram",
    ),
    (
        "before we commit to this launch, imagine it failed and surface "
        "the risks nobody is voicing",
        "Pre_Mortem",
    ),
    (
        "tickets take six weeks end to end but the actual work is only a few hours",
        "Value_Stream_Mapping",
    ),
    (
        "interview customers about what they were struggling with when they "
        "switched and what they stopped using",
        "Jobs_To_Be_Done",
    ),
    (
        "what is resisting this change, and how do we weaken the restraints "
        "instead of pushing harder",
        "Force_Field_Analysis",
    ),
    # Prioritization is the most crowded corner of the catalog: RICE, MoSCoW,
    # Eisenhower and Value Stream Mapping all speak about too much work and not
    # enough capacity. RICE's distinguishing feature is quantified scoring, and
    # a probe only surfaces that by naming reach/impact/effort — which would be
    # testing the query. The embedding alone ranks it second (EN) or fourth
    # (DE); the reranker is what puts it first.
    (
        "we have more backlog items than capacity and need a defensible ranked order",
        "RICE_Scoring",
    ),
    (
        "fixed release date, we must agree now which requirements get dropped",
        "MoSCoW_Method",
    ),
    (
        "which features are table stakes that earn no credit and which would "
        "actually delight customers",
        "Kano_Model",
    ),
    (
        "my week is eaten by interruptions and the important work never gets started",
        "Eisenhower_Matrix",
    ),
    (
        "end of sprint team retrospective, what should we start and stop doing",
        "Start_Stop_Continue",
    ),
    # Two retrospective formats sit close together by construction; this probe
    # leans on the "one picture" framing to separate them. The embedding alone
    # ranks it fourth in English. Expect it to need re-measuring if more
    # retrospective formats are added.
    (
        "the team has gone quiet in our usual list-based retrospectives, we "
        "need goal drag and upcoming risks in one picture",
        "Sailboat_Retrospective",
    ),
    (
        "debrief the launch we just finished: what did we expect versus what happened",
        "After_Action_Review",
    ),
    (
        "whenever we discuss something as a group the same two or three people talk "
        "and everyone else just nods along, how do I get input from all of them",
        "One_Two_Four_All",
    ),
    (
        "before we announce the reform, who could stop it or carry it, and which "
        "groups do we bring in early versus just keep updated",
        "Stakeholder_Map",
    ),
    (
        "every company-wide initiative we launch fizzles out within a year and staff "
        "drift back to the old ways",
        "Kotter_Eight_Steps",
    ),
    (
        "every time we vote the losing side reopens it at the next meeting, and "
        "waiting for unanimity just drags things out",
        "Consent_Decision_Making",
    ),
    (
        "the foundation wants to know how all the things our project does are supposed "
        "to bring about the effect we are aiming for, and nobody here can explain it",
        "Theory_of_Change",
    ),
    (
        "everyone here is flat out, yet at year end nobody can say what all that work "
        "actually changed, and our plans are just long lists of tasks",
        "OKR",
    ),
    (
        "in our weekly team meeting the boss always decides what we talk about, the "
        "things we really want to discuss never come up, and one point eats the whole hour",
        "Lean_Coffee",
    ),
    (
        "we keep rolling out new ideas to every department at once and never find out "
        "whether they actually helped, how can we try them out on a small scale first",
        "PDCA_Cycle",
    ),
    (
        "how do I get a reliable estimate from a group of specialists in different "
        "organisations when the famous names dominate every meeting",
        "Delphi_Method",
    ),
    (
        "we are hosting an evening for about 150 residents and do not want another night "
        "of speeches, people should discuss a few big questions in depth with each other "
        "and mix with people they do not know",
        "World_Cafe",
    ),
    (
        "management already decided we need a new app, but nobody has asked the users "
        "what problem they actually have",
        "Double_Diamond",
    ),
    (
        "we have to pick one of four suppliers and every meeting ends with people "
        "defending their favourite on instinct, we want to agree what matters most "
        "before comparing the offers",
        "Weighted_Decision_Matrix",
    ),
    (
        "every improvement plan at our school starts from what we're failing at and the "
        "teachers have lost all motivation; I want to build on what we already do well",
        "Appreciative_Inquiry",
    ),
    (
        "every office says its own part of the permit process works fine, yet "
        "applicants keep getting lost between them and giving up; nobody has "
        "ever gone through it the way they do",
        "Customer_Journey_Map",
    ),
    (
        "every measure we take against this problem seems to make it worse a few "
        "months later, and nobody can explain why",
        "Causal_Loop_Diagram",
    ),
    (
        "we have dozens of things that might go wrong on this programme, no idea "
        "which ones deserve money and attention, and nobody knows who handles which",
        "Risk_Matrix",
    ),
    (
        "we have to talk about the disputed reform in front of three hundred parents; "
        "a podium panel only gives monologues and an open microphone ends in chaos, "
        "I want a few people to really argue it out while anyone in the hall can still "
        "join in",
        "Fishbowl",
    ),
    (
        "my staff bring me every problem and I just tell them what to do; I'd like our "
        "one-on-one talks to help them work it out themselves and leave knowing what "
        "they will do next",
        "GROW_Model",
    ),
    (
        "every department says its request is top priority, but nobody can tell us "
        "what we actually lose if one of them waits three more months",
        "Cost_of_Delay_WSJF",
    ),
    (
        "the reorganisation is decided and announced, but my people are mourning what "
        "they've lost, nobody knows where they stand any more, and upper management "
        "only talks about how bright the future will be",
        "Bridges_Transition_Model",
    ),
    (
        "management steers us purely by the budget figures; whether our service is any "
        "good, how our processes run and whether staff are developing is invisible in "
        "every report",
        "Balanced_Scorecard",
    ),
    (
        "a room in our building frees up next year and we want a long list of possible "
        "uses for it; when we throw ideas around out loud we run dry after five and each "
        "one gets picked apart straight away",
        "Brainwriting_635",
    ),
    (
        "lots of tasks before opening day can only begin once others are finished; which "
        "of these hold-ups actually move our opening day, and which have room to slip?",
        "Critical_Path_Method",
    ),
    (
        "our operating costs have gone up by a fifth and the board wants to know why; where "
        "do we even start, how do we split that into pieces we can each check without "
        "missing anything",
        "Issue_Tree",
    ),
    (
        "my team waits for my permission on everything, yet when they do act on their own "
        "I end up reversing it; how do we pin down what they may settle alone",
        "Delegation_Poker",
    ),
    (
        "how do I tell a coworker that something he did yesterday really annoyed the team "
        "without it sounding like I'm attacking him as a person",
        "SBI_Feedback",
    ),
    (
        "three offices share the work of getting new pupils started each year; some letters "
        "go out twice, some accounts never get set up, and when we ask why, each office "
        "thought one of the others was doing it",
        "RACI_Matrix",
    ),
    (
        "our committee has to agree today which three proposals get funded, and the final "
        "list always ends up being whatever the chair and the two most talkative members "
        "wanted; I want everyone to bring their own suggestions and everyone's preferences "
        "to count the same",
        "Nominal_Group_Technique",
    ),
    (
        "our customer service team gets hundreds of complaints a month about all sorts of "
        "things and tries to chase down every one separately; I suspect most of them are "
        "really about just a couple of issues, but nobody has ever counted",
        "Pareto_Analysis",
    ),
    (
        "we have to grow next year and the leadership is split: some want to sell more of "
        "what we already offer to the people we already serve, others want to reach "
        "completely different groups or launch something brand new, and nobody has "
        "compared how risky each path is",
        "Ansoff_Matrix",
    ),
    (
        "one of my pupils has completely shut down and things with his parents keep getting "
        "worse; our school has no supervisor or coach, and when I mention it in the staff "
        "room everyone just throws in their own stories and quick tips. I'd like a few "
        "colleagues to properly help me think it through in under an hour",
        "Collegial_Case_Consultation",
    ),
]

# The same problems as a German-speaking user would put them. Not literal
# translations where Swiss usage differs ("Pendenzen", "Lancierung", Franken):
# the point is to probe the language users will actually type.
PROBES_DE = [
    (
        "Sollen wir in diese Branche einsteigen? Wie gut lässt sich die Position "
        "gegen Konkurrenten und Neueinsteiger verteidigen",
        "Porters_Five_Forces",
    ),
    (
        "Auftakt der Strategieplanung: unsere eigene Position und das externe "
        "Umfeld in vier Quadranten beurteilen",
        "SWOT",
    ),
    (
        "das weitere Umfeld absuchen: Gesetzgebung, Demografie, Klimarisiken und "
        "gesamtwirtschaftliche Lage",
        "PESTEL_Analysis",
    ),
    (
        "auf einer Seite darstellen, wie dieses neue Vorhaben Wert schafft und abschöpft",
        "Business_Model_Canvas",
    ),
    (
        "sollen wir diese Komponente selbst bauen, fertig einkaufen oder auslagern",
        "Wardley_Mapping",
    ),
    (
        "wir können für dieses Jahrzehnt keine einzelne Zahl prognostizieren, welche "
        "Entscheidungen halten über mehrere plausible Zukünfte",
        "Scenario_Planning",
    ),
    ("wer genehmigt diesen bereichsübergreifenden Entscheid", "DACI_Matrix"),
    (
        "eine Gruppe will vorab einen detaillierten Plan, eine andere will "
        "experimentieren, wir sind uns uneinig, was für ein Problem das ist",
        "Cynefin_Framework",
    ),
    (
        "Kosten und Nutzen in Franken ausdrücken, abzinsen und den Kapitalwert "
        "jeder Option vergleichen",
        "Cost_Benefit_Analysis",
    ),
    (
        "die Diskussion hat sich in Befürworter und Kritiker gespalten und immer "
        "dieselbe Person ist die Skeptikerin",
        "Six_Thinking_Hats",
    ),
    (
        "wir beheben bei diesem wiederkehrenden Fehler immer das Symptom statt der "
        "eigentlichen Ursache",
        "Five_Whys",
    ),
    (
        "viele mögliche Ursachen bei Menschen, Prozessen, Geräten und Material, wir "
        "müssen sie abbilden",
        "Ishikawa_Diagram",
    ),
    (
        "bevor wir uns auf diese Lancierung festlegen, stellen wir uns vor, sie sei "
        "gescheitert, und holen die Risiken hervor, die niemand anspricht",
        "Pre_Mortem",
    ),
    (
        "Tickets brauchen von Anfang bis Ende sechs Wochen, aber die eigentliche "
        "Arbeit dauert nur ein paar Stunden",
        "Value_Stream_Mapping",
    ),
    (
        "Kundinnen und Kunden befragen, womit sie kämpften, als sie wechselten, und "
        "was sie nicht mehr nutzen",
        "Jobs_To_Be_Done",
    ),
    (
        "was steht dieser Veränderung entgegen, und wie schwächen wir die "
        "Widerstände, statt stärker zu drücken",
        "Force_Field_Analysis",
    ),
    (
        "wir haben mehr Pendenzen als Kapazität und brauchen eine begründbare Rangfolge",
        "RICE_Scoring",
    ),
    (
        "fixer Releasetermin, wir müssen jetzt festlegen, welche Anforderungen wegfallen",
        "MoSCoW_Method",
    ),
    (
        "welche Funktionen sind selbstverständlich und bringen keine Anerkennung, und "
        "welche würden Kunden begeistern",
        "Kano_Model",
    ),
    (
        "meine Woche wird von Unterbrechungen aufgefressen und die wichtige Arbeit beginnt nie",
        "Eisenhower_Matrix",
    ),
    (
        "Retrospektive am Ende des Sprints, was sollen wir anfangen und was aufhören",
        "Start_Stop_Continue",
    ),
    (
        "das Team ist in unseren üblichen listenbasierten Retrospektiven verstummt, "
        "wir brauchen Bremsklötze, Ziel und kommende Risiken in einem Bild",
        "Sailboat_Retrospective",
    ),
    (
        "Nachbesprechung der eben abgeschlossenen Lancierung: was haben wir "
        "erwartet und was ist passiert",
        "After_Action_Review",
    ),
    (
        "bei unseren Besprechungen reden immer die gleichen zwei, drei Leute und der "
        "Rest hört nur zu, wie bekomme ich von allen Ideen",
        "One_Two_Four_All",
    ),
    (
        "bevor wir die Reform ankündigen: wer könnte sie zu Fall bringen oder mittragen, "
        "und welche Gruppen binden wir früh ein, welche halten wir nur auf dem Laufenden",
        "Stakeholder_Map",
    ),
    (
        "unsere organisationsweiten Initiativen verlaufen nach dem Kickoff jedes Mal "
        "im Sand und alle kehren zu den alten Gewohnheiten zurück",
        "Kotter_Eight_Steps",
    ),
    (
        "Im Vorstand wird jeder Mehrheitsentscheid an der nächsten Sitzung wieder "
        "aufgerollt, und Einstimmigkeit erreichen wir nie",
        "Consent_Decision_Making",
    ),
    (
        "unser Projekt hat Budget und viele Aktivitäten, aber niemand kann erklären, "
        "wie daraus die angestrebte Wirkung entstehen soll, und die Stiftung will das wissen",
        "Theory_of_Change",
    ),
    (
        "Alle sind dauernd ausgelastet, aber Ende Jahr kann niemand sagen, was die ganze "
        "Arbeit eigentlich bewirkt hat, und unsere Planung ist bloss eine lange Pendenzenliste",
        "OKR",
    ),
    (
        "in unserer wöchentlichen Teamsitzung bestimmt immer die Chefin, worüber wir "
        "reden, was uns unter den Nägeln brennt, kommt nie dran, und ein Punkt frisst "
        "die ganze Stunde",
        "Lean_Coffee",
    ),
    (
        "Neue Ideen führen wir immer gleich im ganzen Schulhaus ein und merken nie, ob "
        "sie überhaupt etwas gebracht haben. Wie probieren wir sie zuerst im Kleinen aus?",
        "PDCA_Cycle",
    ),
    (
        "Welche Kompetenzen Lernende in zwanzig Jahren brauchen, lässt sich mit keinen "
        "Zahlen belegen; wir wollen das Urteil von Fachleuten aus mehreren Hochschulen, "
        "ohne dass die bekannteste Professorin allen die Meinung vorgibt",
        "Delphi_Method",
    ),
    (
        "am Elternabend mit gut hundert Leuten wollen wir keine Referate, sondern dass "
        "sich alle in wechselnden kleinen Runden über ein paar grosse Fragen zur Schule "
        "austauschen",
        "World_Cafe",
    ),
    (
        "Die Stadt hat eine neue App für die Anmeldung lanciert, aber kaum jemand nutzt "
        "sie. Bevor wir das nächste Angebot bauen, wollen wir verstehen, was die "
        "Bevölkerung wirklich braucht",
        "Double_Diamond",
    ),
    (
        "wir müssen uns für eine von drei Schulsoftwares entscheiden und jede Sitzung "
        "endet beim Bauchgefühl, wir wollen vorher festlegen, was uns wie wichtig ist, "
        "und dann alle Angebote gleich beurteilen",
        "Weighted_Decision_Matrix",
    ),
    (
        "bei uns im Team wird nur noch über Mängel geredet und alle sind demotiviert; "
        "wir möchten die Entwicklung auf dem aufbauen, was schon gut läuft",
        "Appreciative_Inquiry",
    ),
    (
        "Jedes Amt sagt, sein Teil des Bewilligungsverfahrens funktioniere, trotzdem "
        "verlieren sich Gesuchsteller zwischen den Stellen und geben auf; niemand "
        "hat es je so durchlaufen wie sie",
        "Customer_Journey_Map",
    ),
    (
        "Was immer wir gegen das Problem tun, es kommt ein paar Monate später grösser "
        "zurück, und niemand kann erklären, warum",
        "Causal_Loop_Diagram",
    ),
    (
        "bei diesem Vorhaben könnten Dutzende Dinge schiefgehen, wir wissen nicht, "
        "welche Geld und Aufmerksamkeit verdienen, und niemand weiss, wer sich um was kümmert",
        "Risk_Matrix",
    ),
    (
        "an der Personalversammlung müssen wir die umstrittene Reorganisation vor allen "
        "besprechen; ein Podium endet in Monologen und eine offene Fragerunde im Durcheinander, "
        "ein paar Leute sollen vertieft miteinander diskutieren und wer aus dem Saal etwas "
        "beizutragen hat, soll mitreden können",
        "Fishbowl",
    ),
    (
        "In den Mitarbeitergesprächen gebe ich immer gleich die Lösung vor, und am Ende "
        "weiss niemand, was eigentlich vereinbart wurde; ich möchte, dass meine "
        "Lehrpersonen selbst draufkommen, wie sie weitermachen",
        "GROW_Model",
    ),
    (
        "alle Aufträge sind als dringend markiert; welche werden wirklich teurer, "
        "je länger sie liegen bleiben",
        "Cost_of_Delay_WSJF",
    ),
    (
        "Die Zusammenlegung unserer zwei Schulen ist beschlossen, doch das Kollegium "
        "trauert dem Alten nach und hängt in der Luft, und die Schulleitung redet nur "
        "noch davon, wie toll alles wird",
        "Bridges_Transition_Model",
    ),
    (
        "Unser Amt wird nur über Budget und Fallzahlen gesteuert; ob die Leistung für die "
        "Bevölkerung gut ist, wie rund unsere Abläufe laufen und ob sich das Personal "
        "weiterentwickelt, taucht in keinem Bericht an die Geschäftsleitung auf",
        "Balanced_Scorecard",
    ),
    (
        "wir brauchen möglichst viele Vorschläge, wie mehr Eltern an die Elternabende "
        "kommen; wenn wir in der Runde Ideen zurufen, ist nach ein paar Minuten Schluss "
        "und jeder Vorschlag wird sofort zerredet",
        "Brainwriting_635",
    ),
    (
        "Der Umzug ins neue Schulhaus muss bis zum Schuljahresbeginn klappen; vieles kann "
        "erst losgehen, wenn anderes erledigt ist, und niemand weiss, welche Verzögerung "
        "uns den Termin kostet und wo wir noch Luft haben",
        "Critical_Path_Method",
    ),
    (
        "Die Geschäftsleitung will wissen, warum unsere Betriebskosten dieses Jahr um einen "
        "Fünftel höher sind als budgetiert; jede Abteilung zeigt auf eine andere, und ich weiss "
        "nicht, wie ich die Frage so aufteile, dass wir alles prüfen und nichts doppelt machen",
        "Issue_Tree",
    ),
    (
        "Meine Leute fragen mich bei jeder Kleinigkeit um Erlaubnis, und wenn sie einmal selbst "
        "etwas entscheiden, kippe ich es; wir wollen festhalten, worüber das Team künftig "
        "allein bestimmt",
        "Delegation_Poker",
    ),
    (
        "Wie sage ich einem Kollegen, dass mich etwas, das er gestern getan hat, gestört "
        "hat, ohne dass er es als Angriff auf seine Person versteht?",
        "SBI_Feedback",
    ),
    (
        "In unserem Team weiss bei den wiederkehrenden Aufgaben niemand genau, wer was macht; "
        "manches erledigen zwei Leute doppelt, anderes vergessen alle, weil jeder dachte, "
        "jemand anders sei dran",
        "RACI_Matrix",
    ),
    (
        "In der Schulkonferenz müssen wir heute festlegen, welche drei Vorhaben aus dem "
        "Budget Geld bekommen; am Schluss steht immer das zuoberst, was die Schulleitung und "
        "die Lautesten wollten. Alle sollen eigene Vorschläge einbringen, und die Meinung "
        "jeder Person soll gleich viel zählen",
        "Nominal_Group_Technique",
    ),
    (
        "Bei uns gehen jede Woche unzählige Reklamationen und Anfragen zu allen möglichen "
        "Themen ein, und wir versuchen, jede einzeln zu erledigen. Ich vermute, dass die "
        "meisten eigentlich nur ein paar wenige Themen betreffen, aber gezählt hat das noch "
        "nie jemand",
        "Pareto_Analysis",
    ),
    (
        "Wir sollen wachsen, aber die Geschäftsleitung ist uneins: die einen wollen den "
        "bisherigen Kunden mehr vom Gleichen verkaufen, andere ganz andere Zielgruppen "
        "gewinnen oder etwas völlig Neues anfangen, und niemand hat verglichen, wie riskant "
        "welcher Weg ist",
        "Ansoff_Matrix",
    ),
    (
        "Ich komme mit einem Schüler in meiner Klasse nicht mehr weiter, und mit seinen "
        "Eltern ist es völlig verfahren. Supervision gibt es bei uns im Schulhaus keine, "
        "und im Lehrerzimmer hat jede und jeder sofort einen gut gemeinten Tipp. Wie können "
        "mir ein paar Leute aus dem Team in einer Dreiviertelstunde geordnet weiterhelfen?",
        "Collegial_Case_Consultation",
    ),
]

ALL_PROBES = PROBES + PROBES_DE

# Questions the catalog does not cover. The weak-match floor in mcp_tools must
# sit above all of these and below every probe, in both languages.
OFF_TOPIC = [
    "how do I fix my bicycle chain",
    "what is the capital of France",
    "wie flicke ich meine Velokette",
    "was ist die Hauptstadt von Frankreich",
    "Rezept für Zürcher Geschnetzeltes",
]


@pytest.mark.parametrize(("problem", "expected"), ALL_PROBES)
def test_embedding_puts_the_right_method_on_the_shortlist(
    real_index, real_embedding, problem, expected
):
    """The retrieval half: the reranker can only promote what it is shown."""
    settings = Settings()
    shortlist = settings.top_k * settings.overfetch_factor
    result = search(
        query=problem,
        embedding=real_embedding,
        llm=None,
        chroma_path=real_index,
        top_k=shortlist,
    )

    assert result.explanation is None, "llm=None must skip the explanation call"
    ids = [c.id for c in result.candidates]
    assert expected in ids, (
        f"{expected} not in the {shortlist}-method shortlist for {problem!r}: "
        f"{[(c.id, round(c.similarity, 3)) for c in result.candidates]}"
    )
    assert result.candidates[0].similarity >= WEAK_MATCH_SIMILARITY, (
        f"a probe the catalog covers scored {result.candidates[0].similarity:.3f}, "
        f"below the weak-match floor {WEAK_MATCH_SIMILARITY}"
    )


@pytest.mark.parametrize("problem", OFF_TOPIC)
def test_uncovered_questions_stay_below_the_weak_match_floor(real_index, real_embedding, problem):
    """The other side of the floor: these must trigger `guidance`."""
    top = search(
        query=problem, embedding=real_embedding, llm=None, chroma_path=real_index, top_k=1
    ).candidates[0]
    assert top.similarity < WEAK_MATCH_SIMILARITY, (
        f"{problem!r} reached {top.similarity:.3f} ({top.id}), at or above the floor "
        f"{WEAK_MATCH_SIMILARITY} — guidance would stay silent on an uncovered question"
    )


def test_query_path_produces_descending_similarities(real_index, real_embedding):
    result = search(
        query="we need to enter a new market without burning cash",
        embedding=real_embedding,
        llm=None,
        chroma_path=real_index,
        top_k=3,
    )
    sims = [c.similarity for c in result.candidates]
    assert sims == sorted(sims, reverse=True)
    # Cosine over normalized vectors; anything outside this means the metric
    # or the `1 - distance` conversion in search.py drifted.
    assert all(-1.0 <= s <= 1.0 for s in sims)


def test_query_path_hydrates_candidates_from_the_catalog(real_index, real_embedding):
    """Metadata survives the round-trip through Chroma, not just the ids."""
    result = search(
        query="who is the approver for this cross-functional decision",
        embedding=real_embedding,
        llm=None,
        chroma_path=real_index,
        top_k=1,
    )
    top = result.candidates[0]
    assert top.id == "DACI_Matrix"
    assert top.name == "DACI Decision-Making Framework"
    assert top.category == "decision-making"
    assert 1 <= top.complexity_score <= 5
    assert top.strengths and top.weaknesses
    assert top.duration_min <= top.duration_max
    assert (REPO_ROOT / top.doc_path).is_file(), f"{top.doc_path} should exist on disk"


@pytest.mark.skipif(
    os.environ.get("METHODOS_INTEGRATION_LLM") != "1",
    reason="needs a reachable LLM backend; set METHODOS_INTEGRATION_LLM=1 to run",
)
def test_query_path_with_real_llm_returns_an_explanation(real_index, real_embedding):
    """Exercises the one path fakes can't: a real completion through litellm.

    Assertions stay loose on purpose — the wording is non-deterministic. What
    matters is that the prompt renders, the call succeeds, and the model wrote
    about the methods it was actually given.
    """
    settings = Settings()
    result = search(
        query="should we enter this industry? how defensible is the position",
        embedding=real_embedding,
        llm=make_llm(settings),
        chroma_path=real_index,
        top_k=2,
    )

    assert result.explanation is not None
    assert result.explanation.strip(), "explanation must not be blank"
    names = [c.name for c in result.candidates]
    assert any(name.split()[0] in result.explanation for name in names), (
        f"explanation mentions none of {names}: {result.explanation[:200]!r}"
    )


def test_every_method_in_the_catalog_has_a_probe():
    """A new method must arrive with a probe, or it goes untested.

    Needs no model, so it fails fast even without the `local` extra: a method
    added without a probe could otherwise sit in the catalog unretrievable and
    nothing here would notice.
    """
    catalog = {p.stem for p in REPO_METHODS.glob("*.json")}
    probed = {expected for _, expected in PROBES}
    probed_de = {expected for _, expected in PROBES_DE}
    assert probed_de == probed, f"German probes out of step: {sorted(probed ^ probed_de)}"
    assert catalog == probed, (
        f"methods with no probe: {sorted(catalog - probed)}; "
        f"probes naming an unknown method: {sorted(probed - catalog)}"
    )


# --- cross-encoder rerank --------------------------------------------------


@pytest.fixture(scope="module")
def real_reranker():
    """The default cross-encoder. Skips if the `local` extra isn't installed."""
    pytest.importorskip(
        "sentence_transformers",
        reason="needs the `local` extra: pip install -e '.[dev,local]'",
    )
    from methodos.providers.rerank_cross_encoder import CrossEncoderRerank

    return CrossEncoderRerank(model_name=Settings().rerank_model)


@pytest.mark.parametrize(("problem", "expected"), ALL_PROBES)
def test_rerank_puts_every_pinned_probe_first(
    real_index, real_embedding, real_reranker, problem, expected
):
    """The pipeline as shipped — default top_k and overfetch — ranks it first."""
    from methodos.search import retrieve

    settings = Settings()
    out = retrieve(
        query=problem,
        embedding=real_embedding,
        chroma_path=real_index,
        top_k=settings.top_k,
        reranker=real_reranker,
        overfetch_factor=settings.overfetch_factor,
    )
    assert out[0].id == expected, (
        f"expected {expected} first for {problem!r}, got "
        f"{[(c.id, round(c.similarity, 3), round(c.rerank_score or 0, 2)) for c in out]}"
    )
    assert all(c.rerank_score is not None for c in out)
    scores = [c.rerank_score for c in out]
    assert scores == sorted(scores, reverse=True)


# Probes that embedding-only retrieval cannot separate — each was rejected
# during PR #12/#13 for landing under the 0.10 bar or missing outright, which
# forced the pinned probe to be reworded. Measured against the 23-method
# catalog with overfetch_factor=4, under the English-only models:
#
#   SWOT probe    : embedding 0.004 behind Porter's (miss) -> rerank +15.3 ahead
#   Wardley probe : embedding 0.009 behind (miss)          -> rerank  +9.3 ahead
#
# Both still hold with the multilingual pair; the SWOT probe is now ranked
# third by the embedding (0.526, behind PESTEL 0.609 and Porter's 0.562).
#
# These assert only the reranked outcome. Asserting the embedding-only failure
# too would turn a future embedding improvement into a spurious test failure.
@pytest.mark.parametrize(
    ("problem", "expected_top"),
    [
        (
            "internal strengths and weaknesses vs external opportunities and threats",
            "SWOT",
        ),
        (
            "we keep spending engineering effort on infrastructure that is now a standard utility",
            "Wardley_Mapping",
        ),
    ],
)
def test_rerank_rescues_probes_the_embedding_cannot_separate(
    real_index, real_embedding, real_reranker, problem, expected_top
):
    from methodos.search import retrieve

    out = retrieve(
        query=problem,
        embedding=real_embedding,
        chroma_path=real_index,
        top_k=3,
        reranker=real_reranker,
        overfetch_factor=4,
    )
    assert out[0].id == expected_top, (
        f"expected {expected_top} first for {problem!r}, got "
        f"{[(c.id, round(c.rerank_score or 0, 2)) for c in out]}"
    )


def test_rerank_leaves_the_retrieval_similarity_intact(real_index, real_embedding, real_reranker):
    """Both scores survive to the renderer; neither overwrites the other."""
    from methodos.search import retrieve

    out = retrieve(
        query="who is the approver for this cross-functional decision",
        embedding=real_embedding,
        chroma_path=real_index,
        top_k=3,
        reranker=real_reranker,
        overfetch_factor=4,
    )
    for c in out:
        assert -1.0 <= c.similarity <= 1.0, "cosine similarity must stay in range"
        assert c.rerank_score is not None


def test_switching_provider_without_reingest_is_a_stale_index(real_index, real_embedding):
    """local → openai without a rebuild must be caught before any API call.

    OpenAIEmbedding reads its dimensionality from a static table, so it can be
    constructed and compared without credentials — which is exactly why this
    guard is reachable offline and worth pinning here: the failure it prevents
    is querying 384d vectors with a 1536d model and getting silent nonsense
    back rather than an error.
    """
    from methodos.providers.embedding_openai import OpenAIEmbedding
    from methodos.search import StaleIndexError, retrieve

    with pytest.raises(StaleIndexError) as excinfo:
        retrieve(
            query="anything",
            embedding=OpenAIEmbedding(model_name="text-embedding-3-small"),
            chroma_path=real_index,
            top_k=2,
        )
    message = str(excinfo.value)
    assert real_embedding.name in message, "must name the provider the index was built with"
    assert "openai:text-embedding-3-small" in message, "must name the provider now configured"
    assert "ingest" in message, "must say how to fix it"


@pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="needs a real OPENAI_API_KEY; OpenAIEmbedding is otherwise only seen by mocks",
)
@pytest.mark.parametrize("model_name", _openai_models())
def test_openai_embedding_dimensions_match_the_api(model_name):
    """_KNOWN_DIMS is hand-maintained, so verify it against what the API returns.

    A wrong entry here does not raise: ingest would write vectors of one width
    while `dimensions` reports another, and the mismatch only shows up later as
    bad retrieval. The unit suite mocks the client, so this is the only place
    the table is checked against reality.
    """
    from methodos.providers.embedding_openai import _KNOWN_DIMS, OpenAIEmbedding

    provider = OpenAIEmbedding(model_name=model_name)
    vectors = provider.embed(["a short probe sentence for dimensionality"])

    assert len(vectors) == 1
    assert len(vectors[0]) == _KNOWN_DIMS[model_name], (
        f"_KNOWN_DIMS says {model_name} is {_KNOWN_DIMS[model_name]}d, "
        f"API returned {len(vectors[0])}d"
    )
    assert provider.dimensions == len(vectors[0]), (
        "declared dimensions must match what embed returns"
    )


def _first_mention(text: str, method_name: str) -> int | None:
    """Index where `method_name` is first referred to, or None.

    Matches on the leading word only ("SWOT", "Porter", "PESTEL"): models write
    "Porter's Five Forces", "the Five Forces model" or just "Porter's", and an
    exact-name search would miss all but the first. Trailing possessives and
    punctuation are stripped so "Porter's" and "Porter" both hit.
    """
    token = method_name.split()[0].removesuffix("'s").strip(".,:;'\"").lower()
    idx = text.lower().find(token.lower())
    return None if idx < 0 else idx


@pytest.mark.skipif(
    os.environ.get("METHODOS_INTEGRATION_LLM") != "1",
    reason="needs a reachable LLM backend; set METHODOS_INTEGRATION_LLM=1 to run",
)
def test_real_llm_leads_with_the_reranked_top_not_the_most_similar(
    real_index, real_embedding, real_reranker
):
    """The behavioural half of the `{ranking_basis}` change.

    `render_explain_prompt` tells the model the list is ordered by cross-encoder
    relevance and that the printed similarity is *not* the sort key. That text
    exists to stop a model from "correcting" the order back to similarity. The
    unit suite pins that the sentence renders; only a real completion can show
    whether a model acts on it.

    The proxy is which method the explanation introduces first. It is a weak
    signal by construction — but a stable one, because models walk a numbered
    list in the order they are given it, and it fails in exactly the case worth
    catching: an explanation that opens with the highest-*similarity* candidate
    after the reranker deliberately demoted it.

    Non-deterministic wording, so nothing is asserted about content.

    NOTE: this has never passed. It was written where no backend was reachable,
    so it has only ever failed at the litellm call with retrieval and the
    precondition below both holding. First green run is real news — see #22.
    """
    # Same query as scripts/verify_explain.py, and for the same reason: at
    # top_k=3 the reranker puts SWOT (sim 0.526) above both PESTEL (0.609)
    # and Porter's (0.562), so the prompt genuinely shows a top entry that is
    # less similar than the ones under it.
    query = "internal strengths and weaknesses vs external opportunities and threats"
    settings = Settings()
    result = search(
        query=query,
        embedding=real_embedding,
        llm=make_llm(settings),
        chroma_path=real_index,
        top_k=3,
        reranker=real_reranker,
    )

    top, rest = result.candidates[0], result.candidates[1:]
    assert rest, "need at least two candidates for an ordering to exist"
    # Precondition, not the thing under test: without a similarity/rerank
    # conflict the model is never asked to trust the reranked order, and the
    # assertion below would pass for the wrong reason. `test_rerank_rescues_*`
    # pins that such conflicts exist at all; this one needs one specifically.
    assert any(c.similarity > top.similarity for c in rest), (
        f"query {query!r} no longer produces a rerank/similarity conflict — "
        f"{[(c.id, round(c.similarity, 3), round(c.rerank_score or 0, 2)) for c in result.candidates]}. "
        "Pick a query where the reranker promotes a lower-similarity method."
    )

    explanation = result.explanation
    assert explanation is not None and explanation.strip()

    top_at = _first_mention(explanation, top.name)
    assert top_at is not None, (
        f"explanation never mentions the top-ranked {top.name}: {explanation[:300]!r}"
    )
    for other in rest:
        other_at = _first_mention(explanation, other.name)
        if other_at is None:
            continue
        assert top_at < other_at, (
            f"explanation leads with {other.name} (sim {other.similarity:.2f}) "
            f"instead of the reranked top {top.name} (sim {top.similarity:.2f}, "
            f"rerank {top.rerank_score:+.2f}) — the model appears to be sorting "
            f"by similarity: {explanation[:300]!r}"
        )
