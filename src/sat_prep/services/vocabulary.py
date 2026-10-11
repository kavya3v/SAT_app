"""Small, locally authored vocabulary rotation for daily SAT-style practice."""

from datetime import datetime
from zoneinfo import ZoneInfo

WORDS = (
    ('lucid', 'Clear and easy to understand.'),
    ('infer', 'To reach a conclusion from evidence rather than a direct statement.'),
    ('corroborate', 'To support a claim with additional evidence.'),
    ('ambiguous', 'Having more than one possible meaning.'),
    ('pragmatic', 'Focused on what works in practice.'),
    ('mitigate', 'To make something less severe or harmful.'),
    ('conjecture', 'An explanation or opinion formed without enough evidence to be certain.'),
    ('scrutinize', 'To examine something very carefully.'),
    ('substantiate', 'To provide evidence that supports a claim.'),
    ('nuance', 'A small but meaningful difference in meaning or expression.'),
    ('tentative', 'Not final or certain; open to change.'),
    ('coherent', 'Logical and well connected.'),
    ('discrepancy', 'A difference between things expected to agree.'),
    ('refute', 'To show that a claim is false using evidence or reasoning.'),
    ('plausible', 'Reasonable enough to seem possible or true.'),
    ('impartial', 'Fair and not favoring one side.'),
    ('concise', 'Expressing an idea clearly in few words.'),
    ('pervasive', 'Present or spreading throughout many parts of something.'),
    ('resilient', 'Able to recover after difficulty or disruption.'),
    ('delineate', 'To describe or outline something precisely.'),
    ('empirical', 'Based on observation or experiment.'),
    ('inadvertent', 'Unintentional; happening by accident.'),
    ('elaborate', 'To explain something in more detail.'),
    ('bolster', 'To strengthen or support something.'),
    ('equivocal', 'Unclear or open to different interpretations.'),
    ('conventional', 'Following an established or commonly accepted approach.'),
    ('innovative', 'Introducing new ideas or methods.'),
    ('concede', 'To acknowledge that a point is true, often reluctantly.'),
    ('salient', 'Especially noticeable or relevant.'),
    ('synthesize', 'To combine ideas or information into a connected whole.'),
)


def daily_word(on_date=None):
    """Keep the word stable for a Los Angeles calendar day across UI reruns."""
    day = on_date if on_date is not None else datetime.now(ZoneInfo('America/Los_Angeles')).date()
    word, meaning = WORDS[day.toordinal() % len(WORDS)]
    return {'word': word, 'meaning': meaning}
