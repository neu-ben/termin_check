import json
import os
import smtplib
from email.message import EmailMessage
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "https://traukalender.magdeburg.de/de/Termine-96.html?ort=3430&typ=1166"
FREI = ("td.tko-datepicker-day"
           ":not(.tko-datepicker-day--unavailable)"
           ":not(.tko-datepicker-day--past)")

STATE_FILE = Path("letzter_stand.json")

MAIL_ADRESSE = os.environ["MAIL_ADRESSE"]
MAIL_PASSWORT = os.environ["MAIL_PASSWORT"]
SMTP_SERVER = "smtp.web.de"
SMTP_PORT = 587


def freie_tage():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(URL)
        page.wait_for_selector("td.tko-datepicker-day")
        tage = [td.get_attribute("data-date") for td in page.query_selector_all(FREI)]

        nxt = page.query_selector(".tko-datepicker-go-next a")
        if nxt and nxt.is_visible():
            nxt.click()
            page.wait_for_timeout(1000)
            tage += [td.get_attribute("data-date") for td in page.query_selector_all(FREI)]

        browser.close()
    return sorted(set(tage))


def mail_senden(tage):
    msg = EmailMessage()
    msg["Subject"] = "Termin frei beim Standesamt Magdeburg!"
    msg["From"] = msg["To"] = MAIL_ADRESSE
    msg.set_content("Freie Tage: " + ", ".join(tage) + f"\n\nJetzt buchen: {URL}")
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as s:
        s.starttls()
        s.login(MAIL_ADRESSE, MAIL_PASSWORT)
        s.send_message(msg)


def alter_stand():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return []


if __name__ == "__main__":
    tage = freie_tage()
    neu = [t for t in tage if t not in alter_stand()]
    if neu:
        mail_senden(tage)
        print("Mail gesendet:", tage)
    else:
        print("Nichts Neues. Freie Tage:", tage)
    STATE_FILE.write_text(json.dumps(tage))
