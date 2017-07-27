# notdoord

A hacky daemon to interface with the door Arduino, allowing access to members based on member card data stored in a simple file format.

This is in lieu of using the full daemon, `doord`, which lives in the [lhs-marvin](https://github.com/leedshackspace/lhs-marvin) repo and reads member data from a MySQL database.

## Configuration

Member card data is loaded from the file `cards.dat` stored in the root directory of the repository. An example file, `cards.dat.example` is provided to demonstrate the file format.

## Assumptions

The door Arduino is visible as a serial device as `/dev/ttyUSBX`, where X is a number.

## Usage

`$ ./notdoord.py <serialDevice>`

e.g.

`$ ./notdoord.py /dev/ttyUSB?`

This will run the daemon in the foreground.

If running as the `hackspace` user, the `runme.sh` script can be used to run the daemon on a loop in case it crashes.