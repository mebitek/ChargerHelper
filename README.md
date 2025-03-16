# venus.Charger Helper v0.1
Service to integrate a charger into cerbos gui

The script has been developed with my current RV setup in mind.

The Python script read you `com.victronenergy.charger` and create a `vebus` to connect to the `grid`

### Configuration

* #### Manual
    see `config.ini` and amend for your needs.
    - `device`: your charger device dbus name
    - `voltage`: your grid voltage - defautl 230v
    - `debug`: set log level to debug

### Installation

* #### SetupHelper
    1. install [SetupHelper](https://github.com/kwindrem/SetupHelper)
    2. enter `Package Mager` in Settings
    3. Enter `Inactive Packages`
    4. on `new` enter the following:
        - `package name` -> `ChargerHelper`
        - `GitHub user` -> `mebitek`
        - `GitHub branch or tag` -> `master`
    5. go to `Active packages` and click on `TasmotaInverter`
        - click on `download` -> `proceed`
        - click on `install` -> `proceed`

### Debugging
You can turn debug off on `config.ini` -> `debug=false`

The log you find in /var/log/ChargerHelper

`tail -f -n 200 /data/log/ChargerHelper/current`

You can check the status of the service with svstat:

`svstat /service/ChargerHelper`

It will show something like this:

`/service/ChargerHelper: up (pid 10078) 325 seconds`

If the number of seconds is always 0 or 1 or any other small number, it means that the service crashes and gets restarted all the time.

When you think that the script crashes, start it directly from the command line:

`python /data/ChargerHelper/ChargerHelper.py`

and see if it throws any error messages.

If the script stops with the message

`dbus.exceptions.NameExistsException: Bus name already exists: com.victronenergy.grid"`

it means that the service is still running or another service is using that bus name.


### Hardware

tested with Victron IP22 charger