"""Print labels from YAML file."""

import click
import yaml
import sys
from pathlib import Path

from .label_generator import LabelGenerator
from .printer import BrotherPrinter


@click.command()
@click.argument("yaml_file", type=click.Path(exists=True), required=True)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Generate labels but don't print",
)
@click.option(
    "--save-dir",
    type=click.Path(),
    default=None,
    help="Directory to save label images",
)
@click.option(
    "--printer-id",
    default=None,
    envvar="BROTHER_QL_PRINTER",
    help="Brother printer identifier",
)
@click.option(
    "--model",
    default="QL-700",
    envvar="BROTHER_QL_MODEL",
    help="Printer model",
)
def main(
    yaml_file: str,
    dry_run: bool,
    save_dir: str,
    printer_id: str,
    model: str,
):
    """
    Print labels from a YAML file.

    Example:
        label-print-yaml labels.yaml
        label-print-yaml labels.yaml --dry-run
        label-print-yaml labels.yaml --save-dir ./images
    """
    # Load YAML
    yaml_path = Path(yaml_file)
    try:
        with open(yaml_path) as f:
            data = yaml.safe_load(f)
    except Exception as e:
        click.echo(f"❌ Failed to load YAML: {e}", err=True)
        sys.exit(1)

    labels = data.get("labels", [])
    if not labels:
        click.echo("❌ No labels found in YAML", err=True)
        sys.exit(1)

    click.echo(f"📋 Found {len(labels)} labels in {yaml_path.name}")

    # Initialize generator
    generator = LabelGenerator()

    # Initialize printer if not dry-run
    printer = None
    if not dry_run:
        printer = BrotherPrinter(printer_id=printer_id, model=model)
        if not printer.validate_connection():
            click.echo("❌ Could not connect to printer", err=True)
            sys.exit(1)
        click.echo(f"   Using printer: {printer.printer_id}")

    # Create save directory if needed
    if save_dir:
        save_path = Path(save_dir)
        save_path.mkdir(parents=True, exist_ok=True)

    # Process each label
    for i, label_data in enumerate(labels):
        part_number = label_data.get("part_number", "")
        title = label_data.get("title", "")
        description = label_data.get("description", "")
        url = label_data.get("url", "")

        if not title:
            click.echo(f"  ⚠️  Skipping label {i+1}: no title", err=True)
            continue

        click.echo(f"  {i+1}/{len(labels)}: {title}")

        # Generate label
        try:
            label_img = generator.generate(
                part_name=title,
                info_line=description,
                datasheet_url=url if url else None,
            )
        except Exception as e:
            click.echo(f"  ❌ Failed to generate: {e}", err=True)
            continue

        # Save if requested
        if save_dir:
            safe_filename = f"{part_number or title}".replace("/", "-").replace(" ", "_")
            save_file = save_path / f"{safe_filename}.png"
            generator.save_to_file(label_img, str(save_file))
            click.echo(f"     Saved to {save_file}")

        # Print
        if not dry_run and printer:
            is_last = (i == len(labels) - 1)
            chain = not is_last  # Chain all except last

            success = printer.print_image(label_img, label_size="12", chain=chain)
            if not success:
                click.echo(f"  ❌ Print failed", err=True)
                break
        elif dry_run:
            click.echo(f"     (Dry-run, not printed)")

    if not dry_run and printer:
        click.echo(f"\n✅ Printed {len(labels)} labels!")
    else:
        click.echo(f"\n✅ Generated {len(labels)} labels (dry-run)")


if __name__ == "__main__":
    main()
