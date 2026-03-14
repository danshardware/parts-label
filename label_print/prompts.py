"""Prompts for LLM-based label processing.

Edit these prompts to customize label extraction and cleanup behavior.
"""

# Prompt for extracting data from component label images
LABEL_EXTRACTION_PROMPT = """Analyze this electronic component label and extract the following information in JSON format:

{
  "distributor": "name of distributor (e.g., Mouser, Digi-Key, LCSC)",
  "distributor_pn": "distributor part number",
  "manufacturer_pn": "manufacturer part number",
  "description": "brief component description from label",
  "manufacturer": "manufacturer name if visible",
  "quantity": "quantity if visible",
  "additional_info": "any other relevant information"
}

Only include fields that are clearly visible in the label. Return ONLY the JSON, no other text."""


# Prompt for cleaning up part descriptions for label printing
LABEL_CLEANUP_PROMPT = """You are helping create concise labels for electronic components in a PCB assembly workflow.

Component Information:
Manufacturer P/N: {manufacturer_pn}
Raw Description: {raw_description}

Task: Extract the most important information for a small label (12mm tape, ~20 characters max per line).

Return JSON with:
{{
  "title": "Key identification in 1-4 words (e.g., '10µH 1.9A', 'LM1117 3.3V', '74LS04', '100nF 50V')",
  "description": "Brief technical summary (2-10 words max, e.g., 'Low ESR ceramic capacitor' or 'Unshielded power inductor, 2.7A sat')"
}}

## General Guidelines

- Focus on PRIMARY electrical specs (value, voltage, current, frequency, etc.)
- Skip tape/reel info, RoHS status, temperature grades, packaging variants
- Use standard abbreviations: µH, nF, pF, V, A, mA, MHz, kHz, Ω, kΩ, MΩ
- Always use metric prefixes: µ (micro), m (milli), k (kilo), M (mega)
- Use larger units when sensible: "1.5A" not "1500mA" (but use mA for < 100mA)
- Abbreviate: "XTAL" (crystal), "Rot" (rotary), "Reg" (regulator), "Conv" (converter), "Recept" (receptacle), "Horiz"/"Vert" (orientation), "Tant" (tantalum), "Poly" (polymer), "Alum" (aluminum electrolytic)
- For multi-channel parts use: "Dual OpAmp", "Quad 2-in NAND", "2Ch Buck" (don't repeat specs per channel)

## IC Part Number Handling

- Title should be SHORTEST version without packaging variants
- Remove: -TSSOP, -SOT23, -0805, -ND, /NOPB, -R7, -RL, -AU, -MU, -PU, -ARMZ, -DBVR
- Keep functional variants: -3.3, -5.0, -ADJ, -12, -N (N-channel), -P (P-channel)
- Examples: "ATMEGA328P" not "ATMEGA328P-AU", "AD8420" not "AD8420ARMZ"
- Description should contain key differentiating features

## Category-Specific Instructions

### Passives - Title Format:
- **Capacitors**: value + voltage (e.g., "100nF 50V", "10µF 16V")
- **Resistors**: value, add power if space (e.g., "10kΩ" or "10kΩ 1/4W")
- **Inductors**: value + current (e.g., "10µH 1.9A", "220µH 2.7A")
- **Crystals**: frequency (e.g., "16MHz", "32.768kHz")

### Passives - Description Format:
- **Capacitors**: Include dielectric for critical ones, tolerance if ≤5%% (e.g., "X7R ceramic 20%%, 0805" or "Tant 10%%")
- **Resistors**: Include tolerance if ≤1%%, package size (e.g., "1%% 0603" or "1/4W THT")
- **Inductors**: Saturation current, shielding (e.g., "Unshielded 2.7A sat, 0403")
- **Crystals**: Tolerance + package (e.g., "20ppm 3.2x2.5mm" or "±100ppm radial")

### Active Components - Title Format:
- **Voltage/Current Regulators**: Part# + voltage (e.g., "LM1117 3.3V", "LM7805")
- **Op Amps**: Part# or key spec (e.g., "LM358", "OPA2134")
- **MOSFETs**: Channel + voltage + current (e.g., "N-Ch 60V 30A", "P-Ch 20V 4A")
- **BJTs**: Type + voltage + current (e.g., "NPN 40V 200mA", "PNP 45V 100mA")
- **Diodes**: Type + voltage + current (e.g., "Schottky 40V 1A", "1N4148", "Zener 5.1V 1W")
- **LEDs**: Color + package (e.g., "Red 0805", "Blue 3mm", "RGB 5050")

### Active Components - Description Format:
- **Regulators**: Type + input/output range (e.g., "LDO 15V in, 3.3V/800mA out" or "Buck converter 4-36V in, adj out")
- **Op Amps**: Voltage range + key feature (e.g., "Dual rail-to-rail, 3MHz, 2.7-5.5V")
- **MOSFETs**: Rds(on) + gate type if relevant (e.g., "Logic level, 8mΩ Rds" or "50mΩ Rds, TO-220")
- **BJTs**: Gain range if important (e.g., "General purpose, hFE 100-300")
- **Diodes**: Forward voltage, speed if relevant (e.g., "Vf 0.3V, fast switching" or "500mW, DO-35")

### Other Components:
- **Connectors**: Pins + pitch + orientation (e.g., "2x5 2.54mm", "USB-C Recept", "JST-PH 2")
- **Fuses**: Current + voltage + speed (e.g., "2A 250V Fast", "500mA Slow Blow")

## Tolerance Guidelines

- Include tolerance ONLY if non-standard:
  - Resistors: Show if ≤1%% (skip ±5%%, ±10%%)
  - Capacitors: Show if ≤5%% (skip ±10%%, ±20%%)
  - Crystals: Always show (e.g., "±20ppm", "±100ppm")

## Priority When Space Limited

Most important → Least important:
1. Component value/function (10µH, 3.3V, NPN)
2. Voltage/current rating
3. Key feature (Schottky, LDO, Fast)
4. Package size (only if critical for fit)
5. Tolerance (only if special)

## Handling Missing Information

- If description lacks key specs (common with generic parts):
  - Use part number as title
  - Use whatever description is available
  - Don't make up specifications

## Examples

BAD titles:
  - "Instrumentation Amplifier" (too generic)
  - "AD8420ARMZ-R7" (includes packaging variant)
  - "1 ohm" (use 'Ω' to save space)

GOOD titles:
  - "AD8420" (IC without package suffix)
  - "10µH 2.7A" (inductor with key specs)
  - "100nF 50V" (capacitor value + voltage)
  - "N-Ch 60V 30A" (MOSFET specs)
  - "Schottky 40V 1A" (diode type + specs)

Think carefully about what a designer would need to work with this part and ensure the description captures that.

Return ONLY valid JSON."""


# Prompt for verifying if two components are the same (for fuzzy matching)
COMPONENT_MATCH_VERIFICATION_PROMPT = """Compare these two electronic components and determine if they are the same part.

Component A (from label):
  Manufacturer P/N: {pn_a}
  Description: {desc_a}

Component B (from search result):
  Manufacturer P/N: {pn_b}
  Description: {desc_b}

Consider:
- Part numbers may differ in packaging suffixes (-ND, /NOPB, etc.)
- Descriptions may vary in detail but should describe same component type
- Example: "TL3311DBVR" and "TL331IDBVR" are DIFFERENT (different part numbers)
- Example: "TL3311DBVR" and "TL3311DBVR-ND" are the SAME (just distributor or packaging suffix)

Return JSON:
{{
  "match": true/false,
  "confidence": "high/medium/low",
  "reason": "Brief explanation"
}}

Return ONLY valid JSON."""
