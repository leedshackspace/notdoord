# notdoord

A hacky daemon to interface with the door Arduino, allowing access to members based on member card data stored in a simple file format.

This is in lieu of using the full daemon, `doord`, which lives in the [lhs-marvin](https://github.com/leedshackspace/lhs-marvin) repo and reads member data from a MySQL database.

## Configuration

Member card data is loaded from the file `cards.dat` stored in the root directory of the repository. An example file, `cards.dat.example` is provided to demonstrate the file format.

## Assumptions

The door Arduino is visible as a serial device as `/dev/ttyUSBX`, where X is a number.

## Usage

`$ ./notdoord.py --device <serialDevice> --cardsPath <pathToCardsFile>`

e.g.

`$ ./notdoord.py --device /dev/ttyUSB0 --cardsPath cards.dat`

This will run the daemon in the foreground.

## Running as a service

An example systemd service unit file is included in `notdoord.service`. It can be set up follows:

1. Copy `notdoord.service` to /etc/systemd/system/notdoord.service
2. Enable autostart on boot with `sudo systemctl enable notdoord.service`
3. Start the service with `sudo systemctl start notdoord.service`

Service output can be viewed by running `sudo journalctl -fu notdoord.service`
