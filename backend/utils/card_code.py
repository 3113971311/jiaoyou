import hashlib
import secrets

from config import CARD_PEPPER, CARD_PREVIOUS_PEPPERS

CHARSET = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'

def generate_code() -> str:
    chars = []
    while len(chars) < 16:
        b = secrets.randbits(8)
        if b < 240: chars.append(CHARSET[b % 30])
    s = ''.join(chars)
    return f"{s[0:4]}-{s[4:8]}-{s[8:12]}-{s[12:16]}"

def normalize_code_text(text: str) -> str:
    return text.replace('-', '').upper()

def hash_text(text: str, pepper: str | None = None) -> str:
    return hashlib.sha256(((pepper or CARD_PEPPER) + normalize_code_text(text)).encode()).hexdigest()

def hash_candidates(text: str) -> list[str]:
    hashes = [hash_text(text, CARD_PEPPER)]
    for pepper in CARD_PREVIOUS_PEPPERS:
        digest = hash_text(text, pepper)
        if digest not in hashes:
            hashes.append(digest)
    return hashes
