"""Brother printer interface."""

import os
import subprocess
import logging
from pathlib import Path
from typing import Optional
from PIL import Image

logger = logging.getLogger(__name__)


class BrotherPrinter:
    """Interface to Brother QL label printer."""

    def __init__(
        self,
        printer_id: Optional[str] = None,
        model: str = "QL-700",
    ):
        """
        Initialize printer connection.

        Args:
            printer_id: Printer identifier (e.g., usb://..., tcp://...)
                       If None, tries to detect automatically
            model: Printer model (default: QL-700, compatible with PT-P700)
        """
        self.printer_id = printer_id or os.environ.get("BROTHER_QL_PRINTER", "")
        self.model = model or os.environ.get("BROTHER_QL_MODEL", "PT-P700")

    def discover(self) -> list:
        """
        Discover connected printers.

        Returns:
            List of printer identifiers
        """
        try:
            result = subprocess.run(
                ["brother_ql", "-b", "pyusb", "discover"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                logger.error(f"Discovery failed: {result.stderr}")
                return []

            # Parse printer IDs and clean up any garbage characters
            printers = []
            for line in result.stdout.split("\n"):
                line = line.strip()
                if line.startswith("usb://"):
                    # Extract only the USB ID part, remove any trailing garbage
                    # Format: usb://0xVVVV:0xPPPP or usb://0xVVVV:0xPPPP_serial
                    # Clean by keeping only ASCII printable chars and stopping at whitespace
                    cleaned = ''.join(c for c in line if c.isprintable() and ord(c) < 128)
                    # Further clean: keep only up to first space or unprintable
                    cleaned = cleaned.split()[0] if cleaned else ""
                    # Remove trailing underscore if present
                    cleaned = cleaned.rstrip('_')
                    if cleaned:
                        printers.append(cleaned)

            logger.info(f"Found {len(printers)} printer(s)")
            return printers

        except FileNotFoundError:
            logger.error("brother_ql command not found. Install with: pip install brother-ql")
            return []
        except subprocess.TimeoutExpired:
            logger.error("Printer discovery timeout")
            return []

    def validate_connection(self) -> bool:
        """
        Validate printer is available.

        Returns:
            True if printer is ready, False otherwise
        """
        if not self.printer_id:
            printers = self.discover()
            if not printers:
                logger.error("No printers found. Please connect Brother printer.")
                return False
            self.printer_id = printers[0]
            logger.info(f"Auto-detected printer: {self.printer_id}")

        return True

    def print_image(
        self,
        image: Image.Image,
        label_size: str = "d24",
        rotate: Optional[str] = None,
    ) -> bool:
        """
        Print image to Brother printer.

        Args:
            image: PIL Image to print
            label_size: Label size (d24 for 24mm die-cut tape)
            rotate: Rotation in degrees (auto, 0, 90, 180, 270)

        Returns:
            True if print succeeded, False otherwise
        """
        if not self.validate_connection():
            return False

        # Save image to temporary file
        temp_file = "/tmp/label_to_print.png"
        image.save(temp_file, "PNG")
        logger.debug(f"Saved label image to {temp_file}")

        # Build brother_ql command
        cmd = [
            "brother_ql",
            "-b", "pyusb",
            "-m", self.model,
            "-p", self.printer_id,
            "print",
            "-l", label_size,  # 24mm tape
        ]

        # Add rotation if specified
        if rotate:
            cmd.extend(["-r", rotate])

        # Add image file
        cmd.append(temp_file)

        try:
            logger.debug(f"Running: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                logger.error(f"Print failed: {result.stderr}")
                return False

            logger.info("Label printed successfully")
            return True

        except FileNotFoundError:
            logger.error("brother_ql command not found")
            return False
        except subprocess.TimeoutExpired:
            logger.error("Print timeout")
            return False
        finally:
            # Clean up temp file
            try:
                Path(temp_file).unlink(missing_ok=True)
            except Exception as e:
                logger.warning(f"Failed to clean up temp file: {e}")

    def get_status(self) -> dict:
        """
        Get printer status.

        Returns:
            Dictionary with printer status info
        """
        try:
            result = subprocess.run(
                ["brother_ql", "-p", self.printer_id, "info"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            return {
                "connected": result.returncode == 0,
                "output": result.stdout,
            }

        except Exception as e:
            logger.error(f"Failed to get status: {e}")
            return {"connected": False, "error": str(e)}
