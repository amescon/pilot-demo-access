#!/usr/bin/python

import time   # needed for sleep()
import serial # needed for serialPort
import datetime

def print_usage():
  print('rpcp access control example')

def validate_pin(pin):
  return pin == "1234"

def open_door():
  print('start opening door')
  with open("/sys/class/gpio/gpio55/value", mode='w') as f:
    f.write("1")
  time.sleep(5);
  with open("/sys/class/gpio/gpio55/value", mode='w') as f:
    f.write("0")
  print('end opening door')
  return

def show_image(img):
  with open(img, "rb") as input:
    with open("/proc/rpc+/module2/bitmap", "wb", 16000) as output:
      output.write(input.read())
  return

def show_access_granted():
  show_image("./bmp_access_granted_128x128_inverted.bmp")
  return

def show_access_denied():
  show_image("./bmp_access_denied_128x128_inverted.bmp")
  return

def show_access_control():
  show_image("./bmp_access_control_128x128_inverted.bmp")
  return

def print_access_granted(ser, number):
  ser.write("access granted for:\n")
  ser.write(number + "\n")
  ser.write("at: " + datetime.datetime.now().strftime("%H:%M:%S %Y-%m-%d") + "\n")
  ser.write("\n\n");
  return

def print_access_denied(ser, number):
  ser.write("access denied for:\n")
  ser.write(number + "\n")
  ser.write("at: " + datetime.datetime.now().strftime("%H:%M:%S %Y-%m-%d") + "\n")
  ser.write("\n\n")
  return

def gsm_send(ser, cmd, echo = None):
  if echo == None:
    echo = False

  answer = []
  for c in cmd:
    ser.write(c)
    if echo:
      answer.append(ser.read())

  c = ser.read()
  while c != "":
    answer.append(c)
    c = ser.read()

  return ''.join(answer)

def gsm_receive(ser):
  answer = []
  c = ser.read()
  while c != "":
    answer.append(c)
    c = ser.read()
  return answer

def receive_sms(ser):
  return gsm_send(ser, "AT+CMGL=\"REC UNREAD\"\n")
  #return gsm_send(ser, "AT+CMGL=\"REC UNREAD\",1\n")
  #return gsm_send(ser, "AT+CMGL=\"ALL,1\"\n")

def get_pin(sms):
  index = sms.find("PIN: ")
  length = len(sms)
  pin=""

  if index != -1 and length > index + 9:
    pin=sms[index + 5: index + 5 + 4]
    print("pin: " + pin)
  return pin

def get_number(sms):
  start_index = sms.find("\"+")
  number = ""

  if start_index != -1:
    end_index = sms.find("\"", start_index+1)
    if end_index != -1:
      number = sms[start_index+1 : end_index-1]

  return number

def init():

  def init_output():
    # export the gpio 55 and configure it as an output
    try:
      with open("/sys/class/gpio/export", mode='w') as f:
        f.write("55")
    except: pass
    try:
      with open("/sys/class/gpio/gpio55/direction", mode='w') as f:
        f.write("out")
    except: pass
    return

  def init_lcd():
    # set the resolution of the lcd
    with open("/proc/rpc+/module2/resolution", mode='w') as f:
      f.write("128x128");
    show_access_control()
    return

  def init_printer():
    # initialize the serialport
    ser = serial.Serial(port='/dev/ttyRPC+0', baudrate=9600)
    ser.write("printer initialized.\n\n\n")
    return ser

  def init_gsm():

    # initialize the serialport
    ser = serial.Serial(port='/dev/ttyRPC+4', baudrate=9600, timeout = 1)

    gsm_receive(ser)

    answer = gsm_send(ser, "ATE0\n", echo = True);
    print(answer)

    answer = gsm_send(ser, "AT+CMEE=2\n")
    print(answer)

    answer = gsm_send(ser, "AT+CPIN=4103\n")
    print(answer)

    answer = gsm_send(ser, "AT+CMGF=1\n")
    print(answer)

    return ser

  print('initializing devices')
  serial_gsm = init_gsm()
  init_output()
  serial_printer = init_printer()
  init_lcd()
  return serial_gsm, serial_printer

def receive_sms_loop(serial_gsm, serial_printer):

  print('waiting to receive an sms')
  while 1:
    sms = receive_sms(serial_gsm)

    if sms == '\r\nOK\r\n':
      ''
    else:
      print('sms received is: ' + sms)
      pin = get_pin(sms)
      print('received pin is: ' + pin)
      number = get_number(sms)
      if validate_pin(pin):
        print("access granted!")
        show_access_granted()
        open_door()
        show_access_control()
        print_access_granted(serial_printer, number)
      elif pin != "":
        print("access denied!")
        show_access_denied()
        print_access_denied(serial_printer, number)
        time.sleep(5)
        show_access_control()

    time.sleep(5)

def main():

  # tell the user what we do
  print_usage()

  # initialize all devices
  serial_gsm, serial_printer = init()

  # start listening for sms messages
  receive_sms_loop(serial_gsm, serial_printer)

main()
