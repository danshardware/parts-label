"""Label image generation for Brother PT-P700."""

import io
import qrcode
from PIL import Image, ImageDraw, ImageFont
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# 12mm tape = 76 pixels at 180 DPI (Brother PT-P700)
# Width: 76 pixels (max for 12mm tape), Height: proportional for content
TAPE_WIDTH_PX = 76  # 12mm at 180 DPI (PT-P700 max)
LABEL_HEIGHT_PX = 150  # ~20mm at 180 DPI

# Color constants (for 1-bit mode: 0 = black, 1 = white)
BLACK = 0
WHITE = 1


class LabelGenerator:
    """Generate label images for printing."""

    def __init__(self, dpi: int = 180):
        """
        Initialize label generator.

        Args:
            dpi: Dots per inch for printer (Brother PT-P700: 180)
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
        # Create blank label image in landscape (PT-P700 format)
        # PT-P700 expects: width = along tape, height = tape width (76px)
        img = Image.new("1", (LABEL_HEIGHT_PX, TAPE_WIDTH_PX), 1)  # 1 = white, landscape
        draw = ImageDraw.Draw(img)

        # Calculate text area width based on whether we have a QR code
        if datasheet_url:
            # With QR code: text on left, QR code on right
            qr_size = 60  # QR code size in pixels (max for 76px tape)
            qr_x = LABEL_HEIGHT_PX - qr_size - 5
            text_area_width = qr_x - 10  # Leave 5px margin on left, 5px gap before QR
            max_title_font_size = 20
        else:
            # Without QR code: use full width for text
            text_area_width = LABEL_HEIGHT_PX - 10  # 5px margins on each side
            max_title_font_size = 30  # Larger font when more space available

        # Try to load fonts, fallback to default if not available
        try:
            # Start with max font size and reduce if text doesn't fit
            title_font_size = max_title_font_size
            text_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)

            # Find largest font size that fits
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", title_font_size)
            test_draw = ImageDraw.Draw(img)

            # Check if part_name fits in one line
            try:
                bbox = test_draw.textbbox((0, 0), part_name, font=title_font)
                text_width = bbox[2] - bbox[0]
            except AttributeError:
                text_width = test_draw.textsize(part_name, font=title_font)[0]

            # Reduce font size if text is too wide
            while text_width > text_area_width and title_font_size > 10:
                title_font_size -= 1
                title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", title_font_size)
                try:
                    bbox = test_draw.textbbox((0, 0), part_name, font=title_font)
                    text_width = bbox[2] - bbox[0]
                except AttributeError:
                    text_width = test_draw.textsize(part_name, font=title_font)[0]

        except (OSError, IOError):
            # Fallback to default font
            logger.warning("Could not load fonts, using default")
            title_font = ImageFont.load_default()
            text_font = ImageFont.load_default()

        # Draw part name (larger, bold, auto-sized)
        self._draw_text(
            draw,
            part_name,
            font=title_font,
            x=5,
            y=8,
            max_width=text_area_width,
            color=BLACK,
        )

        # Draw info line (smaller)
        self._draw_text(
            draw,
            info_line,
            font=text_font,
            x=5,
            y=45,
            max_width=text_area_width,
            color=BLACK,
        )

        # Generate and paste QR code if URL provided
        if datasheet_url:
            try:
                qr_img = self._generate_qr_code(datasheet_url, qr_size)
                # Position QR code on the right side
                qr_y = (TAPE_WIDTH_PX - qr_size) // 2  # Center vertically
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
            PIL Image of QR code (1-bit black and white)
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

        # Convert to 1-bit mode to match label image
        qr_img = qr_img.convert("1")

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
