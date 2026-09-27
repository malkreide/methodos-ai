# Zugang und Monetarisierung

Stand: September 2026 · Owner: Hayal Özkan

Methodos AI ist ein privates, öffentliches Projekt: Code und Katalog liegen
offen auf GitHub, und das Projekt soll später Geld einbringen. Dieses Dokument
legt fest, wer wie Zugang erhält, womit sich Geld verdienen lässt und was vorher
entschieden oder gebaut sein muss.

## 1. Die Ausgangslage, nüchtern betrachtet

**Die Beschreibungen von SWOT & Co. sind nicht das Produkt.** Sie sind
Allgemeinwissen und lassen sich von jedem Sprachmodell in Sekunden erzeugen.
Wer sie hinter eine Bezahlschranke stellt, verkauft etwas, das es gratis gibt.

Verkaufen lassen sich vier Dinge, die sich schwer kopieren lassen:

1. **Kuratierung.** Geprüfte Inhalte mit Quellen und Review-Datum sowie mit
   Einsatzsituationen aus Verwaltung und Bildung. Generische Kataloge haben das
   nicht.
2. **Treffsicherheit.** Die richtige Methode auf eine unscharf formulierte
   Frage, auf Deutsch wie auf Englisch. Das ist gemessen und nicht behauptet
   (46 Probes).
3. **Integration.** Der Katalog als MCP-Server im KI-Assistenten der
   Organisation, als API und als Konsole.
4. **Eigene Kataloge.** Die internen Methoden, Vorlagen und Begriffe einer
   Organisation, zusammen mit dem öffentlichen Katalog durchsuchbar.

Daraus folgt das Modell: **Open Core.** Der Katalog und die Software bleiben
offen. Bezahlt wird für Betrieb, Premium-Material und organisationseigene
Kataloge.

## 2. Zugangsstufen

| Stufe | Für wen | Zugang | Preis |
|---|---|---|---|
| **Open** | Entwickler, Selbst-Hoster | GitHub, `pip`, Docker, lokaler MCP-Server | gratis |
| **Public** | alle | öffentliche Web-Konsole und gehosteter MCP-Endpunkt, **nur Suche, ohne LLM-Erklärung**, mit Rate Limit | gratis |
| **Pro** | Beraterinnen, Moderatoren, Führungskräfte | API-Key, LLM-Erklärung, Premium-Kits (Vorlagen, Moderationsfolien), höhere Limits | Abo |
| **Team** | Schulen, Verwaltungen, Unternehmen | eigener Katalog über dem öffentlichen, Hosting in der Schweiz oder EU, SSO, Auswertungen, SLA | Jahreslizenz |
| **Services** | Organisationen | Einführung, Workshops, Kuratierung eigener Methoden | Aufwand |

Warum *Public* ohne LLM läuft: Jede Erklärung kostet einen Modellaufruf. Eine
offene, anonyme Konsole mit LLM ist eine offene Kreditkarte. Die reine Suche
kostet nur Hosting und zeigt trotzdem den Kernnutzen. Die Erklärung ist der
natürliche Grund für ein Upgrade.

## 3. Entscheide, die vor dem ersten Franken fallen müssen

### 3.1 Lizenz des Katalogs (dringend)

Heute steht **alles unter MIT**, auch `methods/`. Das erlaubt jedem, den
ganzen Katalog zu nehmen und als eigenes Produkt zu verkaufen. Für bereits
veröffentlichte Versionen lässt sich das **nicht rückgängig machen**. Jeder
weitere Commit unter MIT vergrössert das, was frei weiterverkauft werden darf.

| Option | Wirkung | Einschätzung |
|---|---|---|
| Alles MIT lassen | maximale Verbreitung, keinerlei Schutz des Inhalts | nur sinnvoll, wenn allein Betrieb und Services verkauft werden |
| **Code MIT, Katalog CC BY-SA 4.0** | kommerzielle Nutzung erlaubt, aber mit Namensnennung und Weitergabe unter gleicher Lizenz; proprietäre Übernahme ist ausgeschlossen | **Empfehlung.** Passt zu Open Core und bleibt für Schulen und Verwaltung problemlos nutzbar |
| Katalog CC BY-NC-SA, kommerzielle Lizenz separat | Inhalt selbst wird verkaufbar (Dual Licensing) | schreckt Beitragende ab; «nicht-kommerziell» ist bei öffentlichen Schulen und Verwaltungen unklar |

Premium-Material (Vorlagen, Kits) steht ohnehin nicht im Repository. Das
Datenmodell erzwingt das: `access: premium` verlangt eine `url` und
verbietet eine Datei.

### 3.2 Beiträge Dritter

