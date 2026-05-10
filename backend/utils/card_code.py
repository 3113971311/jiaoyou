import uuid, hashlib, secrets
from config import CARD_PEPPER

CHARSET = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'

def generate_code() -> str:
    chars = []
    while len(chars) < 16:
        b = secrets.randbits(8)
        if b < 240: chars.append(CHARSET[b % 30])
    s = ''.join(chars)
    return f"{s[0:4]}-{s[4:8]}-{s[8:12]}-{s[12:16]}"

def hash_text(text: str) -> str:
    return hashlib.sha256((CARD_PEPPER + text.replace('-', '').upper()).encode()).hexdigest()
