# coords.py  – drop this in src/
from dataclasses import dataclass

@dataclass
class CoordSystem:
    """
    Immutable helper that knows how to convert between:

      • RAW   – real-world mm on your microscope slide
      • DISP  – pixels shown in PlateGrid
      • CNC   – mm in the printer's G-code coordinate frame
    """
    mag_factor: float = 4.0           # px / mm in your current UI

    def raw_to_disp(self, x_mm: float, y_mm: float) -> tuple[float, float]:
        """(mm,mm) → (px,px) for drawing.  Y axis is inverted for Matplotlib."""
        return (y_mm*self.mag_factor,        # X display = Yraw
                x_mm*self.mag_factor)        # Y display (before inversion)

    def disp_to_raw(self, x_px: float, y_px: float) -> tuple[float, float]:
        return (y_px/self.mag_factor,
                x_px/self.mag_factor)

    def raw_to_cnc(self, x_mm: float, y_mm: float) -> tuple[float, float]:
        """Swap X/Y only – printer’s origin and axes match RAW size."""
        return (y_mm, x_mm)

    def cnc_to_raw(self, x_mm: float, y_mm: float) -> tuple[float, float]:
        return (y_mm, x_mm)
