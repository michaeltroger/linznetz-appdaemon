import imaplib, email, io, csv
import hassapi as hass

class EnergyConsumption(hass.Hass):
    def initialize(self):
        self.log("Hello from Energy Consumption App")
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
            for part in msg.walk():
                ct = part.get_content_maintype()
                if part.get_filename() and part.get_filename().lower().endswith(".csv"):
                    self.log("found csv")
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
            mail.store(num, '+FLAGS', '\\Seen')
        mail.logout()
        self.log("completed")
