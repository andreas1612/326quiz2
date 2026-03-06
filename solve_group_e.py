import os
import sys
import hashlib
import subprocess
import glob
import re
import itertools
import math
import base64

# Default ID, will be overridden by folder name if possible
ID = "1366653" 

COMMON_WORDS = ['the','and','you','are','for','key','aes','secret','token',
                'stop','congratulations','solution','passphrase','reveal',
                'magic','decrypt','submit','found','your','use','flag',
                'this','successfully','solved','puzzle']

def score_text(text):
    if not text: return -100
    t = text.lower()
    # High weight for key words
    score = sum(10 for w in ['congratulations', 'successfully', 'solved', 'token is'] if w in t)
    score += sum(2 for w in COMMON_WORDS if w in t)
    return score

def vigenere_decrypt(ct, key):
    alpha = "abcdefghijklmnopqrstuvwxyz"
    res = []
    ki = 0
    k_ints = [alpha.index(k) for k in key]
    for c in ct:
        low = c.lower()
        if 'a' <= low <= 'z':
            shift = k_ints[ki % len(key)]
            new_char = chr((ord(low) - 97 - shift) % 26 + 97)
            res.append(new_char if c.islower() else new_char.upper())
            ki += 1
        else:
            res.append(c)
    return "".join(res)

def crack_cipher(text):
    print("\n[7] Attempting to crack final ciphertext...")
    if score_text(text) > 20:
        return text
        
    best_score, best_dec, best_method = score_text(text), text, "Raw"
    
    # Caesar is just Vigenere length 1
    alpha = "abcdefghijklmnopqrstuvwxyz"
    for kl in range(1, 4):
        print(f"  -> Testing Vigenere keylen {kl}...")
        for combo in itertools.product(alpha, repeat=kl):
            dec = vigenere_decrypt(text, combo)
            s = score_text(dec)
            if s > best_score:
                best_score, best_dec, best_method = s, dec, f"Vigenere(key={''.join(combo)})"
                if s > 30: # Early exit for clear matches
                    print(f"  ✓ High-confidence match! Method: {best_method}")
                    return best_dec
                    
    return best_dec

def crack_passphrase(filepath, student_id):
    if not filepath: return None
    print(f"\n[2] Cracking passphrase from {os.path.basename(filepath)}...")
    target_hash = open(filepath).read().strip()
    h_func = hashlib.sha512 if len(target_hash) == 128 else hashlib.sha256
    for digits in range(10000):
        for fmt in [f"{digits:02d}", f"{digits:03d}", f"{digits:04d}"]:
            for p in [f"{fmt}{student_id}", f"{student_id}{fmt}"]:
                if h_func(p.encode()).hexdigest() == target_hash:
                    print(f"  ✓ Found Passphrase: {p}")
                    return p
    return None

def get_aes_key(folder, passphrase):
    print("\n[3] Retrieving AES key...")
    # ZIP check
    zip_f = glob.glob(os.path.join(folder, "*aes*.zip")) + glob.glob(os.path.join(folder, "*protected*.zip"))
    if zip_f and passphrase:
        out = '/tmp/quiz_aes'
        os.makedirs(out, exist_ok=True)
        if subprocess.run(['unzip', '-o', '-P', passphrase, zip_f[0], '-d', out], capture_output=True).returncode == 0:
            extracted = glob.glob(os.path.join(out, "*"))
            if extracted:
                key = open(extracted[0], 'rb').read().decode(errors='replace').strip()
                print(f"  ✓ AES key from ZIP: {key}")
                return key
    # ENC check
    enc_f = glob.glob(os.path.join(folder, "*AES_key.enc"))
    if enc_f and passphrase:
        out = '/tmp/aes_key.txt'
        for opts in [['-provider','legacy','-provider','default','-nosalt'], ['-nosalt']]:
            cmd = ['openssl', 'enc', '-d', '-rc4'] + opts + ['-pass', f'pass:{passphrase}', '-in', enc_f[0], '-out', out]
            if subprocess.run(cmd, capture_output=True).returncode == 0:
                key = open(out, errors='replace').read().strip()
                if key:
                    print(f"  ✓ AES key from ENC: {key}")
                    return key
    return None

def decrypt_private_key(folder, passphrase, aes_key):
    print("\n[4] Decrypting private key...")
    enc_f = glob.glob(os.path.join(folder, "*private*.enc"))
    if not enc_f: return None
    out = '/tmp/private_dec.pem'
    for pwd in [aes_key, passphrase]:
        if not pwd: continue
        for cmd in [
            ['openssl', 'rsa', '-in', enc_f[0], '-out', out, '-passin', f'pass:{pwd}'],
            ['openssl', 'enc', '-d', '-aes-256-cbc', '-pbkdf2', '-pass', f'pass:{pwd}', '-in', enc_f[0], '-out', out],
        ]:
            if subprocess.run(cmd, capture_output=True).returncode == 0:
                if os.path.exists(out) and b'PRIVATE' in open(out, 'rb').read():
                    print(f"  ✓ Success! (pwd={pwd})")
                    return out
    return None

