# Adding a New Language to Talking Clock Audio

This guide walks you through creating a complete time phrase configuration for a new language.

## Overview

To add support for a new language, you'll need to:

1. Create a YAML configuration file defining time phrases
2. Test the configuration with the CLI
3. Generate audio files using a Piper TTS voice model

## Prerequisites


- Talking Clock Audio installed 
- Basic understanding of how time is spoken in your target language
- A Piper TTS voice model for your language (see Finding Voice Models below)

## Step 0: Setup Environment

- Clone this repository locally
- OPTIONAL: Create a virtual environment
- Install requirements file `pip install -r requirements.txt`
- Install Talking Clock into the Python Environment: `pip install -e .` from this directory

## Step 1: Find Available Voice Models

First, check if Piper has voice models for your target language:

```bash
tca list-models --remote | grep -i "your_language"
```

Example for German:

```bash
tca list-models --remote | grep -i german
```

Output shows available models:

```
de_DE - German (Germany):
  de_DE/thorsten/high
  de_DE/thorsten/medium
  de_DE/thorsten/low
```

Choose the highest quality model available (e.g. `de_DE/thorsten/high`)

If your language isn't available, you may need to use a different TTS system or train your own model.

## Step 2: Create the YAML Configuration File

A YAML file is required to indicate the rules for telling time in your language. Many languages have several "modes" for telling time:

- operational: Extremely formal and rule driven. This is typically used by the military, pilots and law enforcement
- broadcast: Formal and standardized way of communicating time in news casts, train stations and airports.
- standard: Formal and structured, but used by common people in the streets and offices.
- informal: Very casual and used among friends and family and typically less precise (e.g. 13:47 becomes "A quarter to two")

Create a new file: `time_formats/time_phrases_{locale}.yaml`

Example: `time_formats/time_phrases_de_DE.yaml` for German

### Optional LLM (Chat GPT) Configuration

Building the yaml file can be difficult. There is a [time_format_prompt.md](./time_format_prompt.md) that can be fed directly into your favorite Large Language Model (Chat GPT, Claude, etc.) and used as a way to build the yaml file by answering questions and providing examples.  This isn't guaranteed to work, but it may get you started.

Download the markdown file, and paste the text exactly as it is into the LLM and start answering questions. 

### File Structure

```yaml
locale: de_DE
description: >
  German time phrases with four standardized output modes.
  Audio generation will automatically deduplicate vocab entries with identical text
  (case-insensitive comparison, but whitespace and punctuation are preserved).

vocab:
  words:
    # Common time-related words
    uhr: "Uhr"
    nach: "nach"
    vor: "vor"
    
  number_words:
    # All hours (0-23) and minutes (0-59)
    0: "null"
    1: "eins"
    2: "zwei"
    # ... continue for all numbers 0-59

fields:
  computed:
    # Computed values used in rules
    hour_24_word: "number_words[hour_24]"
    minute_word: "number_words[minute]"
    hour_12: "((hour_24 + 11) mod 12) + 1"
    hour_12_word: "number_words[hour_12]"

modes:
  operational:
    # Military/radio precision
    rule_order: ["on_the_hour", "hour_minute"]
    rules:
      on_the_hour:
        when: {minute_eq: 0}
        tokens: ["{hour_24_word}", "{uhr}"]
      hour_minute:
        when: {any: true}
        tokens: ["{hour_24_word}", "{uhr}", "{minute_word}"]
  
  broadcast:
    # News/announcements
    # ... define rules
  
  standard:
    # Professional/office
    # ... define rules
  
  casual:
    # Conversational
    # ... define rules

rendered_examples:
  # Include examples to document expected output
  midnight:
    00:00:
      operational: "null Uhr"
      broadcast: "null Uhr"
      standard: "Mitternacht"
      casual: "Mitternacht"
```

### Understanding the YAML Sections

#### vocab.words

Define common words used in time expressions:

- Time markers: "o'clock", "past", "to", "half", "quarter"
- Day periods: "a.m.", "p.m.", "morning", "afternoon", "evening", "night"
- Special cases: "midnight", "noon"

