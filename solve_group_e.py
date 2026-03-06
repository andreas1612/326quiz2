import os
import sys
import hashlib
import subprocess
import glob
import re

ID = "1366653"

# 1. Caesar / Vigenere Decryptor (from telos)
def score_text(text):
    COMMON_WORDS = ['the','and','you','are','for','key','aes','secret','token',
                    'stop','congratulations','solution','passphrase','reveal',
                    'magic','decrypt','submit','found','your','use','flag',
                    'this','have','with','that','from','they','will','been']
    t = text.lower()
    return sum(1 for w in COMMON_WORDS if w in t)

def caesar_decrypt(text, key, alphabet='abcdefghijklmnopqrstuvwxyz '):
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

def crack_details(filepath):
    print(f"\n[1] Attempting to crack {filepath}...")
    with open(filepath, 'r') as f:
        ciphertext = f.read().strip()
    
    alphabets = [
        'abcdefghijklmnopqrstuvwxyz',
        'abcdefghijklmnopqrstuvwxyz ',
        ' abcdefghijklmnopqrstuvwxyz',
        'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 -,.',
    ]
    best_score = 0
    best_dec = ""
    
    for alpha in alphabets:
        for key in range(1, len(alpha)):
            dec = caesar_decrypt(ciphertext, key, alpha)
            sc = score_text(dec)
            if sc > best_score:
                best_score = sc
                best_dec = dec
                
    if best_score > 2:
        print(f"  ✓ Decrypted details: {best_dec[:150]}...")
        # Try finding Token 1 (11 chars)
        words = best_dec.split()
        for w in words:
            clean = re.sub(r'[^a-zA-Z0-9]', '', w)
            if len(clean) == 11 and clean.lower() not in ['congratulations', 'passphrase']:
                print(f"  ★ Possible Token 1 (11 chars): {clean}")
        return best_dec
    return None

def crack_passphrase(filepath, student_id):
    print(f"\n[2] Cracking passphrase from {filepath}...")
    with open(filepath, 'r') as f:
        target_hash = f.read().strip()
        
    hash_type = 'sha512' if len(target_hash) == 128 else 'sha256'
    h_func = hashlib.sha512 if hash_type == 'sha512' else hashlib.sha256
    
    for digits in range(10000):
        for fmt in [f"{digits:02d}", f"{digits:03d}", f"{digits:04d}"]:
            for p in [f"{fmt}{student_id}", f"{student_id}{fmt}"]:
                for candidate in [p, p+'\n']:
                    if h_func(candidate.encode('utf-8')).hexdigest() == target_hash:
                        print(f"  ✓ Found Passphrase: {p}")
                        if len(p) == 10: print(f"  ★ Possible Token 2 (10 chars): {p}")
                        if len(p) == 9 and p.isdigit(): print(f"  ★ Possible Token 3 (9 digits): {p}")
                        return p
    print("  ✗ Failed to crack passphrase.")
    return None

def unzip_aes_key(zip_path, passphrase):
    print(f"\n[3] Unzipping {zip_path} with passphrase...")
    os.makedirs('/tmp/aes_extract', exist_ok=True)
    r = subprocess.run(['unzip', '-o', '-P', passphrase, zip_path, '-d', '/tmp/aes_extract/'], capture_output=True)
    if r.returncode == 0:
        files = glob.glob('/tmp/aes_extract/*')
        if files:
            aes_key = open(files[0], 'rb').read().strip().decode('utf-8', errors='replace')
            print(f"  ✓ Extracted AES key: {aes_key}")
            if len(aes_key) == 10: print(f"  ★ Possible Token 2 (10 chars): {aes_key}")
            if len(aes_key) == 9 and 'aes' not in aes_key.lower(): print(f"  ★ Possible Token 3 (9 digits): {aes_key}")
            return files[0], aes_key
    print(f"  ✗ Failed to unzip. Error: {r.stderr.decode()[:100]}")
    return None, None

def decrypt_private_key(enc_priv_path, passphrase, aes_key):
    print(f"\n[4] Decrypting {enc_priv_path}...")
    out_path = '/tmp/private_dec.pem'
    
    # Try multiple openssl commands. Private key might be encrypted with AES or just the passphrase.
    passwords = [passphrase, aes_key]
    for pwd in passwords:
        if not pwd: continue
        for cmd in [
            ['openssl', 'rsa', '-in', enc_priv_path, '-out', out_path, '-passin', f'pass:{pwd}'],
            ['openssl', 'enc', '-d', '-aes-256-cbc', '-pbkdf2', '-pass', f'pass:{pwd}', '-in', enc_priv_path, '-out', out_path],
            ['openssl', 'enc', '-d', '-aes-128-cbc', '-pbkdf2', '-pass', f'pass:{pwd}', '-in', enc_priv_path, '-out', out_path],
        ]:
            r = subprocess.run(cmd, capture_output=True)
            if r.returncode == 0 and os.path.exists(out_path):
                if b'PRIVATE KEY' in open(out_path, 'rb').read():
                    print(f"  ✓ Successfully decrypted private key using password: {pwd}")
                    return out_path
    print("  ✗ Failed to decrypt private key.")
    return None

