"""Label image generation for Brother PT-P700."""

import io
import qrcode
from PIL import Image, ImageDraw, ImageFont
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# 24mm tape = ~206 pixels at 203 DPI (Brother QL standard)
# Width: 206 pixels, Height: variable based on content
# We'll use 24mm width and 50mm height for labels
TAPE_WIDTH_PX = 206  # 24mm at 203 DPI
LABEL_HEIGHT_PX = 424  # ~50mm at 203 DPI

# Color constants
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)


class LabelGenerator:
    """Generate label images for printing."""

    def __init__(self, dpi: int = 203):
        """
        Initialize label generator.

        Args:
            dpi: Dots per inch for printer (Brother QL standard: 203)
        """
        self.dpi = dpi

    def generate(
        self,
        part_name: str,
        info_line: str,
        datasheet_url: Optional[str] = None,
    ) -> Image.Image:
        """
        Generate a label image.

        Args:
            part_name: Main text (part name) - large
            info_line: Secondary text (category/description) - small
            datasheet_url: Optional URL for QR code

        Returns:
            PIL Image object suitable for printing
        """
        # Create blank label image
        img = Image.new("RGB", (TAPE_WIDTH_PX, LABEL_HEIGHT_PX), WHITE)
        draw = ImageDraw.Draw(img)

        # Try to load fonts, fallback to default if not available
        try:
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
            text_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
        except (OSError, IOError):
            # Fallback to default font
            logger.warning("Could not load fonts, using default")
            title_font = ImageFont.load_default()
            text_font = ImageFont.load_default()

        # Layout: part name on top (left), info line below, QR code on right
        content_width = TAPE_WIDTH_PX - 10  # 5px margins
        qr_size = 80  # QR code size in pixels
        text_area_width = content_width - qr_size - 10  # 10px gap

        # Draw part name (larger, bold)
        self._draw_text(
            draw,
            part_name,
            font=title_font,
            x=5,
            y=10,
            max_width=text_area_width,
            color=BLACK,
        )

        # Draw info line (smaller)
        self._draw_text(
            draw,
            info_line,
            font=text_font,
            x=5,
            y=50,
            max_width=text_area_width,
            color=BLACK,
        )

        # Generate and paste QR code if URL provided
        if datasheet_url:
            try:
                qr_img = self._generate_qr_code(datasheet_url, qr_size)
                # Position QR code on the right side
                qr_x = TAPE_WIDTH_PX - qr_size - 5
                qr_y = 10
                img.paste(qr_img, (qr_x, qr_y))
                logger.debug(f"QR code added at ({qr_x}, {qr_y})")
            except Exception as e:
                logger.warning(f"Failed to generate QR code: {e}")

        return img

    def _draw_text(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        font: ImageFont.FreeTypeFont,
        x: int,
        y: int,
        max_width: int,
        color: tuple,
    ) -> int:
        """
        Draw text with word wrapping.

        Args:
            draw: PIL ImageDraw object
            text: Text to draw
            font: Font to use
            x: X coordinate
            y: Y coordinate
            max_width: Maximum width before wrapping
            color: Text color

        Returns:
            Height used by the text
        """
        if not text:
            return 0

        words = text.split()
        lines = []
        current_line = ""

        for word in words:
            test_line = f"{current_line} {word}".strip()
            # Use getbbox as it's available in newer Pillow versions
            try:
                bbox = draw.textbbox((0, 0), test_line, font=font)
                width = bbox[2] - bbox[0]
            except AttributeError:
                # Fallback for older Pillow versions
                width = draw.textsize(test_line, font=font)[0]

            if width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        # Draw all lines
        current_y = y
        for line in lines:
            draw.text((x, current_y), line, fill=color, font=font)
            try:
                bbox = draw.textbbox((0, 0), line, font=font)
                line_height = bbox[3] - bbox[1]
            except AttributeError:
                line_height = draw.textsize(line, font=font)[1]
            current_y += line_height + 2

        return current_y - y

    def _generate_qr_code(self, data: str, size: int) -> Image.Image:
        """
        Generate QR code image.

        Args:
            data: Data to encode in QR code
            size: Size of QR code in pixels

        Returns:
            PIL Image of QR code
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=2,
            border=1,
        )
        qr.add_data(data)
        qr.make(fit=True)

        qr_img = qr.make_image(fill_color="black", back_color="white")

        # Resize to desired size
        qr_img = qr_img.resize((size, size), Image.Resampling.LANCZOS)

        return qr_img

    def save_to_file(self, img: Image.Image, filepath: str) -> None:
        """
        Save label image to file.

        Args:
            img: PIL Image to save
            filepath: Path to save to
        """
        img.save(filepath, "PNG")
        logger.info(f"Label image saved to {filepath}")

    def to_bytes(self, img: Image.Image) -> bytes:
        """
        Convert image to bytes.

        Args:
            img: PIL Image to convert

        Returns:
            Image bytes in PNG format
        """
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()