def decrypt_problem(problem_path, priv_key, aes_key, rc4_key):
    print(f"\n[6] Decrypting problem file...")
    out = '/tmp/prob_dec.txt'
    results = []
    
    # 1. Try Symmetric (RC4 / AES)
    for k in [x for x in [rc4_key, aes_key] if x]:
        # Try RC4
        for opts in [['-provider','legacy','-provider','default','-nosalt'], ['-nosalt'], []]:
            if subprocess.run(['openssl', 'enc', '-d', '-rc4'] + opts + ['-pass', f'pass:{k}', '-in', problem_path, '-out', out], capture_output=True).returncode == 0:
                try:
                    data = open(out, 'r', errors='replace').read().strip()
                    if len(data) > 5:
                        results.append((score_text(data), "RC4", data))
                except: pass
        # Try AES
        for cipher in ['-aes-256-cbc', '-aes-128-cbc']:
            for kdf in [['-pbkdf2'], ['-md', 'md5'], []]:
                if subprocess.run(['openssl', 'enc', '-d', cipher] + kdf + ['-pass', f'pass:{k}', '-in', problem_path, '-out', out], capture_output=True).returncode == 0:
                    try:
                        data = open(out, 'r', errors='replace').read().strip()
                        if len(data) > 5:
                            results.append((score_text(data), "AES", data))
                    except: pass

    # 2. Try RSA Asymmetric
    if priv_key and os.path.getsize(problem_path) <= 512:
        for cmd in [['openssl', 'pkeyutl', '-decrypt', '-inkey', priv_key], ['openssl', 'rsautl', '-decrypt', '-inkey', priv_key]]:
            if subprocess.run(cmd + ['-in', problem_path, '-out', out], capture_output=True).returncode == 0:
                try:
                    data = open(out, 'r', errors='replace').read().strip()
                    if data:
                        results.append((score_text(data), "RSA", data))
                except: pass
    
    if not results: return None
    
    # Sort by score. If scores are tied at 0, prioritize RSA for small files (~256 bytes) and RC4 for others.
    results.sort(key=lambda x: x[0], reverse=True)
    if results[0][0] == 0:
        # Tie-breaker
        fsize = os.path.getsize(problem_path)
        for score, method, data in results:
            if fsize == 256 and method == "RSA":
                print(f"  ✓ Selected {method} decryption (Tie-breaker for RSA size)")
                return data
            if fsize != 256 and method == "RC4":
                print(f"  ✓ Selected {method} decryption (Tie-breaker for Symmetric size)")
                return data
                
    best_score, best_method, best_data = results[0]
    print(f"  ✓ Selected {best_method} decryption (score={best_score})")
    return best_data

def main():
    if len(sys.argv) < 2: return
    folder = sys.argv[1].rstrip('/')
    sid = os.path.basename(folder) if os.path.basename(folder).isdigit() else ID
    
    hash_f = glob.glob(os.path.join(folder, "*hash.txt"))[0] if glob.glob(os.path.join(folder, "*hash.txt")) else None
    passphrase = crack_passphrase(hash_f, sid)
    aes_key = get_aes_key(folder, passphrase)
    priv_key = decrypt_private_key(folder, passphrase, aes_key)
    
    rc4_key = None
    rc4_enc = glob.glob(os.path.join(folder, "*RC4*.enc"))
    if rc4_enc and priv_key:
        out_rc4 = '/tmp/rc4.bin'
        if subprocess.run(['openssl', 'pkeyutl', '-decrypt', '-inkey', priv_key, '-in', rc4_enc[0], '-out', out_rc4], capture_output=True).returncode == 0:
            rc4_key = open(out_rc4, 'rb').read().decode(errors='replace').strip()
            print(f"  ✓ Decrypted RC4 key: {rc4_key}")

    prob_f = glob.glob(os.path.join(folder, "*problem*.enc"))[0] if glob.glob(os.path.join(folder, "*problem*.enc")) else None
    if prob_f:
        raw = decrypt_problem(prob_f, priv_key, aes_key, rc4_key)
        if raw:
            final = crack_cipher(raw)
            print("\n" + "="*50 + "\nFINAL TEXT:\n" + final + "\n" + "="*50)
            words = final.split()
            print(f"\n★ KEY TOKENS:\n  1: {passphrase}\n  2: {aes_key}\n  3: {rc4_key}\n  4: {re.sub(r'[^a-zA-Z0-9]', '', words[-1]) if words else ''}")

if __name__ == "__main__":
    main()
