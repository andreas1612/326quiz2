# 326quiz2

This repository contains the complete toolkit and exact commands we used to crack the previous EPL326 cryptography quizzes. If you're using this for a future quiz, read through carefully to understand the systematic process. 

## Structure

- `epl326_solver_telos.py`: The universal solver script handling Vigenere cracking, AES decryption, and RSA logic.
- `solve_step2.py` / `solve_step*.py`: Breakdown scripts for individual steps (cracking the passphrase, unzipping the key, etc.)
- `crypto_helper.py`: A utility script testing `openssl enc` and hashing commands iteratively.
- `/123456/`: Contains sample tokens, cracked hashes, and keys from past attempts as examples.

## How Past Quizzes Were Cracked
Most quizzes followed a multi-stage lock structure where unlocking one level gives you the key to the next.

### Step 1: Cracking the Passphrase (Token 1 & 2)
You usually start with your student ID (e.g., `123456`) and a hash file (`hash.txt`).
1. **Goal**: Crack the passphrase which is an SHA256 or SHA512 hash of your ID plus 2 or 3 digits (e.g., `01123456` or `12345699`).
2. **Command**: We wrote Python scripts (`solve_step2.py`) looping through all 2 and 3 digit combinations concatenated to the ID until the hash matched.
3. **Usage**: The found passphrase could be directly the token, or it's used to unlock the `aes_protected.zip` guarding Token 2.

### Step 2: Unlocking the Private Key (Token 3)
1. You might find a `private.pem.zip` or a password-protected RSA file (`private.pem.enc`).
2. **Command**:
   - For a zip: `unzip -P <cracked_passphrase> private.pem.zip`
   - For an encrypted key format:
     ```bash
     openssl rsa -in private.pem.enc -out private_dec.pem -passin pass:<passphrase>
     ```
3. Once decrypted, you will be able to read the plain `-----BEGIN RSA PRIVATE KEY-----`.

### Step 3: Decrypting the AES Key
Sometimes, the AES symmetric key is RSA-encrypted in a file (like `encryptedKeyAES.txt`).
1. **Command**: Use the decrypted private key to decrypt the AES key:
   ```bash
   openssl pkeyutl -decrypt -inkey private_dec.pem -in encryptedKeyAES.txt -out aes.bin
   ```
   Or `rsautl` for older OpenSSL:
   ```bash
   openssl rsautl -decrypt -inkey private_dec.pem -in encryptedKeyAES.txt -out aes.bin
   ```

### Step 4: Decrypting the Problem File (Token 4 & 5)
Now, you use the AES key to finally decrypt `problem_file.enc`.
1. **Command**:
   ```bash
   openssl enc -d -aes-256-cbc -pbkdf2 -in problem_file.enc -out decrypted_problem.txt -pass pass:<AES_KEY_STRING>
   ```
2. What comes out is usually a ciphertext encrypted with a **Caesar** or **Vigenère** cipher.
3. If they provide a `details_file.txt`, look for hints like "key length is three" or "shifted by 5". Look into `epl326_solver_telos.py` which automatically runs frequency analysis matching against a dictionary of english words (like "congratulations", "token", "the").
4. Once the final plaintext is revealed, Token 4 is the Vigenere key or Caesar shift, and Token 5 is usually a long **Base64** string at the end of the plaintext.

## Quick Automation Command
We merged all logic into `epl326_solver_telos.py`. During the quiz, you can usually just run:
```bash
# General Cipher Mode (if it's just raw ciphertext)
python3 epl326_solver_telos.py cipher "CIPHERTEXT"

# Full Puzzle Folder Mode
python3 epl326_solver_telos.py puzzle 123456 /path/to/extracted/quiz/folder
```

Good luck on the new quiz!