Words can have multiple variants for random selection:

```yaml
to: 
  - "to"
  - "till"
  - "until"
```

#### vocab.number_words

Define ALL numbers from 0-59. These are used for hours and minutes.

Important: Include special cases for your language:

- Compound numbers (e.g., "twenty one" vs "twentyone")
- Language-specific rules (e.g., Dutch "drieëntwintig" with diacritics)
- Zero variations (some languages use different words for "zero" vs "oh")

#### fields.computed

Define computed values derived from the base `hour_24` (0-23) and `minute` (0-59) inputs.

Common computed fields:

```yaml
fields:
  computed:
    # Direct lookups
    hour_24_word: "number_words[hour_24]"
    minute_word: "number_words[minute]"
    
    # Convert 24h to 12h format
    hour_12: "((hour_24 + 11) mod 12) + 1"
    hour_12_word: "number_words[hour_12]"
    
    # For "to" phrases (e.g., "ten to three")
    next_hour_12: "(hour_12 mod 12) + 1"
    next_hour_12_word: "number_words[next_hour_12]"
    minute_to_next: "60 - minute"
    minute_to_next_word: "number_words[minute_to_next]"
    
    # Day period (AM/PM or language equivalent)
    day_period:
      when_hour_24_lt_12: "am"
      otherwise: "pm"
    day_period_word: "words[day_period]"
```

Special case: Languages where "half" means "halfway to next hour":

```yaml
# Dutch: "half twee" = 1:30 (halfway to 2:00)
next_hour_12: "(hour_12 mod 12) + 1"
next_hour_12_word: "number_words[next_hour_12]"
```

#### modes

Define the four standard speaking modes. Each mode has rules that match specific times.

**Mode definitions:**

- **operational**: Military/radio precision with maximum clarity
- **broadcast**: News/announcements, clear and formal
- **standard**: Professional/office use, natural but precise
- **casual**: Conversational, uses relative phrases

**Rule structure:**

```yaml
modes:
  casual:
    rule_order: ["midnight", "half_past", "quarter_past", "default"]
    rules:
      midnight:
        when: {hour_24_eq: 0, minute_eq: 0}
        tokens: ["{midnight}"]
      
      half_past:
        when: {minute_eq: 30}
        tokens: ["{half}", "{past}", "{hour_12_word}"]
      
      quarter_past:
        when: {minute_eq: 15}
        tokens: ["{quarter}", "{past}", "{hour_12_word}"]
      
      default:
        when: {any: true}
        tokens: ["{hour_12_word}", "{minute_word}"]
```

**Rule matching:**

Rules are evaluated in the order specified by `rule_order`. The first matching rule wins.

**Condition operators:**

- `minute_eq: 30` - minute equals 30
- `minute_lt: 10` - minute less than 10
- `minute_gt: 30` - minute greater than 30
- `minute_lte: 30` - minute less than or equal to 30
- `minute_gte: 30` - minute greater than or equal to 30
- `hour_24_eq: 0` - hour equals 0
- `any: true` - always matches (use as fallback)

Multiple conditions in one rule create AND logic (all must match):

```yaml
midnight:
  when: {hour_24_eq: 0, minute_eq: 0}  # Both must be true
  tokens: ["{midnight}"]
```

**Token expansion:**

Tokens in curly braces reference computed fields:

- `{hour_12_word}` → looks up computed field `hour_12_word` → returns vocab reference
- `{midnight}` → direct word reference
- Literal words without braces: `past` → `words.past`

#### rendered_examples

Document expected outputs for validation. Include examples for:

- Midnight (00:00)
- Morning times (before noon)
- Noon (12:00)
- Afternoon times
- Evening times

Example:

```yaml
rendered_examples:
  midnight:
    00:00:
      operational: "null Uhr"
      broadcast: "Mitternacht"
      standard: "Mitternacht"
      casual: "Mitternacht"
  
  morning:
    11:30:
      operational: "elf Uhr dreißig"
      broadcast: "elf Uhr dreißig"
      standard: "halb zwölf"
      casual: "halb zwölf"
```

