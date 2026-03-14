"""Command-line interface for label-scan."""

import click
import logging
import sys
import yaml
import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict, Any

from .llm_client import LLMClient
from .part_number import detect_distributor, Distributor
from .part_lookup import PartLookupClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def process_image(
    image_path: Path,
    llm_client: LLMClient,
    lookup_client: PartLookupClient,
    skip_lookup: bool = False,
) -> Dict[str, Any]:
    """
    Process a single label image.

    Args:
        image_path: Path to label image
        llm_client: LLM client for extraction
        lookup_client: Part lookup client
        skip_lookup: Skip distributor lookup

    Returns:
        Dictionary with label data
    """
    logger.info(f"Processing {image_path.name}...")

    # Extract data from image
    extracted = llm_client.extract_label_data(image_path)

    if "error" in extracted:
        logger.error(f"Failed to extract data from {image_path.name}: {extracted['error']}")
        return {
            "image": str(image_path),
            "error": extracted["error"],
            "part_number": "",
            "title": "",
            "description": "",
            "url": "",
        }

    # Get part numbers
    manufacturer_pn = extracted.get("manufacturer_pn", "")
    distributor_pn = extracted.get("distributor_pn", "")
    raw_description = extracted.get("description", "")

    # Try to get better data from distributor lookup
    if not skip_lookup and (distributor_pn or manufacturer_pn):
        # Choose which part number to lookup
        # For Digi-Key and unknown distributors, prefer manufacturer P/N for Mouser fuzzy search
        part_to_lookup = distributor_pn or manufacturer_pn
        distributor = detect_distributor(part_to_lookup)

        # If Digi-Key or unknown, use manufacturer P/N for better Mouser fuzzy match
        if distributor in [Distributor.DIGI_KEY, Distributor.UNKNOWN] and manufacturer_pn:
            part_to_lookup = manufacturer_pn

        logger.info(f"Looking up {part_to_lookup} on {distributor.value}...")
        try:
            # get_part_info handles all distributors including fuzzy search fallback
            lookup_name, lookup_url = lookup_client.get_part_info(part_to_lookup)
            if lookup_name != part_to_lookup:
                # Got useful data from lookup
                raw_description = lookup_name
                url = lookup_url or ""
            else:
                url = lookup_url or ""
        except Exception as e:
            logger.warning(f"Lookup failed: {e}")
            url = ""
    else:
        url = ""

    # Clean up the description using LLM
    if raw_description:
        cleaned = llm_client.cleanup_label_text(manufacturer_pn, raw_description)
        title = cleaned.get("title", manufacturer_pn[:20])
        description = cleaned.get("description", raw_description[:50])
    else:
        title = manufacturer_pn[:20]
        description = "Unknown component"

    return {
        "image": str(image_path),
        "part_number": manufacturer_pn or distributor_pn or "UNKNOWN",
        "title": title,
        "description": description,
        "url": url,
        "raw_data": {
            "extracted": extracted,
        },
    }


@click.command()
@click.argument("images", nargs=-1, type=click.Path(exists=True), required=True)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default=None,
    help="Output YAML file (default: labels.yaml in current directory)",
)
@click.option(
    "--edit",
    "-e",
    is_flag=True,
    help="Open YAML in $EDITOR after generation",
)
@click.option(
    "--print",
    "-p",
    "print_labels",
    is_flag=True,
    help="Print labels after editing (requires --edit)",
)
@click.option(
    "--skip-lookup",
    is_flag=True,
    help="Skip distributor lookup (faster, uses only label data)",
)
@click.option(
    "--mouser-key",
    default=None,
    envvar="MOUSER_API_KEY",
    help="Mouser API key",
)
@click.option(
    "-v", "--verbose",
    is_flag=True,
    help="Verbose output",
)
def main(
    images: tuple,
    output: str,
    edit: bool,
    print_labels: bool,
    skip_lookup: bool,
    mouser_key: str,
    verbose: bool,
):
    """
    Scan component labels and generate print-ready YAML.

    IMAGES: One or more image files or glob patterns

    Example:
        label-scan ~/Downloads/parts/*.jpg -e -p
        label-scan image1.jpg image2.jpg -o labels.yaml
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Expand image paths
    image_paths = []
    for img in images:
        path = Path(img)
        if path.is_file():
            image_paths.append(path)
        else:
            # Try glob pattern
            parent = path.parent
            pattern = path.name
            matches = list(parent.glob(pattern))
            image_paths.extend(matches)

    if not image_paths:
        click.echo("❌ No images found", err=True)
        sys.exit(1)

    click.echo(f"📸 Found {len(image_paths)} images")

    # Initialize clients
    llm_client = LLMClient()
    lookup_client = PartLookupClient(mouser_api_key=mouser_key, llm_client=llm_client) if not skip_lookup else None

    # Process all images
    results = []
    for img_path in image_paths:
        try:
            result = process_image(img_path, llm_client, lookup_client, skip_lookup)
            results.append(result)
            click.echo(f"  ✓ {img_path.name}: {result['title']}")
        except Exception as e:
            logger.error(f"Failed to process {img_path.name}: {e}")
            results.append({
                "image": str(img_path),
                "error": str(e),
                "part_number": "",
                "title": "",
                "description": "",
                "url": "",
            })
            click.echo(f"  ✗ {img_path.name}: {e}")

    # Generate YAML
    output_path = Path(output) if output else Path("labels.yaml")

    yaml_data = {
        "labels": [
            {
                "part_number": r["part_number"],
                "title": r["title"],
                "description": r["description"],
                "url": r.get("url", ""),
                "image": r["image"],
            }
            for r in results
        ]
    }

    with open(output_path, "w") as f:
        yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)

    click.echo(f"\n✅ Generated {output_path}")

    # Open in editor if requested
    if edit:
        import os
        editor = os.environ.get("EDITOR", "vi")
        click.echo(f"Opening in {editor}...")

        try:
            subprocess.run([editor, str(output_path)], check=True)
        except subprocess.CalledProcessError:
            click.echo(f"❌ Editor exited with error", err=True)
            sys.exit(1)
        except FileNotFoundError:
            click.echo(f"❌ Editor '{editor}' not found", err=True)
            sys.exit(1)

        # Reload YAML after editing
        with open(output_path) as f:
            yaml_data = yaml.safe_load(f)

    # Print labels if requested
    if print_labels:
        if not edit:
            click.echo("⚠️  --print requires --edit (skipping print)", err=True)
        else:
            click.echo("\n🖨️  Printing labels...")
            from .printer import BrotherPrinter
            from .label_generator import LabelGenerator

            printer = BrotherPrinter()
            generator = LabelGenerator()

            for i, label_data in enumerate(yaml_data.get("labels", [])):
                is_last = (i == len(yaml_data["labels"]) - 1)
                chain = not is_last  # Chain all except last

                part_number = label_data.get("part_number", "")
                title = label_data.get("title", "")
                description = label_data.get("description", "")
                url = label_data.get("url", "")

                click.echo(f"  Printing: {title}")

                # Generate label
                label_img = generator.generate(
                    part_name=title,
                    info_line=description,
                    datasheet_url=url if url else None,
                )

                # Print with chain mode
                success = printer.print_image(label_img, label_size="12", chain=chain)

                if not success:
                    click.echo(f"  ❌ Failed to print {title}", err=True)
                    break

            click.echo("✅ All labels printed!")


if __name__ == "__main__":
    main()
