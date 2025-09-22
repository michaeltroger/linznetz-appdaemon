import imaplib, email, io, csv
import hassapi as hass
import requests
from email.header import decode_header, make_header

IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993
SEARCH_QUERY = "Tagesbericht"
CSV_COLUMN_NAME = "Energiemenge in kWh"
INPUT_NUMBER_ENTITY = "input_number.daily_energy"
NTFY_URL = "https://ntfy.sh/mytopic"
MAX_EMAILS = 2

class EnergyConsumption(hass.Hass):
    def initialize(self):
        self.log("Hello from Energy Consumption App")
        # self.check_email({}) # uncomment for running once
        self.run_daily(self.check_email, "13:30:00")

    def check_email(self, kwargs):
        self.log("now checking...")
        try:
            mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
            mail.login(self.args.get("username"), self.args.get("password"))
            mail.select("INBOX")
            _, data = mail.search(None, f'(UNSEEN SUBJECT "{SEARCH_QUERY}")')
            message_ids = data[0].split()
            message_count = len(message_ids)
            self.log(f"Found: {message_count} mails")
            if message_count == 0:
                requests.post(NTFY_URL, data="No emails found")
                mail.logout()
                return
            elif message_count == MAX_EMAILS:
                requests.post(NTFY_URL, data=f"{MAX_EMAILS} emails found")
            elif message_count > MAX_EMAILS:
                requests.post(NTFY_URL, data=f"Error - too many emails: {message_count}")
                mail.logout()
                return

            for message_id in message_ids[:MAX_EMAILS]:
                self.log("found email")
                _, msg_data = mail.fetch(message_id, "(RFC822)")
                msg = email.message_from_bytes(msg_data[0][1])
                self.log(f"Subject: {str(make_header(decode_header(msg['Subject'])))}")
                total = 0.0
                for part in msg.walk():
                    filename = part.get_filename()
                    if not filename or not filename.lower().endswith(".csv"):
                        continue
                    self.log("found csv")
                    self.log(f"Filename: {filename}")
                    body = part.get_payload(decode=True)
                    reader = csv.DictReader(io.StringIO(body.decode()), delimiter=";")
                    for row in reader:
                        value = row[CSV_COLUMN_NAME].replace(",", ".")
                        total += float(value)
                    break
                mail.store(message_id, '+FLAGS', '\\Seen')

                if not (1.0 < total < 100.0):
                    raise Exception(f"Unexpected energy value count: {total}")
                self.log(f"Total consumption = {total}")
                self.call_service(
                    "input_number/set_value",
                    entity_id=INPUT_NUMBER_ENTITY,
                    value=total
                )
                self.log("resetting sensor again")
                self.call_service(
                    "input_number/set_value",
                    entity_id=INPUT_NUMBER_ENTITY,
                    value=0
                )
            mail.logout()
        except Exception as e:
            self.log(f"Email check failed: {e}", level="ERROR")
            requests.post(NTFY_URL, data = "Appdaemon error") # optionally send notification via ntfy.sh
        else:
            self.log("completed")