## Step 3: Test Your Configuration

Validate the configuration and preview sample phrases:

```bash
tca validate time_formats/time_phrases_de_DE.yaml casual
```

This shows:

- Available modes in the file
- Number of unique audio files needed
- Sample time phrases for the selected mode

Example output:

```
Loaded configuration: de_DE
Available modes: operational, broadcast, standard, casual

Vocabulary: 73 unique audio files needed

Sample phrases for mode 'casual':
  00:00 (midnight    ): Mitternacht
  06:00 (early morning): sechs Uhr
  11:30 (late morning ): halb zwölf
  12:00 (noon        ): Mittag
  13:45 (afternoon   ): Viertel vor zwei
  18:30 (evening     ): halb sieben
  23:00 (late night  ): elf Uhr

Configuration is valid!
```

Fix any errors before proceeding to audio generation.

## Step 4: Download Voice Model

Find and download a voice model for your language:

```bash
# List available models
tca list-models --remote | grep -i german

# Download a specific model
tca get-model de_DE/thorsten/medium
```

The model downloads to `./models/de/de_DE/thorsten/medium/`

## Step 5: Generate Audio Files

Generate the complete audio package:

```bash
tca generate time_formats/time_phrases_de_DE.yaml casual \
  --model ./models/de/de_DE/thorsten/medium/de_DE-thorsten-medium.onnx
```

This creates:

```
audio/de_DE_thorsten_medium_casual/
  config.json
  audio/
    word_uhr.wav
    word_nach.wav
    number_null.wav
    number_eins.wav
    ... (all vocab files)
```

Generation takes 2-5 minutes depending on vocabulary size.

## Step 6: Test the Generated Package

Verify the audio package works correctly:

```python
from talking_clock_audio.pico_audio import get_audio_files_for_time

# Test various times
times = [(0, 0), (11, 30), (13, 45), (23, 0)]

for hour, minute in times:
    files = get_audio_files_for_time(
        'audio/de_DE_thorsten_medium_casual/config.json',
        hour,
        minute
    )
    print(f"{hour:02d}:{minute:02d} -> {files}")
```

## Complete Example: Adding German

Here's a minimal but complete German configuration:

```yaml
locale: de_DE
description: German time phrases

vocab:
  words:
    uhr: "Uhr"
    nach: "nach"
    vor: "vor"
    halb: "halb"
    viertel: "Viertel"
    mitternacht: "Mitternacht"
    mittag: "Mittag"

  number_words:
    0: "null"
    1: "eins"
    2: "zwei"
    3: "drei"
    4: "vier"
    5: "fünf"
    6: "sechs"
    7: "sieben"
    8: "acht"
    9: "neun"
    10: "zehn"
    11: "elf"
    12: "zwölf"
    13: "dreizehn"
    14: "vierzehn"
    15: "fünfzehn"
    16: "sechzehn"
    17: "siebzehn"
    18: "achtzehn"
    19: "neunzehn"
    20: "zwanzig"
    21: "einundzwanzig"
    # ... continue through 59

fields:
  computed:
    hour_24_word: "number_words[hour_24]"
    minute_word: "number_words[minute]"
    hour_12: "((hour_24 + 11) mod 12) + 1"
    hour_12_word: "number_words[hour_12]"
    next_hour_12: "(hour_12 mod 12) + 1"
    next_hour_12_word: "number_words[next_hour_12]"

modes:
  operational:
    rule_order: ["on_the_hour", "hour_minute"]
    rules:
      on_the_hour:
        when: {minute_eq: 0}
        tokens: ["{hour_24_word}", "{uhr}"]
      hour_minute:
        when: {any: true}
        tokens: ["{hour_24_word}", "{uhr}", "{minute_word}"]

  casual:
    rule_order: ["midnight", "noon", "on_the_hour", "half_hour", "quarter_past", "default"]
    rules:
      midnight:
        when: {hour_24_eq: 0, minute_eq: 0}
        tokens: ["{mitternacht}"]
      noon:
        when: {hour_24_eq: 12, minute_eq: 0}
        tokens: ["{mittag}"]
      on_the_hour:
        when: {minute_eq: 0}
        tokens: ["{hour_12_word}", "{uhr}"]
      half_hour:
        when: {minute_eq: 30}
        tokens: ["{halb}", "{next_hour_12_word}"]
      quarter_past:
        when: {minute_eq: 15}
        tokens: ["{viertel}", "{nach}", "{hour_12_word}"]
      default:
        when: {any: true}
        tokens: ["{hour_12_word}", "{uhr}", "{minute_word}"]

rendered_examples:
  midnight:
    00:00:
      operational: "null Uhr"
      casual: "Mitternacht"
  
  morning:
    11:30:
      operational: "elf Uhr dreißig"
      casual: "halb zwölf"
```