def decrypt_rc4_key(rc4_enc_path, priv_key_path):
    print(f"\n[5] Decrypting {rc4_enc_path} with RSA private key...")
    out_path = '/tmp/rc4_key.bin'
    for cmd in [
        ['openssl', 'pkeyutl', '-decrypt', '-inkey', priv_key_path, '-in', rc4_enc_path, '-out', out_path],
        ['openssl', 'rsautl', '-decrypt', '-inkey', priv_key_path, '-in', rc4_enc_path, '-out', out_path],
    ]:
        r = subprocess.run(cmd, capture_output=True)
        if r.returncode == 0:
            data = open(out_path, 'rb').read()
            rc4_txt = data.decode('utf-8', errors='replace').strip()
            print(f"  ✓ Decrypted RC4 key: {rc4_txt}")
            if len(rc4_txt) == 10: print(f"  ★ Possible Token 2 or 4 (10 chars): {rc4_txt}")
            if len(rc4_txt) == 9 and rc4_txt.isdigit(): print(f"  ★ Possible Token 3 (9 digits): {rc4_txt}")
            return rc4_txt
    print("  ✗ Failed to decrypt RC4 key.")
    return None

def decrypt_problem(problem_path, rc4_key, aes_key, passphrase):
    print(f"\n[6] Decrypting {problem_path}...")
    out_path = '/tmp/problem_dec.txt'
    
    # It could be encrypted via RC4 or AES. Let's try RC4 first since the key is named RC4_key.enc 
    if rc4_key:
        print("  -> Trying RC4 decryption...")
        r = subprocess.run(['openssl', 'enc', '-d', '-rc4', '-pass', f'pass:{rc4_key}', '-in', problem_path, '-out', out_path], capture_output=True)
        if r.returncode == 0 and os.path.exists(out_path):
            data = open(out_path, 'r', errors='replace').read()
            if len(data) > 5:
                print(f"  ✓ RC4 Decryption successful! First 50 chars: {data[:50]}")
                return data

    if aes_key:
        print("  -> Trying AES decryption...")
        for cipher in ['-aes-256-cbc', '-aes-128-cbc', '-aes-256-ecb']:
            for kdf in [['-pbkdf2'], ['-md', 'md5'], []]:
                r = subprocess.run(['openssl', 'enc', '-d', cipher] + kdf + ['-pass', f'pass:{aes_key}', '-in', problem_path, '-out', out_path], capture_output=True)
                if r.returncode == 0 and os.path.exists(out_path):
                    data = open(out_path, 'r', errors='replace').read()
                    if len(data) > 5 and score_text(data) > 0:
                        print(f"  ✓ AES Decryption successful! First 50 chars: {data[:50]}")
                        return data
                        
    print("  ✗ Failed to decrypt problem_file.enc")
    return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 solve_group_e.py <folder_path>")
        sys.exit(1)
        
    folder = sys.argv[1].rstrip('/')
    
    # Locate files
    files = {
        'details': os.path.join(folder, 'details.txt'),
        'hash': os.path.join(folder, 'hash.txt'),
        'aes_zip': glob.glob(os.path.join(folder, '*aes*.zip')),
        'priv_enc': os.path.join(folder, 'private key.enc') if os.path.exists(os.path.join(folder, 'private key.enc')) else glob.glob(os.path.join(folder, '*private*.enc')),
        'rc4_enc': glob.glob(os.path.join(folder, '*RC4*.enc')) + glob.glob(os.path.join(folder, '*rc4*.enc')),
        'problem': os.path.join(folder, 'problem_file.enc')
    }
    
    # 1. Crack Details
    if os.path.exists(files['details']):
        crack_details(files['details'])
        
    # 2. Crack Hash -> Passphrase
    passphrase = None
    if os.path.exists(files['hash']):
        passphrase = crack_passphrase(files['hash'], ID)
        
    # 3. Unzip AES
    aes_key = None
    if files['aes_zip'] and passphrase:
        _, aes_key = unzip_aes_key(files['aes_zip'][0], passphrase)
        
    # 4. Decrypt Private Key
    priv_key_path = None
    priv_enc_file = files['priv_enc'][0] if isinstance(files['priv_enc'], list) and files['priv_enc'] else files['priv_enc']
    if priv_enc_file and os.path.exists(priv_enc_file) and (passphrase or aes_key):
        priv_key_path = decrypt_private_key(priv_enc_file, passphrase, aes_key)
        
    # 5. Decrypt RC4 Key
    rc4_key = None
    rc4_enc_file = files['rc4_enc'][0] if files['rc4_enc'] else None
    if rc4_enc_file and os.path.exists(rc4_enc_file) and priv_key_path:
        rc4_key = decrypt_rc4_key(rc4_enc_file, priv_key_path)
        
    # 6. Decrypt Problem
    if os.path.exists(files['problem']):
        final_text = decrypt_problem(files['problem'], rc4_key, aes_key, passphrase)
        if final_text:
            print("\n================== FINAL PROBLEM FILE TEXT ==================")
            print(final_text[:500])
            print("=============================================================")
            # Look for tokens in final text
            words = final_text.split()
            for w in words:
                clean = re.sub(r'[^a-zA-Z0-9]', '', w)
                if len(clean) == 10: print(f"  ★ Possible Token 4 (10 chars): {clean}")

if __name__ == '__main__':
    main()
