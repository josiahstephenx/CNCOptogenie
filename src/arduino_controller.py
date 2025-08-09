"""
Arduino laser-pulser host driver   –   v2.0
Protocol:  R,intensity,sequenceSeconds,frequencyHz,pulseDurationMs
"""

import time, serial
from serial import SerialException

class ArduinoController:
    def __init__(self, port: str, baud_rate: int = 115200):
        self.port, self.baud = port, baud_rate
        self.ser = None
        self.connect()

    # ───────────────────────────────────────────────────────────
    #  Serial connection management
    # ───────────────────────────────────────────────────────────
    def connect(self) -> bool:
        try:
            if self.ser and self.ser.is_open:
                self.ser.close()
            self.ser = serial.Serial(self.port, self.baud, timeout=1)
            time.sleep(2)                             # auto-reset pause
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            return True
        except SerialException as e:
            print(f"[Serial] connect failed: {e}")
            self.ser = None
            return False

    def reconnect(self) -> bool:
        print("[Serial] reconnecting …")
        if self.ser and self.ser.is_open:
            self.ser.close()
        time.sleep(1)
        return self.connect()

    def close(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
            self.ser = None

    # ───────────────────────────────────────────────────────────
    #  Helper: wait for specific response
    # ───────────────────────────────────────────────────────────
    def _await(self, expected_response, timeout=5):
        """Wait for a specific response from Arduino with timeout."""
        if not self.ser or not self.ser.is_open:
            return None

        start_time = time.time()
        while (time.time() - start_time) < timeout:
            try:
                if self.ser.in_waiting > 0:
                    response = self.ser.readline().decode('ascii').strip()
                    print(f"Arduino response: {response}")
                    if expected_response in response:
                        return response
                time.sleep(0.1)
            except SerialException:
                self.reconnect()
                return None
        return None

    # ───────────────────────────────────────────────────────────
    #  Public API
    # ───────────────────────────────────────────────────────────
    def send_recipe_command(self,
                            intensity:        float,
                            sequence_seconds: float,
                            frequency_hz:     float,
                            pulse_duration_ms:float):
        """
        Send one pulse-train recipe.

        intensity         – 0-255
        sequence_seconds  – total length of the train
        frequency_hz      – pulses per second (integer 1-1000)
        pulse_duration_ms – ON-time of each pulse (1-60 000 ms)
        """
        # ---- sanitise & validate ----------------------------------
        intensity_i  = int(round(intensity))
        seq_i        = int(round(sequence_seconds))
        freq_i       = int(round(frequency_hz))
        pulse_i      = int(round(pulse_duration_ms))

        if not (0 <= intensity_i <= 255):
            raise ValueError("Intensity must be 0-255")
        if seq_i <= 0:
            raise ValueError("Sequence duration must be > 0 s")
        if not (1 <= freq_i <= 1000):
            raise ValueError("Frequency must be 1-1000 Hz")
        if not (1 <= pulse_i <= 60000):
            raise ValueError("Pulse duration must be 1-60000 ms")

        period_ms = 1000 / freq_i
        if pulse_i > period_ms:
            raise ValueError(f"Pulse duration ({pulse_i} ms) exceeds "
                             f"period ({int(period_ms)} ms) for {freq_i} Hz")

        # ---- build & send command ---------------------------------
        cmd = f"R,{intensity_i},{seq_i},{freq_i},{pulse_i}"
        print(f"[Host] → {cmd}")
        try:
            self.ser.write((cmd + "\n").encode())
            self.ser.flush()
        except SerialException as e:
            raise RuntimeError("Serial write failed") from e

        # ---- handshake --------------------------------------------
        if not self._await("ACK", timeout=2):
            raise RuntimeError("ACK not received")

        # dynamic timeout: whole sequence + 20 % + 5 s
        if not self._await("DONE", timeout=seq_i * 1.2 + 5):
            raise RuntimeError("DONE not received in time")

        print("[Host] ✓ sequence complete")
        return True

    def test_connection(self):
        """Test the connection to the Arduino."""
        if not self.ser or not self.ser.is_open:
            return False

        try:
            self.ser.write(b'TEST\n')
            response = self._await("OK", timeout=2)
            return response is not None
        except Exception as e:
            print(f"Error testing Arduino connection: {e}")
            return False
        
    def await_response(self, token: str = "DONE", timeout: float = 60):
        """
        Public wrapper around the internal _await().
        Keeps backward-compatibility while giving other modules a
        stable, non-underscored API.
        """
        return self._await(token, timeout)