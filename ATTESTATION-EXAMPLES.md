# Build Attestation Examples

## The Vision

Anyone who builds a package can publish on **any** medium of choice:
- Twitter/X
- Mastodon
- GitHub
- Slack
- Email
- Blog post
- IRC
- Discord

## Full Workflow Example

### Step 1: Build Package
```bash
$ cd build-tool
$ python3 -m lebowski.cli build bash \
    --opinion-file ../opinions/bash/xsc-base.yaml \
    --output-dir ~/builds

Building bash with opinion 'xsc-base'...
✓ Source fetched: bash 5.1
✓ Opinion modifications applied
✓ Package built
✓ Build manifest saved

📦 Package: bash_5.1-6ubuntu1.1_amd64.deb
🔐 SHA256: a1b2c3d4e5f6...
📋 Manifest: bash_5.1-6ubuntu1.1_amd64.lebowski-manifest.json
```

### Step 2: Generate Attestation

#### For Twitter
```bash
$ lebowski attest ~/builds/bash_5.1_amd64.lebowski-manifest.json \
    --format twitter \
    --copy

🔨 Built bash 5.1
Opinion: xsc-base
Hash: a1b2c3d4e5f6
Verify: https://builds.example.com/bash.manifest.json
#reproducibleBuilds

✅ Copied to clipboard!
```

**Post to Twitter** (paste from clipboard):
```
🔨 Built bash 5.1
Opinion: xsc-base
Hash: a1b2c3d4e5f6
Verify: https://builds.example.com/bash.manifest.json
#reproducibleBuilds
```

#### For Mastodon
```bash
$ lebowski attest ~/builds/bash_5.1_amd64.lebowski-manifest.json \
    --format mastodon \
    --url https://builds.example.com/bash.manifest.json

🔨 Reproducible Build Complete!

📦 Package: bash 5.1
🔧 Opinion: xsc-base (configure-only)
⚙️  Compiler: x86_64-xsc-linux-gnu-gcc
🔐 Output Hash: a1b2c3d4e5f6...

✅ Anyone can rebuild and verify!

📋 Manifest: https://builds.example.com/bash.manifest.json

#ReproducibleBuilds #SoftwareSupplyChain #Security
```

#### For GitHub
```bash
$ lebowski attest ~/builds/bash_5.1_amd64.lebowski-manifest.json \
    --format github \
    --url https://builds.example.com/bash.manifest.json

## Build Attestation

**Package:** `bash-5.1`

### Source
- **Fetch Method:** `apt-get source`
- **DSC Hash:** `abc123def456...`

### Opinion
- **Name:** `xsc-base`
- **Purity Level:** `configure-only`
- **Opinion Hash:** `def456abc789...`

### Toolchain
- **Compiler:** `x86_64-xsc-linux-gnu-gcc`
- **Version:** `x86_64-xsc-linux-gnu-gcc (GCC) 13.2.0`
- **Compiler Hash:** `ghi789jkl012...`

### Output
- **Filename:** `bash_5.1-6ubuntu1.1_amd64.deb`
- **SHA256:** `a1b2c3d4e5f6...`

### Manifest
https://builds.example.com/bash.manifest.json

### Verification
Anyone can rebuild this package and verify it produces an identical hash:

```bash
lebowski verify https://builds.example.com/bash.manifest.json
```

This build is **reproducible** - anyone with the same source, opinion, and toolchain will produce a bit-for-bit identical package.
```

#### For Slack
```bash
$ lebowski attest ~/builds/bash_5.1_amd64.lebowski-manifest.json \
    --format slack

*Build Complete* :hammer:

*Package:* `bash-5.1`
*Opinion:* `xsc-base`
*Output Hash:* `a1b2c3d4e5f6...`

:white_check_mark: Reproducible build - anyone can verify!
```

#### One-line (for git commits)
```bash
$ lebowski attest ~/builds/bash_5.1_amd64.lebowski-manifest.json \
    --format oneline

[lebowski] bash-5.1 + xsc-base + x86_64-xsc-linux-gnu-gcc → a1b2c3d4e5f6
```

