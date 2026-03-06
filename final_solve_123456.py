import subprocess
import os

ALPHABET = 'abcdefghijklmnopqrstuvwxyz'
COMMON_WORDS = ['the','and','you','are','for','key','aes','secret','token','stop','congratulations','solution','passphrase','reveal','magic','decrypt','submit','found','your','use','flag']

def score_text(text):
    t = text.lower()
    return sum(1 for w in COMMON_WORDS if w in t)

def caesar_decrypt(text, key):
    res = ""
    for c in text:
        if c.lower() in ALPHABET:
            is_upper = c.isupper()
            idx = (ALPHABET.index(c.lower()) - key) % 26
            res += ALPHABET[idx].upper() if is_upper else ALPHABET[idx]
        else:
            res += c
    return res

def solve():
    pwd = "4072023370"
    in_file = "problem_file.enc"
    
    # Try common ciphers
    for cipher in ["-aes-256-cbc", "-aes-128-cbc", "-des-ede3-cbc", "-des-cbc"]:
        for kdf in [["-pbkdf2"], ["-md", "md5"], ["-md", "sha256"], []]:
            cmd = ["openssl", "enc", "-d", cipher] + kdf + ["-pass", f"pass:{pwd}", "-in", in_file]
            r = subprocess.run(cmd, capture_output=True)
            if r.returncode == 0:
                decrypted_bytes = r.stdout
                try:
                    text = decrypted_bytes.decode('utf-8', errors='replace')
                except:
                    continue
                
                # Check Caesar shifts
                for shift in range(26):
                    shifted = caesar_decrypt(text, shift)
                    score = score_text(shifted)
                    if score >= 3:
                        print(f"SUCCESS! cipher={cipher} kdf={kdf} shift={shift}")
                        print(f"Decrypted: {shifted}")
                        return True
    return False

if __name__ == "__main__":
    if not solve():
        print("Failed to find result.")
