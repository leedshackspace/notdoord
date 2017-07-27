#! /usr/bin/env python3

# Bodge electronic door locks

import sys
import crc16
import serial
import time
import optparse
import os

def dbg(msg):
    print(msg)

def encode64(val):
    if val < 26:
        return chr(val + ord("A"))
    val -= 26;
    if val < 26:
        return chr(val + ord("a"))
    val -= 26;
    if val < 10:
        return chr(val + ord("0"))
    val -= 10;
    if val == 0:
        return '+';
    if val == 1:
        return '/';
    return '*';

def decode64(c):
    if c >= 'A' and c <= 'Z':
        return ord(c) - ord('A')
    if c >= 'a' and c <= 'z':
        return ord(c) + 26 - ord('a')
    if c >= '0' and c <= '9':
        return ord(c) + 52 - ord('0')
    if c == '+':
        return 62
    if c == '/':
        return 63
    raise Exception("Bad base64 character: '%s'" % c)

def encoded_time():
    t = int(time.time())
    s = ""
    for i in range(6):
        s += encode64(t & 0x3f)
        t >>= 6;
    return s

def decode_time(s):
    t = 0
    for i in range(len(s)):
        t |= decode64(s[i]) << (i * 6)
    return t

def crc_str(s):
    return "%04X" % crc16.crc16xmodem(s)

def OpenSerial(name):
    return serial.Serial(name, 9600, timeout=30)

class SimpleDoor():
    def __init__(self, port_name):
        self.port_name = port_name
        self.ser = None
        self.public_open = False
        self.open_expires = None
        self.keys = []
        self.seen_event = False
        self.seen_kp = None

    def dbg(self, *args):
        dbg(*args)

    def load_keys(self, filename):
        self.keys = []
        with open(filename, "rt") as f:
            header = f.readline().split()
            if header != ["card_id", "pin", "user_id"]:
                raise Exception("Bad card file header")
            for l in f:
                card, pin, _ = l.split()
                self.keys.append("%s %s" % (card.upper(), pin))

    def do_cmd(self, cmd):
        dbg("Sending %s" % cmd)
        self.ser.write(cmd.encode())
        self.ser.write(crc_str(cmd).encode())
        self.ser.write(b"\n")
        r = None
        while r is None:
            r = self.read_response()
        return r

    def read_response(self):
        r = self.ser.readline().decode()
        self.dbg("Response: %s" % r[:-1])
        if len(r) == 0:
            raise Exception("Timeout waiting for response")
        if len(r) < 5:
            return None
        if r[0] == '#':
            return None
        crc = r[-5:-1]
        r = r[:-5]
        if crc != crc_str(r):
            raise Exception("CRC mismatch (exp %s got %s)" % (crc, crc_str(r)))
        if r[0] == 'E':
            self.seen_event = True;
        elif r[0] == 'Y':
            kp_char = r[2]
            if self.seen_kp is None:
                self.seen_kp = ''
            self.seen_kp += kp_char
        else:
            return r
        return None

    def do_cmd_expect(self, cmd, response, error):
        r = self.do_cmd(cmd)
        if r != response:
            self.dbg("Expected %r got %r" % (response, r))
            raise Exception(error)

    def do_kp(self, kp):
        self.dbg("Keypad %s" % kp)
        if self.public_open and kp == '#':
            self.do_cmd("U0")

    def check_open_day(self):
        try:
            with open("/tmp/open-day", "rt") as f:
                hours = int(f.read())
            os.unlink("/tmp/open-day")
            self.public_open = True
            self.open_expires = time.monotonic() + hours * 3600
            self.dbg("Opening Space for %d hours" % hours)
        except FileNotFoundError:
            pass
        if self.public_open:
            if time.monotonic() >= self.open_expires:
                self.public_open = False
                self.dbg("Closing Space")

    def read_event(self):
        while True:
            r = self.do_cmd("G0")
            if r[:2] != 'V0':
                raise Exception("Failed to get log event")
            if r == 'V0':
                return
            print("Log event:" , r[2:])
            self.do_cmd_expect("C0", "A0", "Error clearing event log")

    def run(self):
        self.resync()
        next_tick = time.monotonic()
        while True:
            self.check_open_day()
            while self.ser.inWaiting():
                self.read_response()
            if self.seen_event:
                self.seen_event = False
                self.read_event()
            if self.seen_kp is not None:
                k = self.seen_kp
                self.seen_kp = None
                self.do_kp(k)
            if time.monotonic() < next_tick:
                time.sleep(0.1)
            else:
                self.send_ping()
                next_tick += 5

    def send_ping(self):
        t = encoded_time()
        self.do_cmd_expect("P0" + t, "P1" + t, "Machine does not go ping")

    def key_hash(self):
        crc = 0
        for key in self.keys:
            crc = crc16.crc16xmodem(key, crc)
            crc = crc16.crc16xmodem(chr(0), crc)
        self.dbg("key hash %04X" % crc)
        return "%04X" % crc

    def resync(self):
        self.dbg("Resync")
        if self.ser is None:
            self.ser = OpenSerial(self.port_name)
            self.ser.write(b"X\n")
            time.sleep(1)
            # Wait for a 1s quiet period
            while self.ser.inWaiting():
                while self.ser.inWaiting():
                    self.ser.read(1)
                time.sleep(0.1)

        # Enumerate devices
        self.do_cmd_expect("S0", "S1", "Device not accepting address")
        self.send_ping()
        hash_result = "H0" + self.key_hash()
        r = self.do_cmd("K0")
        if r != hash_result:
            self.dbg("Uploading keys")
            self.do_cmd_expect("R0", "A0", "Device key reset failed")
            for key in self.keys:
                self.do_cmd_expect("N0" + key, "A0", "Device not accepting keys")
            self.do_cmd_expect("K0", hash_result, "Key upload corrupt")


def main():
    d = SimpleDoor(sys.argv[1])
    d.load_keys("cards.dat")
    d.run()

if __name__ == "__main__":
    main()
