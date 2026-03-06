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

## Group E Specifics (18:00 Exam)

The new Group E format introduces an `RC4_key.enc` file in the decryption chain, replacing the direct AES problem decryption with an intermediate step.

### Changes & Comparison:
1. **Passphrase**: Same (SHA-256 or SHA-512 Hash cracking).
2. **AES ZIP**: The `aes_key_protected.zip` is unlocked using the passphrase (Same).
3. **Private Key**: `private key.enc` is decrypted using the **Passphrase** or **AES Key** (new variation).
4. **RC4 Key (NEW)**: `RC4_key.enc` is decrypted via RSA using the unlocked private key.
5. **Problem Decryption**: `problem_file.enc` is decrypted using the **RC4 Key** (or sometimes AES key).
6. **Final Tokens**: 
   - Token 1 (11 chars) from `details.txt`
   - Token 2 (10 chars) from unzipping AES key or RC4 key
   - Token 3 (9 digits) from decrypting RC4 key or passphrase
   - Token 4 (10 chars) hidden in the final `problem_file.enc` plaintext

We have added a custom tailored script `solve_group_e.py` specifically for this exact structure to instantly solve it.

### Usage for Group E:
```bash
python3 solve_group_e.py /path/to/extracted/quiz/folder
```

### Update: Universal Solver (March 6, 2026)
The toolkit has been upgraded to handle both the **Standard Symmetric** and **New Asymmetric (RSA)** quiz variations automatically.

**Usage:**
```bash
python3 solve_group_e.py <folder_path>
```

**Key Features:**
- **Auto-Hashing**: Detects SHA-256 vs SHA-512 for passphrases.
- **Robust Key Chain**: Automatically handles encrypted ZIPs or `AES_key.enc` files.
- **Smart Decryption**: Uses word-scoring and file signatures to decide between RSA and Symmetric decryption for the final `problem_file.enc`.
- **Integrated Cracking**: Automatically performs Caesar and Vigenere brute-forcing on the final result to reveal Token 4.

## Update: March 6, 2026 Quiz (Group C - ID 1071316)
The Group C variation for ID `1071316` introduced a specific sequence:
1. **Details:** Base64 encoded hints: `sha512`, `rc4`, `rsa`, `cbc`, `pbkdf2`, `caesar`.
2. **Passphrase (Token 1):** `06221071316` (Cracked via SHA-512).
3. **Private Key (Token 2):** Decrypted from `private_key.enc` using **RC4** with the passphrase (Token 1) and **no salt**. 
   - *Note:* The key length was **1670 characters** for this ID.
4. **Token 3 (AES/Symmetric Key):** Extracted by RSA-decrypting `aes_key.enc` using the private key.
   - Result: `6269391303`
5. **Token 4 (Final):** Decrypting `problem_file.enc` with Token 3 using **AES-256-CBC** with **PBKDF2**, followed by a **Caesar shift of 11**.
   - Result: `jeypcrwzci`

### Similarity Analysis & Variations Matrix

| Feature | Group E (Previous) | Group C (1071316) | Standard (Old) |
|---------|-------------------|-------------------|----------------|
| **Passphrase Hash** | SHA-256 / SHA-512 | SHA-512 | SHA-256 |
| **Private Key Dec** | AES-256-CBC / RSA | **RC4 (No Salt)** | openssl rsa (direct) |
| **Intermediate Key** | RC4 (from RSA) | **AES (from RSA)** | Direct Problem File |
| **Problem Dec** | RC4 / AES-CBC | **AES-256-CBC (PBKDF2)** | AES-256-CBC |
| **Final Cipher** | Caesar / Vigenere | **Caesar (Shift 11)** | Vigenere |

**Key Takeaways for Future Quizzes:**
- **Clue Discovery:** Always Base64-decode `details.txt` first; it contains the algorithm roadmap.
- **OpenSSL 3 Legacy:** RC4 and some older ciphers REQUIRE `-provider legacy -provider default`.
- **Salt Detection:** If `od -c <file> | head` shows no `Salted__` magic number, you MUST use the `-nosalt` flag in OpenSSL.
- **Dynamic Key Chain:** The relationship between Token 1-4 is fluid. Sometimes Token 1 unlocks the private key, sometimes it's Token 2. Always follow the `details.txt` breadcrumbs.