## Common Patterns and Tips

### Pattern 1: Languages with "half to next hour"

Dutch and German use "half" to mean halfway TO the next hour:

- Dutch: "half twee" = 1:30 (halfway to 2:00)
- German: "halb zwölf" = 11:30 (halfway to 12:00)

Use the `next_hour_12_word` computed field:

```yaml
half_hour:
  when: {minute_eq: 30}
  tokens: ["{half}", "{next_hour_12_word}"]
```

### Pattern 2: Time of day markers

Many languages have context-specific day markers:

Dutch example:

```yaml
fields:
  computed:
    day_period:
      when_hour_24_lt_6: "nachts"      # 00:00-05:59
      when_hour_24_lt_12: "ochtends"   # 06:00-11:59
      when_hour_24_lt_18: "middags"    # 12:00-17:59
      otherwise: "avonds"               # 18:00-23:59
    day_period_word: "words[day_period]"

# Then use in rules:
standard_with_period:
  when: {any: true}
  tokens: ["{hour_12_word}", "{uhr}", "{minute_word}", "{day_period_word}"]
```

### Pattern 3: Leading zeros in formal speech

Some languages speak leading zeros differently:

```yaml
operational:
  rule_order: ["on_the_hour", "minute_lt_10", "hour_minute"]
  rules:
    minute_lt_10:
      when: {minute_lt: 10, minute_gt: 0}
      tokens: ["{hour_24_word}", "{null}", "{minute_word}"]
    # This produces "elf null sieben" for 11:07
```

### Pattern 4: Special vocabulary needs

Add words to vocab if they're used in multiple contexts:

```yaml
vocab:
  words:
    # Add "zero" or "null" if used as a filler word
    null: "null"
    
    # Add "twelve" if used differently than number_words[12]
    twelve: "zwölf"
```

### Pattern 5: Compound numbers

For languages with compound number words:

```yaml
number_words:
  21: "einundzwanzig"    # German: one-and-twenty
  22: "tweeëntwintig"    # Dutch: with diacritics
  30: "dertig"           # Dutch: not "drie-tig"
```

## Step 7: Validate Your Configuration

Test with different modes:

```bash
# Test casual mode
tca validate time_formats/time_phrases_de_DE.yaml casual

# Test operational mode
tca validate time_formats/time_phrases_de_DE.yaml operational

# Test with more samples
tca validate time_formats/time_phrases_de_DE.yaml casual --samples 7
```

Common validation errors:

**Error: "KeyError: 'words.something'"**

Solution: Add the missing word to `vocab.words` or reference the correct vocab entry.

**Error: "No matching rule found"**

Solution: Add a fallback rule with `when: {any: true}` at the end of rule_order.

## Step 8: Generate Audio

Once validation passes, generate the audio package:

```bash
# Download the voice model first
tca get-model de_DE/thorsten/medium

# Generate audio files
tca generate time_formats/time_phrases_de_DE.yaml casual \
  --model ./models/de/de_DE/thorsten/medium/de_DE-thorsten-medium.onnx
```

Output structure:

