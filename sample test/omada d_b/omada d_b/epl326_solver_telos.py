#!/usr/bin/env python3
"""
EPL326 Universal Solver
Quiz 1 (cipher): python3 epl326_solver.py cipher "CIPHERTEXT"
Quiz 2 (puzzle): python3 epl326_solver.py puzzle <ID> <FOLDER>
"""

import sys, os, hashlib, subprocess, itertools, shutil, math
from collections import Counter

# ══════════════════════════════════════════════════════════════
# ALPHABETS
# ══════════════════════════════════════════════════════════════
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

# ══════════════════════════════════════════════════════════════
# SCORING
# ══════════════════════════════════════════════════════════════
def score_text(text):
    t = text.lower()
    return sum(1 for w in COMMON_WORDS if w in t)

def detect_alphabet(ciphertext):
    chars = set(ciphertext)
    best = '1'
    best_coverage = 0
    for k, alpha in ALPHABETS.items():
        alpha_set = set(alpha)
        coverage = len(chars & alpha_set) / max(len(chars), 1)
        if coverage > best_coverage:
            best_coverage = coverage
            best = k
    return best

# ══════════════════════════════════════════════════════════════
# CAESAR
# ══════════════════════════════════════════════════════════════
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

def crack_caesar_all_alphabets(ciphertext):
    results = []
    for alpha_id, alphabet in ALPHABETS.items():
        for key in range(1, len(alphabet)):
            dec = caesar_decrypt(ciphertext, key, alphabet)
            s = score_text(dec)
            if s > 0:
                results.append((s, f"Caesar key={key} alpha={alpha_id}", dec))
    results.sort(reverse=True)
    return results[:10]

# ══════════════════════════════════════════════════════════════
# TRANSPOSITION
# ══════════════════════════════════════════════════════════════
def transposition_decrypt(text, key):
    columns = int(math.ceil(len(text) / float(key)))
    rows = key
    padding = (columns * rows) - len(text)
    plain = [''] * columns
    column = row = 0
    for symbol in text:
        plain[column] += symbol
        column += 1
        if (column == columns) or (column == columns - 1 and row >= rows - padding):
            column = 0
            row += 1
    return ''.join(plain)

def crack_transposition(ciphertext):
    results = []
    for key in range(2, min(len(ciphertext), 60)):
        dec = transposition_decrypt(ciphertext, key)
        s = score_text(dec)
        if s > 0:
            results.append((s, f"Transposition key={key}", dec))
    results.sort(reverse=True)
    return results[:5]

# ══════════════════════════════════════════════════════════════
# VIGENERE
# ══════════════════════════════════════════════════════════════
def vigenere_decrypt(ct, key, alphabet='abcdefghijklmnopqrstuvwxyz'):
    alpha = list(alphabet)
    result, ki = [], 0
    for c in ct:
        if c.lower() in alpha:
            shift = alpha.index(key[ki % len(key)])
            result.append(alpha[(alpha.index(c.lower()) - shift) % len(alpha)])
            ki += 1
        else:
            result.append(c)
    return ''.join(result)

def crack_vigenere(ct, keylen=3):
    best_score, best_key, best_dec = 0, '', ct
    for combo in itertools.product(range(26), repeat=keylen):
        key = ''.join(chr(k+97) for k in combo)
        dec = vigenere_decrypt(ct, key)
        s = score_text(dec)
        if s > best_score:
            best_score, best_key, best_dec = s, key, dec
    return best_key, best_dec, best_score

# ══════════════════════════════════════════════════════════════
# COMBINED: Caesar→Transposition & Transposition→Caesar
# ══════════════════════════════════════════════════════════════
def crack_combined(ciphertext):
    results = []
    alphabet = ALPHABETS['1']  # use basic first
    for caesar_key in range(1, 27):
        after_c = caesar_decrypt(ciphertext, caesar_key, alphabet)
        for trans_key in range(2, min(len(ciphertext), 30)):
            dec = transposition_decrypt(after_c, trans_key)
            s = score_text(dec)
            if s >= 2:
                results.append((s, f"Caesar({caesar_key})→Trans({trans_key})", dec))
    for trans_key in range(2, min(len(ciphertext), 30)):
        after_t = transposition_decrypt(ciphertext, trans_key)
        for caesar_key in range(1, 27):
            dec = caesar_decrypt(after_t, caesar_key, alphabet)
            s = score_text(dec)
            if s >= 2:
                results.append((s, f"Trans({trans_key})→Caesar({caesar_key})", dec))
    results.sort(reverse=True)
    return results[:5]

