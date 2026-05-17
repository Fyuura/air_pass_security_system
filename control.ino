#include <WiFiS3.h>
#include <WiFiUdp.h>
#include <Servo.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include "secrets.h"

// WiFi Variables
char ssid[] = SSID; 
char pass[] = PASS;
unsigned int localPort = 4210;
WiFiUDP Udp;

// Hardware Definitions
#define RED_PIN 3
#define GREEN_PIN 5
#define BLUE_PIN 6
#define SERVO_PIN 9
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);
Servo myServo;

void setup() {
  Serial.begin(115200);
  
  // Pin Modes
  pinMode(RED_PIN, OUTPUT);
  pinMode(GREEN_PIN, OUTPUT);
  pinMode(BLUE_PIN, OUTPUT);
  myServo.attach(SERVO_PIN);
  myServo.write(0); // Starts as locked

  // Starting OLED Display
  if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    for(;;); 
  }

  display.clearDisplay();
  display.display();

  // WiFi Connection
  while (WiFi.begin(ssid, pass) != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Udp.begin(localPort);

  while (WiFi.localIP() == IPAddress(0,0,0,0)) {
    delay(500);
    showStatus("CONNECTING", "Waiting for WiFi connection...");
  }

  showStatus("SYSTEM READY", "Waiting for Raspberry Pi connection...\n\nIP: " + WiFi.localIP().toString());
  setLED(0, 0, 0);
}

void loop() {
  int packetSize = Udp.parsePacket();
  if (packetSize) {
    char cmd = Udp.read();
    
    switch (cmd) {
      case 'E':
        showStatus("ERROR", "Camera is not connected");
        setLED(0, 0, 0);
        break;

      case 'N':
        showStatus("IDLE", "Waiting for a face detection");
        setLED(0, 0, 0);
        break;

      case 'F':
        showStatus("FACE DETECTED", "Enter gesture sequence");
        setLED(0, 0, 255);
        break;

      case 'C':
        showStatus("CORRECT", "Welcome");
        setLED(0, 255, 0);
        myServo.write(90);
        delay(5000);
        myServo.write(0);
        break;

      case 'W':
        showStatus("WRONG", "Try again");
        setLED(255, 0, 0);
        delay(1500);
        break;
      
      case 'Q':
        showStatus("SYSTEM READY", "Waiting for Raspberry Pi connection...\n\nIP: " + WiFi.localIP().toString());
        setLED(0, 0, 0);
        break;
    }
  }
}

// Helper Functions
void setLED(int r, int g, int b) {
  analogWrite(RED_PIN, r);
  analogWrite(GREEN_PIN, g);
  analogWrite(BLUE_PIN, b);
}

void showStatus(String header, String body) {
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(WHITE);
  display.setCursor(0,0);
  display.println(header);
  display.drawLine(0, 10, 128, 10, WHITE);
  display.setCursor(0, 25);
  display.setTextSize(1);
  display.println(body);
  display.display();
}