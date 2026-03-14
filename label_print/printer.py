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
        rotate: Optional[str] = "90",
        chain: bool = False,
    ) -> bool:
        """
        Print image to Brother PT-P700 printer using ptouch-print.

        Args:
            image: PIL Image to print (should be 1-bit B&W)
            label_size: Unused (kept for API compatibility)
            rotate: Unused (kept for API compatibility)
            chain: Skip cutting to print multiple labels continuously

        Returns:
            True if print succeeded, False otherwise
        """
        # Save image to temporary file
        temp_file = "/tmp/label_to_print.png"
        image.save(temp_file, "PNG")
        logger.debug(f"Saved label image to {temp_file}")

        # Build ptouch-print command (much simpler than brother_ql!)
        cmd = ["ptouch-print"]

        if chain:
            cmd.append("--chain")

        cmd.extend(["--image", temp_file])

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
            logger.error("ptouch-print command not found. Install from: https://git.familie-radermacher.ch/linux/ptouch-print.git")
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
