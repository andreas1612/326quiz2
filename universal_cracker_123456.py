import subprocess

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
                'magic','decrypt','submit','found','your','use','flag']

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

pwd = "4072023370"
in_file = "problem_file.enc"

# Try different OpenSSL settings
# 123456 is an older quiz, so maybe no pbkdf2 and md5/sha1
for cipher in ["-aes-256-cbc", "-aes-128-cbc", "-des-ede3-cbc"]:
    for kdf in [["-md", "md5"], ["-md", "sha1"], ["-md", "sha256"], ["-pbkdf2"], []]:
        cmd = ["openssl", "enc", "-d", cipher] + kdf + ["-pass", f"pass:{pwd}", "-in", in_file]
        r = subprocess.run(cmd, capture_output=True)
        if r.returncode == 0:
            decrypted_bytes = r.stdout
            text = decrypted_bytes.decode('utf-8', errors='replace')
            
            for aid, alpha in ALPHABETS.items():
                for shift in range(1, len(alpha)):
                    dt = caesar_decrypt(text, shift, alpha)
                    if score_text(dt) >= 3:
                        print(f"SUCCESS! Settings: {cipher} {kdf}")
                        print(f"Alphabet: {aid}, Shift: {shift}")
                        print(f"Result: {dt}")
                        exit(0)
print("No luck.")