# ══════════════════════════════════════════════════════════════
# REVERSED + CAESAR
# ══════════════════════════════════════════════════════════════
def crack_reversed_caesar(ciphertext):
    results = []
    reversed_ct = ciphertext[::-1]
    for alpha_id, alphabet in ALPHABETS.items():
        for key in range(1, len(alphabet)):
            dec = caesar_decrypt(reversed_ct, key, alphabet)
            s = score_text(dec)
            if s >= 2:
                results.append((s, f"Reversed+Caesar key={key} alpha={alpha_id}", dec))
    results.sort(reverse=True)
    return results[:5]

# ══════════════════════════════════════════════════════════════
# QUIZ 1: AUTO CRACK CIPHERTEXT
# ══════════════════════════════════════════════════════════════
def solve_cipher(ciphertext):
    print(f"\n{'='*55}")
    print(f"  QUIZ 1 - Cipher Solver")
    print(f"  Ciphertext: {ciphertext[:60]}...")
    print(f"{'='*55}")

    all_results = []

    print("\n[1] Caesar (all alphabets)...")
    r = crack_caesar_all_alphabets(ciphertext)
    all_results += r
    if r: print(f"  Best: {r[0]}")

    print("[2] Transposition...")
    r = crack_transposition(ciphertext)
    all_results += r
    if r: print(f"  Best: {r[0]}")

    print("[3] Vigenere (keylen 1-3, basic alphabet)...")
    for kl in [1, 2, 3]:
        key, dec, score = crack_vigenere(ciphertext, keylen=kl)
        if score > 0:
            all_results.append((score, f"Vigenere keylen={kl} key={key}", dec))
    
    print("[4] Combined Caesar+Transposition...")
    r = crack_combined(ciphertext)
    all_results += r
    if r: print(f"  Best: {r[0]}")

    print("[5] Reversed+Caesar...")
    r = crack_reversed_caesar(ciphertext)
    all_results += r
    if r: print(f"  Best: {r[0]}")

    all_results.sort(reverse=True)

    print(f"\n{'='*55}")
    print("  TOP RESULTS")
    print(f"{'='*55}")
    for score, method, dec in all_results[:10]:
        print(f"\n► Score={score} | {method}")
        print(f"  {dec[:100]}")

# ══════════════════════════════════════════════════════════════
# QUIZ 2: PASSPHRASE CRACK
# ══════════════════════════════════════════════════════════════
def crack_passphrase(student_id, hash_val):
    hash_type = 'sha512' if len(hash_val) == 128 else 'sha256'
    h = hashlib.sha512 if hash_type == 'sha512' else hashlib.sha256
    print(f"\n[1] Cracking passphrase ({hash_type})...")
    for digits in range(10000):
        for fmt in [f"{digits:02d}", f"{digits:03d}", f"{digits:04d}"]:
            for p in [f"{fmt}{student_id}", f"{student_id}{fmt}"]:
                for candidate in [p, p+'\n']:
                    if h(candidate.encode()).hexdigest() == hash_val:
                        print(f"  ✓ Passphrase: {p}")
                        return p
    print("  ✗ Not found"); return None

# ══════════════════════════════════════════════════════════════
# QUIZ 2: EXTRACT AES KEY FROM ZIP
# ══════════════════════════════════════════════════════════════
def extract_aes_from_zip(folder, files, passphrase):
    """Unzip aes_protected.zip with passphrase → get AES key file"""
    for f in files:
        if 'zip' in f.lower() and ('aes' in f.lower() or 'protected' in f.lower()):
            path = os.path.join(folder, f)
            print(f"\n[1b] Extracting AES key from zip: {f}...")
            r = subprocess.run(['unzip','-P',passphrase,'-o',path,'-d',folder], capture_output=True)
            if r.returncode == 0:
                # Refresh files list and find aes key
                new_files = os.listdir(folder)
                for nf in new_files:
                    if 'aes' in nf.lower() and 'zip' not in nf.lower() and '.enc' not in nf.lower():
                        aes_path = os.path.join(folder, nf)
                        aes_key = open(aes_path,'rb').read().strip().decode('utf-8', errors='ignore').strip()
                        print(f"  ✓ AES key from zip: {aes_key}")
                        return aes_key, aes_path
    return None, None

