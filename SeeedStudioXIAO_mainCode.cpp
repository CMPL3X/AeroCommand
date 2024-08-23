#include <Arduino.h>
#include <SoftwareSerial.h>
#include <PocketSphinx.h>

const int rxPin = D7;
const int txPin = D6;

SoftwareSerial mySerial(rxPin, txPin);

PocketSphinx sphinx;

const char* keywords[] = {"stop!", "drone up", "drone down", "drone left", "drone right", "drone rotate left", "drone rotate right", "face control on", "face control off", "takeoff", "land", "come home", "Face mode", "Button mode", "Voice mode"};

void setup() {
  mySerial.begin(9600);
  sphinx.init();
  sphinx.start();
}

void loop() {
  String command = sphinx.recognize();
  if (command != "") {
    for (int i = 0; i < sizeof(keywords) / sizeof(keywords[0]); i++) {
      if (command.equalsIgnoreCase(keywords[i])) {
        mySerial.println(command);
        break;
      }
    }
  }
}
