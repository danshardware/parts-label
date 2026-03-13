"""Command-line interface for label-print."""

import click
import logging
import sys
from typing import Optional

from .part_number import validate_part_number, detect_distributor, get_distributor_name
from .part_lookup import PartLookupClient
from .label_generator import LabelGenerator
from .printer import BrotherPrinter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@click.command()
@click.argument("part_number", required=True)
@click.argument("info_line", required=False, default=None)
@click.option(
    "--printer-id",
    default=None,
    envvar="BROTHER_QL_PRINTER",
    help="Brother printer identifier (e.g., usb://..., tcp://...)",
)
@click.option(
    "--model",
    default="QL-700",
    envvar="BROTHER_QL_MODEL",
    help="Printer model (default: QL-700, use for PT-P700)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Generate label but don't print",
)
@click.option(
    "--save-image",
    type=click.Path(),
    default=None,
    help="Save label image to file",
)
@click.option(
    "--mouser-key",
    default=None,
    envvar="MOUSER_API_KEY",
    help="Mouser API key (optional, can also use .env file)",
)
@click.option(
    "--url",
    default=None,
    help="Custom URL for QR code (skips automatic part lookup)",
)
@click.option(
    "-v", "--verbose",
    is_flag=True,
    help="Verbose output",
)
def main(
    part_number: str,
    info_line: Optional[str],
    printer_id: Optional[str],
    model: str,
    dry_run: bool,
    save_image: Optional[str],
    mouser_key: Optional[str],
    url: Optional[str],
    verbose: bool,
):
    """
    Print component labels on Brother PT-P700 label printer.

    Example:
        label-print "296-32654-ND"
        label-print "C0603X5R1V106M030BC" "100nF Capacitor"
        label-print "MY-PART" "Custom part" --url "https://example.com/datasheet.pdf"
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Validate part number
    if not validate_part_number(part_number):
        click.echo(f"❌ Invalid part number: {part_number}", err=True)
        click.echo("   Part numbers must be 3-50 alphanumeric characters.", err=True)
        sys.exit(1)

    # Use custom URL or perform lookup
    if url:
        # Skip lookup, use provided URL
        click.echo(f"📦 Part: {part_number}")
        click.echo(f"   📄 Custom URL: {url}")
        part_name = part_number
        datasheet_url = url
    else:
        # Detect distributor and perform lookup
        distributor = detect_distributor(part_number)
        distributor_name = get_distributor_name(distributor)
        click.echo(f"📦 Part: {part_number} ({distributor_name})")

        # Query distributor for part info
        click.echo("🔍 Looking up part information...")
        lookup_client = PartLookupClient(mouser_api_key=mouser_key)
        part_name, datasheet_url = lookup_client.get_part_info(part_number)

        if part_name != part_number:
            click.echo(f"   Found: {part_name}")
        else:
            click.echo(f"   Using part number as name: {part_number}")

        if datasheet_url:
            click.echo(f"   📄 Datasheet: {datasheet_url}")
        else:
            click.echo("   (No datasheet found)")

    # Use provided info line or default
    final_info_line = info_line or "Electronics"
    if not info_line:
        click.echo(f"   ℹ️  Using default info line: {final_info_line}")

    # Generate label
    click.echo("🖨️  Generating label...")
    generator = LabelGenerator()
    label_img = generator.generate(
        part_name=part_name,
        info_line=final_info_line,
        datasheet_url=datasheet_url,
    )

    # Save image if requested
    if save_image:
        generator.save_to_file(label_img, save_image)
        click.echo(f"✅ Label image saved to {save_image}")

    # Print to printer (unless dry-run)
    if not dry_run:
        printer = BrotherPrinter(printer_id=printer_id, model=model)

        if not printer.validate_connection():
            click.echo("❌ Could not connect to printer", err=True)
            click.echo("   Make sure your Brother PT-P700 is connected and powered on.", err=True)
            click.echo("   Run: brother_ql discover", err=True)
            sys.exit(1)

        click.echo(f"   Using printer: {printer.printer_id}")

        if printer.print_image(label_img, label_size="12"):
            click.echo("✅ Label printed successfully!")
        else:
            click.echo("❌ Print failed", err=True)
            sys.exit(1)
    else:
        click.echo("✅ Dry-run complete (no print)")


if __name__ == "__main__":
    main()