**Use in git commit:**
```bash
$ git add opinions/bash/xsc-base.yaml
$ git commit -m "Add XSC opinion for bash

$(lebowski attest ~/builds/bash.manifest.json --format oneline)
"
```

## Real-World Social Posting Examples

### Twitter Thread
```
Tweet 1:
🔨 Just built bash 5.1 for XSC with reproducible builds!

📦 Package: bash_5.1_amd64.deb
🔐 Hash: a1b2c3d4e5f6...
📄 Manifest: https://t.co/abc123

Who wants to verify? #reproducibleBuilds 🧵

---

Tweet 2:
Build details:
✓ Source: Debian bash 5.1 (verified DSC)
✓ Opinion: xsc-base (configure-only purity)
✓ Toolchain: XSC GCC 13.2.0
✓ Environment: Fully documented

Complete transparency from source → binary!

---

Tweet 3:
To verify:
1. Download manifest
2. Rebuild using same opinion
3. Compare hashes

If hashes match → provably legitimate build

No trust required - it's math! 🔐

#SoftwareSupplyChain #Security
```

### GitHub Discussion
**Title:** "Verify: bash 5.1 with XSC toolchain"

**Body:**
```markdown
I've built bash 5.1 with the XSC toolchain using Lebowski.

## Build Details

- **Package:** bash-5.1-6ubuntu1.1
- **Opinion:** xsc-base (configure-only purity)
- **Output:** bash_5.1-6ubuntu1.1_amd64.deb
- **SHA256:** a1b2c3d4e5f67890...

## Verification

### Download Manifest
```bash
curl -O https://builds.example.com/bash_5.1_amd64.lebowski-manifest.json
```

### Rebuild & Verify
```bash
lebowski verify bash_5.1_amd64.lebowski-manifest.json
```

If you get the same hash, please comment below with:
- ✅ Verified
- Your build environment
- Any issues encountered

## Current Verifications
- [ ] Waiting for first verification...

## Manifest
[Full manifest JSON here]

---

**Please help verify this build!** The more independent verifications, the more trustworthy the package.
```

### Mastodon Toot
```
🔨 Reproducible build announcement! 🎉

I just built bash 5.1 for the XSC project using @lebowski - a new reproducible Debian package builder.

📦 Package: bash 5.1
🔧 Opinion: xsc-base (configure-only)
⚙️  Toolchain: XSC GCC 13.2.0
🔐 Hash: a1b2c3d4e5f67890...

The cool part? Anyone can rebuild this and get the EXACT same binary (bit-for-bit). No trust required - just math!

📋 Manifest: https://builds.example.com/bash.manifest.json

Want to verify? Install lebowski and run:
```
lebowski verify <manifest-url>
```

If you verify this build, please boost and reply with your results!

#ReproducibleBuilds #OpenSource #Security #SoftwareSupplyChain #Debian #XSC
```

### Reddit Post
**Title:** "I built bash with a custom toolchain - here's proof it's reproducible"

**Body:**
```markdown
Hey r/programming,

I've been working on XSC (a ring-based syscall system) and needed to rebuild bash with a custom toolchain. Instead of just saying "trust me," I used Lebowski to make it reproducible.

## What's Lebowski?

A Debian package builder that:
- Documents EVERYTHING (source, toolchain, environment)
- Makes builds reproducible (anyone can verify)
- Generates attestations you can post anywhere

## My Build

**Package:** bash 5.1
**Toolchain:** x86_64-xsc-linux-gnu-gcc 13.2.0
**Opinion:** xsc-base (just compiler flags, no patches)
**Output:** bash_5.1-6ubuntu1.1_amd64.deb
**SHA256:** a1b2c3d4e5f67890...

[Full attestation]

## Verify Yourself

```bash
# Install lebowski
git clone https://github.com/user/lebowski
cd lebowski

# Verify my build
lebowski verify https://builds.example.com/bash.manifest.json
```

If you get the same hash → my binary is provably legitimate.
If you get a different hash → something's wrong (please tell me!)

## Why This Matters

Traditionally:
- Developer builds package
- Users download it
- Hope it's not malware

With reproducible builds:
- Developer builds package
- Posts manifest
- Anyone can rebuild and verify
- Math proves it's legitimate

No central authority. No trust required. Just cryptographic proof.

## Results?

I'd love it if someone could verify this build! Takes about 5 minutes on a modern machine.

Comment with your hash if you try it!

---

**Edit:** Already got 3 verifications - all hashes match! ✅
```

