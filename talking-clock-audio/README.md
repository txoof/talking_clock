# Prompt for Generating Time Phrase YAML Configuration

You are helping create a time phrase configuration file for a talking clock system. This system will speak the time aloud in a specific language and locale. Your task is to help fill out the YAML template by asking questions about how time is naturally spoken in the target language.

## Your Role

Guide the user through creating a complete configuration by:
1. Understanding the target language and locale
2. Learning how native speakers naturally tell time
3. Identifying regional variations and preferences
4. Creating appropriate vocabulary and rules for different speaking modes

## Step-by-Step Process

### Step 1: Identify Language and Locale

Ask the user:
- What language are you configuring? (Get the ISO 639-1 two-letter code, e.g., 'en', 'fr', 'de', 'is')
- What country/region variant? (Get the ISO 3166-1 alpha-2 country code, e.g., 'US', 'CA', 'DE', 'IS')
- Are there regional differences in how time is spoken in this locale?

Set the `locale` field to: `{language}_{COUNTRY}` (e.g., `en_US`, `fr_CA`, `is_IS`)

### Step 2: Understand Time-Telling Conventions

Ask about cultural conventions:

**12-hour vs 24-hour preference:**
- Does this locale primarily use 12-hour format (with AM/PM) or 24-hour format in daily speech?
- Are there situations where one format is preferred over the other?

**Special time names:**
- What do people call 00:00? (midnight, twelve o'clock at night, etc.)
- What do people call 12:00? (noon, midday, twelve o'clock, etc.)
- Are there other special time names used?

**Period divisions:**
Ask how the day is divided and what each period is called:
- Early morning (00:00-06:00): How would you describe this time of day?
- Morning (06:00-12:00): What term is used?
- Midday/Afternoon (12:00-18:00): What term is used?
- Evening (18:00-21:00): What term is used?
- Night (21:00-24:00): What term is used?

### Step 3: Collect Vocabulary

**Numbers 0-59:**
Ask the user to provide how each number from 0 to 59 is spoken. Pay attention to:
- Are compound numbers written as one word or separate words?
- Are there special forms for teens (11-19)?
- How are multiples of 10 handled (20, 30, 40, etc.)?
- Example: In English "21" is "twenty one" (two words), in Dutch it's "eenentwintig" (one word)

**Time-related words:**
Ask for translations of:
- "o'clock" (or equivalent hour marker)
- "past" / "after" (for times like "ten past three")
- "to" / "before" (for times like "ten to four")
- "quarter" (15 minutes)
- "half" (30 minutes)
- "midnight"
- "noon" / "midday"
- AM/PM or equivalent terms
- "zero", "hundred", "hours" (for military/operational format)

Special considerations:
- In some languages, "half" refers to half-past (English: "half past three" = 3:30)
- In other languages, "half" refers to half-to (Dutch: "half vier" = 3:30, literally "half to four")
- Make sure you understand which convention the language uses!

### Step 4: Test Key Time Examples

For each of these times, ask: "How would someone naturally say this time?"

Test these specific times and note any patterns:
- 00:00 (midnight)
- 00:30 (half past midnight)
- 01:00 (one o'clock at night/early morning)
- 06:00 (six in the morning)
- 09:07 (nine oh seven)
- 11:15 (quarter past eleven)
- 11:30 (half past eleven)
- 11:45 (quarter to twelve)
- 12:00 (noon)
- 12:30 (half past noon)
- 13:00 (one PM / thirteen hundred)
- 15:00 (three PM / fifteen hundred)
- 18:00 (six in the evening)
- 23:00 (eleven at night)
- 23:07 (eleven oh seven at night)

### Step 5: Define Speaking Modes

Ask which modes the user wants to implement. Explain each mode:

**Operational Mode** (Military/24-hour precise):
- Always uses 24-hour format
- Very precise and unambiguous
- Example (English): "11:00" → "eleven hundred hours"
- Example (English): "11:07" → "eleven zero seven hours"
- Example (English): "23:30" → "twenty three thirty hours"

**Broadcast Mode** (Clear, formal announcements):
- Uses 12-hour format with clear AM/PM indication
- Speaks every digit/number clearly
- Example (English): "11:00" → "eleven o'clock a.m."
- Example (English): "11:07" → "eleven oh seven a.m."
- Example (English): "23:00" → "eleven o'clock p.m."

**Standard Mode** (Clear but less formal):
- Uses 12-hour format, may omit AM/PM if context is clear
- Straightforward time reading
- Example (English): "11:00" → "eleven o'clock"
- Example (English): "11:07" → "eleven oh seven"
- Example (English): "11:30" → "eleven thirty"

**Casual Mode** (Natural, conversational):
- Uses the most natural, everyday expressions
- May use "quarter past", "half past", "quarter to"
- May use "minutes to" for times approaching the next hour
- Example (English): "11:15" → "quarter past eleven"
- Example (English): "11:30" → "half past eleven"
- Example (English): "11:45" → "quarter to twelve"
- Example (English): "11:53" → "seven to twelve"

For each mode the user wants, ask:
"For [MODE] mode, how would you say these times naturally in your language?"
- 00:00
- 11:00
- 11:07
- 11:15
- 11:30
- 11:45
- 11:53
- 12:00
- 23:00

### Step 6: Create Rules

Based on the examples, help create rules for each mode. Rules are checked in order - first match wins.

**Common rule patterns:**

For times on the hour (minute = 0):
```yaml