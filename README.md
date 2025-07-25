# Linz Netz -> AppDaemon -> HomeAssistant

**AppDaemon** app that parses energy consumption reports of **Linz Netz** (energy supplier in Upper Austria) and forwards the daily consumption to **HomeAssistant**.

Pre setup needed:
- Linz Strom smart meter
- Collecting 15min data is enabled 
- Daily email report is enabled (you will need access to the target mail account on the AppDaemon server)
- Home assistant up and running and input number created (more to that later)
  
It works as follows:
- Periodically checks emails
- Searches for fitting (unread) emails
- Parses the attached CSV file
- calculates the daily consumption
- sends the calculated value to Home Assistant
- marks the email as read

Known issues:
- The emails only include data of the day before yesterday. Home Assistant therefore shows 2 day old data as today's data

Setup in AppDaemon:
Copy `energyconsumption.py` to `conf/apps` and register the app in `apps.yaml` of the same directory:
```
energyconsumption:
  module: energyconsumption
  class: EnergyConsumption
  password: !secret mail_password
  username: !secret mail_username
```
Add to `conf/secrets.yaml`
```
mail_username: yourUsernameHere
mail_password: yourPasswordHere
```

Setup in Home Assistant
`configuration.yaml`
```
input_number:
  daily_energy:
    name: Daily Energy
    min: 0
    max: 100
    step: 0.0001
    unit_of_measurement: "kWh"
    mode: box
```

`automations.yaml`
```
- alias: Reset Daily Energy at Midnight
  description: Reset the daily_energy input number to 0 at midnight
  trigger:
    - platform: time
      at: "00:00:00"
  action:
    - service: input_number.set_value
      target:
        entity_id: input_number.daily_energy
      data:
        value: 0
  mode: single

```
You can further process the data from here. E.g. setting the input number as state input for a template sensor.
