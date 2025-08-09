// Arduino Code

// Define the pin connected to the laser
const byte  LASER_PIN     = 7;          // hard-wired laser pin
const uint32_t MAX_RUN_MS = 60000UL;    // absolute safety cap (60 s)

/* Parsed recipe parameters */
uint8_t  intensity    = 0;   // 0-255 (ignored on pin 7 but kept for protocol)
uint16_t pulseSeconds = 0;   // total train duration (s)
uint16_t frequencyHz  = 0;   // pulses per second
uint16_t onTimeMs     = 0;   // ms laser ON in each period

/* Forward declarations */
bool parseRecipe(const String& cmd);
void executeRecipe();

void setup() {
  pinMode(LASER_PIN, OUTPUT);
  digitalWrite(LASER_PIN, LOW);
  Serial.begin(115200);
  // Clear any pending data
  while (Serial.available()) {
    Serial.read();
  }
}

void loop() {
  if (!Serial.available()) return;

  String cmd = Serial.readStringUntil('\n');
  cmd.trim();

  if (cmd.equals("TEST")) {
    Serial.println("OK");
    return;
  }

  if (cmd.length() == 0)      return;     // empty line
  if (cmd.charAt(0) != 'R')   return;     // ignore non-recipe lines

  if (!parseRecipe(cmd)) {
    Serial.println("ERR");
    return;
  }

  Serial.println("ACK");
  executeRecipe();
  Serial.println("DONE");
}

/* ---------- Parse "R,intensity,pSec,freq,onMs" ----------------------- */
bool parseRecipe(const String& cmd) {
  int idx = 2;            // skip "R,"
  int next;

  /* intensity (0-255, unused on pin 7 but still accepted)  */
  next = cmd.indexOf(',', idx);                 if (next < 0) return false;
  intensity = cmd.substring(idx, next).toInt();
  if (intensity > 255) intensity = 255;
  idx = next + 1;

  /* pulseSeconds (>0) */
  next = cmd.indexOf(',', idx);                 if (next < 0) return false;
  pulseSeconds = cmd.substring(idx, next).toInt();
  if (pulseSeconds == 0) return false;
  idx = next + 1;

  /* frequencyHz (>0) */
  next = cmd.indexOf(',', idx);                 if (next < 0) return false;
  frequencyHz = cmd.substring(idx, next).toInt();
  if (frequencyHz == 0) return false;
  idx = next + 1;

  /* onTimeMs (>0) */
  onTimeMs = cmd.substring(idx).toInt();
  if (onTimeMs == 0) return false;

  /* Ensure onTime ≤ period */
  uint16_t periodMs = 1000UL / frequencyHz;
  if (onTimeMs > periodMs) onTimeMs = periodMs;

  /* Echo parameters for debugging */
  Serial.print("I=");  Serial.print(intensity);
  Serial.print("  T="); Serial.print(pulseSeconds);
  Serial.print("s  f="); Serial.print(frequencyHz);
  Serial.print("Hz  tOn="); Serial.print(onTimeMs); Serial.println("ms");
  return true;
}

/* ---------- Execute pulse train, clipped to 60 s --------------------- */
void executeRecipe() {
  const uint16_t periodMs  = 1000UL / frequencyHz;
  const uint32_t reqMs     = (uint32_t)pulseSeconds * 1000UL;
  uint32_t remainingMs     = reqMs;
  
  while (remainingMs > 0) {
    // Calculate how long to run in this segment
    const uint32_t segmentMs = (remainingMs <= MAX_RUN_MS) ? remainingMs : MAX_RUN_MS;
    const uint32_t pulses    = segmentMs / periodMs;
    
    // Execute this segment
    for (uint32_t i = 0; i < pulses; ++i) {
      digitalWrite(LASER_PIN, HIGH);          // full-power pulse
      delay(onTimeMs);

      digitalWrite(LASER_PIN, LOW);           // off interval
      uint16_t offMs = periodMs - onTimeMs;
      if (offMs) delay(offMs);
    }
    
    // Update remaining time
    remainingMs -= segmentMs;
    
    // If we have more to do, send a progress update
    if (remainingMs > 0) {
      Serial.print("PROGRESS: ");
      Serial.print((reqMs - remainingMs) * 100 / reqMs);
      Serial.println("%");
    }
  }
} 