Sobald andere Personen Methoden beisteuern, gehört ihr Text ihnen. Wer später
die Lizenz wechseln oder doppelt lizenzieren will, braucht dafür vorher ihre
Zustimmung. Das geht über ein **Contributor License Agreement** oder
mindestens das **Developer Certificate of Origin** (DCO, `Signed-off-by`). Das
muss eingeführt sein, bevor der erste externe Pull Request gemergt wird.

### 3.3 Rollenklarheit

Das Projekt ist privat. Die inhaltlichen Schwerpunkte Bildung und öffentliche
Verwaltung liegen aber nahe an der beruflichen Rolle in der Stadtverwaltung.
Deshalb gilt:

- Nebenbeschäftigung nach städtischem Personalrecht klären und schriftlich
  festhalten.
- Keine internen Unterlagen, Prozesse oder Begriffe aus der Verwaltung
  übernehmen. Die Kontexte `public-sector` und `education` beschreiben
  allgemein bekannte Situationen.
- Kein Verkauf an die eigene Organisation und keine Beteiligung an einer
  Beschaffung, in der Methodos AI Anbieter ist.
- Arbeitszeit und Infrastruktur des Arbeitgebers strikt trennen.

Das schützt das Projekt, nicht nur die Person: Ein späterer Vorwurf der
Vermischung wäre für ein Angebot an Schulen und Verwaltungen geschäftsschädigend.

## 4. Was technisch noch fehlt

Bereits vorhanden: strukturierter Katalog mit Kontexten und Assets,
mehrsprachige Suche, Konsole, HTTP-API, lokaler MCP-Server, Datenschutzhinweise,
Kuratierung per Agent.

| Baustein | Nötig für | Bemerkung |
|---|---|---|
| **API-Keys und Rate Limits** | Public, Pro | Die HTTP-API hat heute **keine Authentifizierung**. Vor jedem öffentlichen Betrieb zwingend. |
| **Gehosteter MCP-Endpunkt** (HTTP-Transport) | Public, Pro | Heute nur `stdio` (lokal). |
| **Katalog-Überlagerung** (mehrere Methodenverzeichnisse) | Team | Öffentlicher Katalog plus privates Verzeichnis pro Organisation, IDs dürfen nicht kollidieren. |
| **Mandantentrennung** für Feedback und Index | Team | An dieser Stelle ist der Wechsel von JSONL zu einer Datenbank gerechtfertigt, vorher nicht. |
| **Auslieferung von Premium-Assets** | Pro | Zeitlich begrenzte, signierte Links aus privatem Speicher. |
| **Zahlungsabwicklung** | Pro | Ein *Merchant of Record* (z. B. Paddle, Lemon Squeezy) übernimmt MWST und Rechnungsstellung. Das ist für ein Einzelprojekt einfacher als eine eigene Stripe-Integration. |
| **Datenschutzerklärung und AGB** | Public und alle weiteren Stufen | Nennt den LLM-Anbieter und die Aufbewahrungsdauer der Anfragen (siehe README, «Privacy»). |

## 5. Reihenfolge (klein anfangen)

**Phase 0: erledigt.** Katalogstruktur, mehrsprachige Suche, Kuratierung,
Datenschutzhinweise.

**Phase 1: Fundament und Nachfrage messen.**
Lizenz entscheiden (3.1), DCO einführen (3.2), Rollen klären (3.3).
API-Keys und Rate Limits bauen. Public-Stufe betreiben (Suche ohne LLM, Hosting
in der Schweiz oder EU).
*Weiter, wenn* über drei Monate regelmässig Anfragen kommen und Besucher
wiederkehren. *Sonst* bleibt es ein offenes Projekt, und die Frage ist
beantwortet, ohne Geld verbrannt zu haben.

**Phase 2: Pro.**
LLM-Erklärung hinter API-Key, erste Premium-Kits für die meistgenutzten
Methoden, Zahlungsabwicklung.
*Weiter, wenn* zahlende Nutzende die Modellkosten plus Hosting decken.

**Phase 3: Team.**
Katalog-Überlagerung, Mandantentrennung, SSO. Erst bauen, wenn eine konkrete
Organisation dafür bezahlen will. Ein Pilot finanziert die Entwicklung, nicht
umgekehrt.

## 6. Offene Fragen an den Owner

1. Katalog-Lizenz: CC BY-SA 4.0 wie empfohlen, oder eine andere Option aus 3.1?
2. Sollen öffentliche Beiträge von Anfang an möglich sein (dann zuerst DCO),
   oder bleibt der Katalog vorerst in Eigenregie?
3. Hosting-Anforderung: Schweiz zwingend (Verkaufsargument gegenüber Schulen
   und Verwaltungen), oder genügt die EU?
