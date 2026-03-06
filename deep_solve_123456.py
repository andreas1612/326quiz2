import subprocess
import os

ALPHABETS = {
    '1':  'abcdefghijklmnopqrstuvwxyz',
    '2':  'abcdefghijklmnopqrstuvwxyz ',
    '3':  ' abcdefghijklmnopqrstuvwxyz',
    '4':  ',. abcdefghijklmnopqrstuvwxyz',
    '5':  ' -,.abcdefghijklmnopqrstuvwxyz',
    '6':  '-., abcdefghijklmnopqrstuvwxyz',
    '7':  ',.- abcdefghijklmnopqrstuvwxyz',
    '8':  ',-. abcdefghijklnmopqrstuvwxyz',
    '9':  '.,- abcdefghijklmnopqrstuvwxyz',
    '10': 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 -,.',
    '11': ' abcdefghijklmnopqrstuvwxyz:,.',
    '12': '0123456789,.%() ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz',
    '13': '0123456789.,%(  ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz',
    '14': 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 abcdefghijklmnopqrstuvwxyz',
    '15': 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789,.%()- ',
    '16': 'abcdefghijklmnopqrstuvwxyz,.! ',
    '17': 'abcdefghijklmnopqrstuvwxyz!,. ',
    '18': 'abcdefghijklmnopqrstuvwxyz0123456789,.! ',
    '19': 'abcdefghijklmnopqrstuvwxyz0123456789,!. ',
    '20': '0123456789,. abcdefghijklmnopqrstuvwxyz',
    '21': '0123456789 .,!abcdefghijklmnopqrstuvwxyz',
}

COMMON_WORDS = ['the','and','you','are','for','key','aes','secret','token',
                'stop','congratulations','solution','passphrase','reveal',
                'magic','decrypt','submit','found','your','use','flag',
                'this','have','with','that','from','they','will','been']

def score_text(text):
    t = text.lower()
    return sum(1 for w in COMMON_WORDS if w in t)

def caesar_decrypt(text, key, alphabet):
    alpha = list(alphabet)
    result = ""
    for char in text:
        if char in alpha:
            result += alpha[(alpha.index(char) - key) % len(alpha)]
        elif char.lower() in alpha:
            result += alpha[(alpha.index(char.lower()) - key) % len(alpha)].upper()
        else:
            result += char
    return result

def solve():
    pwd = "4072023370"
    in_file = "problem_file.enc"
    
    # Standard OpenSSL ciphers
    ciphers = ["-aes-256-cbc", "-aes-128-cbc", "-des-ede3-cbc", "-des-cbc"]
    kdfs = [["-pbkdf2"], ["-md", "md5"], ["-md", "sha256"], []]
    
    print(f"Brute forcing problem_file.enc with {len(ciphers)*len(kdfs)} OpenSSL combos...")
    
    for cipher in ciphers:
        for kdf in kdfs:
            cmd = ["openssl", "enc", "-d", cipher] + kdf + ["-pass", f"pass:{pwd}", "-in", in_file]
            r = subprocess.run(cmd, capture_output=True)
            if r.returncode == 0:
                decrypted_bytes = r.stdout
                try:
                    # Try different encodings
                    candidate_text = decrypted_bytes.decode('utf-8', errors='replace')
                except:
                    continue
                
                # For each decryption, try all alphabets and all shifts
                for alpha_id, alphabet in ALPHABETS.items():
                    for key in range(1, len(alphabet)):
                        dt = caesar_decrypt(candidate_text, key, alphabet)
                        score = score_text(dt)
                        if score >= 3:
                            print(f"\n[!!!] MATCH FOUND!")
                            print(f"Cipher: {cipher}, KDF: {kdf}")
                            print(f"Alphabet: {alpha_id}, Shift: {key}")
                            print(f"Decrypted: {dt}")
                            return True
    return False

if __name__ == "__main__":
    if not solve():
        print("Final attempt for 4072023370 failed.")
