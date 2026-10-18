#include <Arduino.h>
#include <SPI.h>
#include <RF24.h>

RF24 radio(4, 5);  // CE, CSN
const int NUM_CH = 126;
const int SWEEPS = 20;
uint8_t hits[NUM_CH];

void setup() {
  Serial.begin(115200);
  if (!radio.begin()) {
    Serial.println("Radio not responding, check wiring/power!");
    while (1);
  }
  radio.setAutoAck(false);
  radio.setDataRate(RF24_1MBPS);
  radio.disableCRC();
  radio.setAddressWidth(3);
  radio.startListening();
  radio.stopListening();
}

void loop() {
  memset(hits, 0, sizeof(hits));
  for (int s = 0; s < SWEEPS; s++) {
    for (int ch = 0; ch < NUM_CH; ch++) {
      radio.setChannel(ch);
      radio.startListening();
      delayMicroseconds(170);
      if (radio.testRPD()) hits[ch]++;
      radio.stopListening();
    }
  }
  Serial.print("D");
  for (int ch = 0; ch < NUM_CH; ch++) {
    Serial.print(',');
    Serial.print(hits[ch] * 100 / SWEEPS);
  }
  Serial.println();
}