```
audio/de_DE_thorsten_medium_casual/
  config.json              # Pico configuration
  audio/                   # Audio files
    word_uhr.wav
    word_nach.wav
    number_null.wav
    ... (70-80 files typically)
```

## Step 9: Generate All Modes

Create packages for each mode you defined:

```bash
for mode in operational broadcast standard casual; do
  tca generate time_formats/time_phrases_de_DE.yaml $mode \
    --model ./models/de/de_DE/thorsten/medium/de_DE-thorsten-medium.onnx
done
```

## Testing the Generated Audio

Use Python to verify the audio package:

```python
from talking_clock_audio.pico_audio import get_audio_files_for_time

config_path = 'audio/de_DE_thorsten_medium_casual/config.json'

# Test specific times
test_times = [
    (0, 0, "midnight"),
    (6, 0, "morning"),
    (11, 30, "before noon"),
    (12, 0, "noon"),
    (13, 45, "afternoon"),
    (23, 59, "late night"),
]

for hour, minute, description in test_times:
    files = get_audio_files_for_time(config_path, hour, minute)
    print(f"{hour:02d}:{minute:02d} ({description}): {files}")
```

Listen to the generated files to verify quality and naturalness.

## Troubleshooting

### Audio files are empty or very small

Check that:
- The voice model downloaded correctly
- Piper TTS is installed (`pip list | grep piper`)
- The text in vocab doesn't have encoding issues

### Phrases sound unnatural

Review your rules and consider:
- Are you using the right computed fields?
- Do the rules match in the right order?
- Are there language-specific patterns you haven't captured?

### Missing vocabulary

If generation fails with "KeyError", check:
- All tokens reference words that exist in vocab
- Computed fields are defined before use
- Rule tokens don't reference non-existent fields

### Wrong time spoken

Verify:
- Hour/minute computation formulas are correct
- Rule conditions match the intended time ranges
- `rule_order` lists rules from most specific to most general

## Language-Specific Notes

### English (en_US, en_GB)

- Use 12-hour format in casual/standard modes
- AM/PM required in broadcast mode
- "quarter to", "half past" common in casual

### Dutch (nl_NL)

- "half" means halfway to NEXT hour
- Time-of-day markers: 's ochtends, 's middags, 's avonds, 's nachts
- 24-hour common in formal contexts

### German (de_DE)

- "halb" means halfway to next hour (like Dutch)
- "Viertel nach/vor" for quarter past/to
- "Uhr" always included except in very casual speech

## Reference Files

Study the existing configurations for patterns:

- `time_formats/time_phrases_en_US.yaml` - English (US)
- `time_formats/time_phrases_nl_NL.yaml` - Dutch

## Contributing Your Language

If you create a configuration for a new language:

1. Test thoroughly with all four modes
2. Include comprehensive `rendered_examples`
3. Add notes about language-specific patterns
4. Submit a pull request with your YAML file

## Advanced: Custom Modes

You can add custom modes beyond the four standard ones:

```yaml
modes:
  # Standard modes
  operational: { ... }
  broadcast: { ... }
  standard: { ... }
  casual: { ... }
  
  # Custom mode
  my_special_mode:
    rule_order: ["custom_rule"]
    rules:
      custom_rule:
        when: {any: true}
        tokens: ["{custom}", "{tokens}"]
```

Just add the required vocab words and generate as normal.

## Quick Reference Commands

```bash
# List remote models
tca list-models --remote

# Download a model
tca get-model <locale>/<voice>/<quality>

# Validate config
tca validate <yaml_file> <mode>

# Generate audio
tca generate <yaml_file> <mode> --model <path_to_onnx>

# Generate with custom output
tca generate <yaml_file> <mode> --model <path> --output-dir custom/path

# Force overwrite existing files
tca generate <yaml_file> <mode> --model <path> --force
```

## Next Steps

After generating audio packages:

1. Copy the complete directory to your Raspberry Pi Pico's SD card
2. Use the `pico_audio.py` module to load and play phrases
3. Integrate with your clock hardware and RTC

See the main project README for Pico integration details.