# ══════════════════════════════════════════════════════════════
# QUIZ 2: DECRYPT PRIVATE KEY
# ══════════════════════════════════════════════════════════════
def decrypt_private_key(folder, files, passphrase, aes_key=None):
    out = '/tmp/private_dec.pem'
    print(f"\n[2] Decrypting RSA private key...")
    for f in files:
        if 'private' in f.lower() and '.dec' in f.lower():
            path = os.path.join(folder, f)
            if b'PRIVATE' in open(path,'rb').read():
                shutil.copy(path, out)
                print(f"  ✓ Found unencrypted key: {f}")
                return out
    for f in files:
        if 'private' in f.lower():
            path = os.path.join(folder, f)
            passwords = [passphrase]
            if aes_key:
                passwords.insert(0, aes_key)
            for pwd in passwords:
                if not pwd: continue
                for cmd in [
                    ['openssl','rsa','-in',path,'-out',out,'-passin',f'pass:{pwd}'],
                    ['openssl','pkey','-in',path,'-out',out,'-passin',f'pass:{pwd}'],
                    ['openssl','enc','-d','-aes-256-cbc','-pbkdf2','-pass',f'pass:{pwd}','-in',path,'-out',out],
                    ['openssl','enc','-d','-aes-128-cbc','-pbkdf2','-pass',f'pass:{pwd}','-in',path,'-out',out],
                    ['openssl','enc','-d','-des-ede3-cbc','-pass',f'pass:{pwd}','-in',path,'-out',out],
                    ['openssl','enc','-d','-aes-256-cbc','-pass',f'pass:{pwd}','-in',path,'-out',out],
                ]:
                    r = subprocess.run(cmd, capture_output=True)
                    if r.returncode == 0 and os.path.exists(out):
                        if b'PRIVATE' in open(out,'rb').read():
                            print(f"  ✓ Decrypted: {f} (pwd={pwd})")
                            return out
    print("  ✗ Failed"); return None

# ══════════════════════════════════════════════════════════════
# QUIZ 2: DECRYPT AES KEY
# ══════════════════════════════════════════════════════════════
def decrypt_aes_key(aes_file, priv_key):
    out = '/tmp/aes.bin'
    print(f"\n[3] RSA-decrypting AES key...")
    for cmd in [
        ['openssl','pkeyutl','-decrypt','-inkey',priv_key,'-in',aes_file,'-out',out],
        ['openssl','rsautl','-decrypt','-inkey',priv_key,'-in',aes_file,'-out',out],
    ]:
        r = subprocess.run(cmd, capture_output=True)
        if r.returncode == 0:
            data = open(out,'rb').read()
            print(f"  ✓ AES key: {data[:40]}")
            return data, out
    print("  ✗ Failed"); return None, None

# ══════════════════════════════════════════════════════════════
# QUIZ 2: DECRYPT PROBLEM FILE
# ══════════════════════════════════════════════════════════════
def decrypt_problem(problem_file, priv_key, aes_key_bytes, aes_key_file, passphrase):
    out = '/tmp/problem_dec.txt'
    print(f"\n[4] Decrypting problem file...")
    attempts = []
    if aes_key_bytes:
        aes_key_str = aes_key_bytes.decode('utf-8', errors='replace').strip()
        for cipher in ['-aes-256-cbc','-aes-128-cbc','-aes-256-ecb','-aes-128-ecb']:
            for kdf in [['-pbkdf2'],['-md','md5'],['-md','sha256'],[]]:
                attempts.append(['openssl','enc','-d',cipher]+kdf+['-in',problem_file,'-out',out,'-pass',f'pass:{aes_key_str}'])
    if priv_key:
        attempts += [
            ['openssl','pkeyutl','-decrypt','-inkey',priv_key,'-in',problem_file,'-out',out],
            ['openssl','rsautl','-decrypt','-inkey',priv_key,'-in',problem_file,'-out',out],
        ]
    if aes_key_file:
        for cipher in ['-aes-256-cbc','-aes-128-cbc','-aes-256-ecb','-aes-128-ecb']:
            for kdf in [['-pbkdf2'],['-md','md5'],[]]:
                attempts.append(['openssl','enc','-d',cipher]+kdf+['-in',problem_file,'-out',out,'-pass',f'file:{aes_key_file}'])
    if passphrase:
        for cipher in ['-aes-256-cbc','-aes-128-cbc','-aes-256-ecb']:
            for kdf in [['-pbkdf2'],['-md','md5'],[]]:
                attempts.append(['openssl','enc','-d',cipher]+kdf+['-in',problem_file,'-out',out,'-pass',f'pass:{passphrase}'])
    for cmd in attempts:
        r = subprocess.run(cmd, capture_output=True)
        if r.returncode == 0 and os.path.exists(out):
            data = open(out,'rb').read()
            if data and len(data) > 10:
                print(f"  ✓ Decrypted: {data[:80]}")
                return data
    print("  ✗ Failed"); return None