### Email to Team
```
Subject: [builds] bash 5.1 for XSC - Please Verify

Team,

I've built bash 5.1 with the XSC toolchain. Before we deploy to production, please verify the build.

PACKAGE: bash-5.1-6ubuntu1.1
OPINION: xsc-base (configure-only purity)
OUTPUT:  bash_5.1-6ubuntu1.1_amd64.deb
SHA256:  a1b2c3d4e5f67890abcdef1234567890...

MANIFEST: https://internal-builds.company.com/bash.manifest.json

TO VERIFY:
1. Download manifest
2. Run: lebowski verify <manifest-url>
3. Compare hash with above

If hash matches, reply with "✅ Verified" and I'll proceed with deployment.

If hash doesn't match, reply immediately - we may have a security issue.

Target: 3 independent verifications before production deployment

Thanks,
Alice
---
[lebowski] bash-5.1 + xsc-base + x86_64-xsc-linux-gnu-gcc → a1b2c3d4e5f6
```

### IRC
```
<alice> Built bash 5.1 for XSC: hash=a1b2c3d4e5f6... manifest=https://builds.example.com/bash.json
<bob> checking...
<bob> rebuilt, got a1b2c3d4e5f6... ✅ matches!
<carol> also verified ✅
<alice> awesome, 2/2 verifications. deploying to staging.
```

## The Power of Platform Independence

### Same Build, Many Platforms

**Alice builds bash:**
```bash
lebowski build bash --opinion xsc-base
```

**Posts everywhere:**
```bash
# Twitter
lebowski attest manifest.json --format twitter | pbcopy
# → Paste to Twitter

# GitHub
lebowski attest manifest.json --format github > build-attestation.md
# → Create GitHub discussion

# Slack
lebowski attest manifest.json --format slack | slack-cli post #builds
# → Auto-post to Slack

# Mastodon
lebowski attest manifest.json --format mastodon > toot.txt
# → Paste to Mastodon

# Email
lebowski attest manifest.json --format full | mail -s "Build: bash 5.1" team@company.com
```

**Result:**
- Same build
- Same manifest
- Same hash
- Posted to 5+ platforms
- Anyone, anywhere can verify

## Verification Network Effect

```
Day 1, 10:00 - Alice builds & posts
Day 1, 10:15 - Bob verifies on Twitter ✅
Day 1, 10:20 - Carol verifies on GitHub ✅
Day 1, 10:30 - Dave verifies on Mastodon ✅
Day 1, 11:00 - 10 more people verify ✅
Day 1, 12:00 - Package has 13 independent verifications

Trust level: EXTREMELY HIGH
Consensus: 13/13 verifications passed (100%)
```

## Attack Resistance

### Attack Attempt
```
Attacker: Builds malicious bash with backdoor
Attacker: Posts: "Built bash - hash: BADBEEF..."

Verifiers rebuild:
@bob:   "❌ Hash doesn't match - I got a1b2c3... not BADBEEF"
@carol: "❌ Hash mismatch - POSSIBLE MALWARE"
@dave:  "❌ Hash different - DO NOT USE"

Result: Attack fails publicly
        Attacker exposed
        Network protected
```

## Implementation Status

### ✅ Implemented
- Attestation format (full, compact, one-line, JSON)
- Social platform formats (Twitter, Mastodon, GitHub, Slack)
- CLI command: `lebowski attest`
- Clipboard support

### 🚧 Next Steps
- GPG signing of attestations
- Verification command implementation
- Public registry of verified builds
- Automated posting to social platforms

---

**This is the future: Build once, verify everywhere.**

No matter what platform you use - Twitter, Mastodon, GitHub, email, IRC - you can participate in the verification network.

**"This commit hash + this compiler + these flags on this architecture → this output hash"**

Universal. Verifiable. Trustless.
