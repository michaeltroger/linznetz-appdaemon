import imaplib, email, io, csv
import hassapi as hass
from email.header import decode_header, make_header

class EnergyConsumption(hass.Hass):
    def initialize(self):
        self.log("Hello from Energy Consumption App")
        self.check_email({})
        self.run_every(self.check_email, "now", 3600)

    def check_email(self, kwargs):
        self.log("now checking...")
        mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
        mail.login(self.args.get("username"), self.args.get("password"))
        mail.select("INBOX")
        _, data = mail.search(None, '(UNSEEN SUBJECT "Tagesbericht")')
        for num in data[0].split():
            self.log("found email")
            _, msg_data = mail.fetch(num, "(RFC822)")
            msg = email.message_from_bytes(msg_data[0][1])
            self.log(f"Subject: {str(make_header(decode_header(msg['Subject'])))}")
            for part in msg.walk():
                filename = part.get_filename()
                if not filename or not filename.lower().endswith(".csv"):
                    continue
                self.log("found csv")
                self.log(f"Filename: {filename}")
                body = part.get_payload(decode=True)
                reader = csv.DictReader(io.StringIO(body.decode()), delimiter=";")
                total = 0.0
                for row in reader:
                    try:
                        value = row["Energiemenge in kWh"].replace(",", ".")
                        total += float(value)
                    except (IndexError, ValueError):
                        self.log(f"Skipping invalid row: {row}")
                        continue
                self.log(f"Total consumption = {total}")
                self.call_service(
                    "input_number/set_value",
                    entity_id = "input_number.daily_energy",
                    value = total
                )
                self.log("resetting sensor again")
                self.call_service(
                    "input_number/set_value",
                    entity_id = "input_number.daily_energy",
                    value = 0
                )
            mail.store(num, '+FLAGS', '\\Seen')
        mail.logout()
        self.log("completed")
