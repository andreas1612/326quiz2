import string

def caesar_decrypt(text, key, alpha):
    res = ""
    for c in text:
        if c in alpha:
            idx = (alpha.index(c) - key) % len(alpha)
            res += alpha[idx]
        else:
            res += c
    return res

ALPHABETS = {
    '1':  'abcdefghijklmnopqrstuvwxyz',
    '2':  'abcdefghijklmnopqrstuvwxyz ',
    '3':  ' abcdefghijklmnopqrstuvwxyz',
    '20': '0123456789,. abcdefghijklmnopqrstuvwxyz',
}

with open("details_file.txt", "r") as f:
    ct = f.read().strip()

best_score = 0
best_text = ""

common_words = ["passphrase", "symmetric", "decrypt", "id", "digits", "stop"]

for name, alpha in ALPHABETS.items():
    for shift in range(len(alpha)):
        dt = caesar_decrypt(ct, shift, alpha)
        score = sum(1 for word in common_words if word in dt.lower())
        if score > best_score:
            best_score = score
            best_text = dt

print(f"Decrypted Details: {best_text}")