# ══════════════════════════════════════════════════════════════
# QUIZ 2: MAIN PUZZLE SOLVER
# ══════════════════════════════════════════════════════════════
def solve_puzzle(student_id, folder):
    files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder,f))]

    print(f"\n{'='*55}")
    print(f"  EPL326 Puzzle Solver | ID: {student_id}")
    print(f"{'='*55}")
    print(f"Files: {files}")

    def find(*kws):
        for kw in kws:
            for f in files:
                if kw.lower() in f.lower():
                    return os.path.join(folder, f)
        return None

    details_file = find('details')
    hash_file    = find('hash')
    private_file = find('private')
    problem_file = find('problem')
    aes_file     = find('aes_key','encryptedkey','aes_protected')

    # Auto-detect Vigenere key length from details
    vigenere_keylen = 3
    word_to_num = {'one':1,'two':2,'three':3,'four':4,'five':5,'six':6,'seven':7,'eight':8,'nine':9,'ten':10}
    if details_file:
        import re
        details_text = open(details_file).read().strip()
        print(f"\nDetails: {details_text[:150]}")
        m = re.search(r"key.{1,10}length.{1,10}is.{1,5}(\w+)", details_text.lower())
        if m:
            word = m.group(1)
            vigenere_keylen = int(word) if word.isdigit() else word_to_num.get(word, 3)
        print(f"  → Vigenere key length: {vigenere_keylen}")

    tokens = {}

    hash_val = open(hash_file).read().strip() if hash_file else None
    passphrase = crack_passphrase(student_id, hash_val) if hash_val else None
    if passphrase: tokens['Token 1 (passphrase)'] = passphrase

    # Step 2a: If aes_protected.zip exists, unzip with passphrase to get AES key plaintext
    import glob, shutil
    aes_key_plain = None
    aes_key_plain_file = None
    zip_aes = find('aes_protected')
    if zip_aes and zip_aes.endswith('.zip') and passphrase:
        print(f"\n[2a] Unzipping AES protected zip with passphrase...")
        shutil.rmtree('/tmp/aes_unzip', ignore_errors=True)
        os.makedirs('/tmp/aes_unzip', exist_ok=True)
        r = subprocess.run(['unzip','-P',passphrase,zip_aes,'-d','/tmp/aes_unzip/'], capture_output=True)
        if r.returncode == 0:
            extracted = glob.glob('/tmp/aes_unzip/*')
            if extracted:
                aes_key_plain_file = extracted[0]
                aes_key_plain = open(aes_key_plain_file,'rb').read().strip().decode('utf-8', errors='replace')
                print(f"  ✓ AES key: {aes_key_plain}")
                tokens['Token 2 (AES key)'] = aes_key_plain
        else:
            print(f"  ✗ Unzip failed: {r.stderr.decode()[:100]}")

    # Step 2b: If private.pem.zip exists, unzip with passphrase
    zip_priv = find('private.pem.zip', 'private_pem.zip')
    if zip_priv and zip_priv.endswith('.zip') and passphrase:
        print(f"\n[2b] Unzipping private key zip with passphrase...")
        shutil.rmtree('/tmp/priv_unzip', ignore_errors=True)
        os.makedirs('/tmp/priv_unzip', exist_ok=True)
        r = subprocess.run(['unzip','-P',passphrase,zip_priv,'-d','/tmp/priv_unzip/'], capture_output=True)
        if r.returncode == 0:
            extracted = glob.glob('/tmp/priv_unzip/*')
            for f in extracted:
                if b'PRIVATE' in open(f,'rb').read():
                    shutil.copy(f, '/tmp/private_dec.pem')
                    print(f"  ✓ Extracted private key: {os.path.basename(f)}")
                    break
        else:
            print(f"  ✗ Unzip failed: {r.stderr.decode()[:100]}")

    # Step 2c: Decrypt private key - check if already extracted from zip
    if os.path.exists('/tmp/private_dec.pem') and b'PRIVATE' in open('/tmp/private_dec.pem','rb').read():
        priv_key = '/tmp/private_dec.pem'
        print(f"\n[2] Using extracted private key from zip")
    else:
        priv_key = decrypt_private_key(folder, files, passphrase, aes_key=aes_key_plain) if passphrase else None

    # Save private key content for Token 3
    if priv_key and os.path.exists(priv_key):
        priv_content = open(priv_key).read().strip()
        tokens['Token 3 (private key - 1674 chars)'] = priv_content

    # Step 3: Get AES key bytes
    aes_key_bytes, aes_key_file = None, None
    if aes_key_plain:
        aes_key_bytes = aes_key_plain.encode()
        # Write AES key to temp file for openssl -pass file: usage
        aes_key_file = '/tmp/aes_key_plain.txt'
        open(aes_key_file, 'w').write(aes_key_plain)
        tokens['Token 2 (AES key)'] = aes_key_plain
    elif aes_file and priv_key:
        aes_key_data, aes_key_file_raw = decrypt_aes_key(aes_file, priv_key)
        if aes_key_data:
            aes_key_plain = aes_key_data.decode('utf-8', errors='replace').strip()
            aes_key_bytes = aes_key_data
            # Write to temp file
            aes_key_file = '/tmp/aes_key_plain.txt'
            open(aes_key_file, 'w').write(aes_key_plain)
            tokens['Token 2 (AES key)'] = aes_key_plain
            print(f"  ✓ AES key (RSA decrypted): {aes_key_plain}")

    problem_dec = None
    if problem_file:
        problem_dec = decrypt_problem(problem_file, priv_key, aes_key_bytes, aes_key_file, passphrase)

    if problem_dec:
        text = problem_dec.decode('utf-8', errors='replace').strip()
        tokens['Raw decrypted'] = text
        if score_text(text) < 3:
            print(f"\n[5] Cracking Vigenere (keylen={vigenere_keylen})...")
            key, dec, sc = crack_vigenere(text, keylen=vigenere_keylen)
            tokens['FINAL plaintext'] = dec
            # Check if Caesar - if all key chars same, it's Caesar, report shift value
            if len(set(key)) == 1:
                shift_val = ord(key[0]) - ord('a')
                tokens['Token 4 (shift/key)'] = str(shift_val)
            else:
                tokens['Token 4 (Vigenere key)'] = key
            # Extract base64 token from final plaintext
            import re
            b64_match = re.search(r'[a-z0-9+/]{20,}={0,2}', dec)
            tokens['Token 5 (base64)'] = b64_match.group(0) if b64_match else ''
            print(f"  ✓ Key='{key}' score={sc}: {dec[:100]}")
        else:
            tokens['FINAL plaintext'] = text

    print(f"\n{'='*55}")
    print("  TOKENS TO SUBMIT")
    print(f"{'='*55}")
    for k, v in tokens.items():
        if 'private key' in k.lower():
            print(f"\n► {k}:\n{str(v)}")
        else:
            print(f"\n► {k}:\n  {str(v)[:400]}")
    print(f"\n{'='*55}")

# ══════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════
def main():
    if len(sys.argv) < 2:
        print("Quiz 1: python3 epl326_solver.py cipher \"CIPHERTEXT\"")
        print("Quiz 2: python3 epl326_solver.py puzzle <ID> <FOLDER>")
        sys.exit(1)

    mode = sys.argv[1].lower()

    if mode == 'cipher':
        if len(sys.argv) < 3:
            print("Usage: python3 epl326_solver.py cipher \"CIPHERTEXT\"")
            sys.exit(1)
        solve_cipher(sys.argv[2])

    elif mode == 'puzzle':
        if len(sys.argv) < 4:
            print("Usage: python3 epl326_solver.py puzzle <ID> <FOLDER>")
            sys.exit(1)
        solve_puzzle(sys.argv[2], sys.argv[3].rstrip('/'))

    else:
        print(f"Unknown mode '{mode}'. Use 'cipher' or 'puzzle'.")

if __name__ == '__main__':
    main()
