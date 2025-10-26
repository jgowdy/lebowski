# Build Ring: Social Verification Network

## Concept

A **Build Ring** is a network of people who verify each other's reproducible builds, similar to:
- **Web rings** (1990s): Trusted circles of websites
- **Web of Trust** (PGP): Decentralized key verification
- **Social proof**: Verification through trusted networks

## How It Works

### 1. Builder Creates Package
```bash
$ lebowski build bash --opinion xsc-base --sign

Building bash with opinion 'xsc-base'...
✓ Source fetched: bash 5.1
✓ Opinion modifications applied
✓ Package built: bash_5.1-6ubuntu1.1_amd64.deb
✓ SHA256: a1b2c3d4e5f6...

📄 Manifest: bash_5.1-6ubuntu1.1_amd64.lebowski-manifest.json
✅ Signed with: alice@example.com

Ready to publish!
```

### 2. Builder Publishes
```bash
$ lebowski ring publish bash_5.1_amd64.deb

Publishing to build ring...
📦 Package: bash_5.1-6ubuntu1.1_amd64.deb
🔐 Hash: a1b2c3d4e5f6...
📄 Manifest: https://builds.example.com/bash.manifest.json
👤 Builder: alice@example.com

Share this:
  Twitter: [Copy tweet]
  Mastodon: [Copy toot]
  GitHub: [Create discussion]
```

### 3. Ring Members Verify
```bash
$ lebowski ring verify alice@example.com bash_5.1_amd64.deb

Verifying alice@example.com's bash build...

Step 1: Download manifest ✓
Step 2: Fetch source (sha256 verified) ✓
Step 3: Load opinion (sha256 verified) ✓
Step 4: Rebuild package...
   ... compiling ...
   ... packaging ...
Step 5: Compare hashes ✓

VERIFICATION RESULT:
  Expected: a1b2c3d4e5f6...
  Got:      a1b2c3d4e5f6...

  ✅ HASHES MATCH - BUILD IS REPRODUCIBLE!

Sign and publish verification? [y/N]: y

✅ Verification published!
   Share: [Copy tweet]
```

### 4. Network Consensus
After multiple verifications:
```bash
$ lebowski ring status bash_5.1_amd64.deb

Package: bash_5.1-6ubuntu1.1_amd64.deb
Builder: alice@example.com
Hash: a1b2c3d4e5f6...

Verifications:
  ✅ bob@example.com      (verified 2025-10-26 08:30 UTC)
  ✅ carol@company.com    (verified 2025-10-26 08:35 UTC)
  ✅ dave@security.org    (verified 2025-10-26 08:40 UTC)
  ✅ eve@infosec.dev      (verified 2025-10-26 08:45 UTC)
  ✅ frank@company.com    (verified 2025-10-26 08:50 UTC)

Trust Level: HIGH (5 independent verifications)
Consensus: 5/5 hashes match (100%)

Safe to deploy? YES ✅
```

## Ring Structure

### Personal Ring (Small Team)
```yaml
ring:
  name: "my-team"
  members:
    - alice@example.com
    - bob@example.com
    - carol@example.com

  policy:
    minimum_verifications: 2
    require_all: false
```

### Company Ring (Organization)
```yaml
ring:
  name: "godaddy-infosec"
  members:
    - security-team@godaddy.com
    - sre-team@godaddy.com
    - build-team@godaddy.com

  policy:
    minimum_verifications: 3
    require_security_team: true
```

### Public Ring (Community)
```yaml
ring:
  name: "debian-xsc-community"
  members:
    - maintainer@debian-xsc.org
    - "*@debian-xsc.org"  # Any member

  policy:
    minimum_verifications: 10
    reputation_threshold: 50
```

## Social Integration

### Twitter/X Integration
```python
# lebowski/social/twitter.py

class TwitterRing:
    def publish_build(self, package, manifest):
        """Post build to Twitter"""
        tweet = f"""
🔨 Built {package.name} for XSC

📦 Package: {package.filename}
🔐 SHA256: {manifest['output']['package_sha256'][:16]}...
📄 Manifest: {manifest_url}
🧪 Opinion: {manifest['opinion']['name']} ({manifest['opinion']['purity_level']})

Who wants to verify? #reproducibleBuilds #webOfTrust
        """
        self.post(tweet)

    def publish_verification(self, package, result):
        """Post verification result"""
        if result.matches:
            tweet = f"""
✅ Verified @{result.builder}'s {package.name} build

🔒 Hash matches: {result.hash[:16]}...
⏱️ Rebuilt in {result.build_time}
🎯 Bit-for-bit identical

Package is legitimate! #reproducibleBuilds
            """
        else:
            tweet = f"""
❌ VERIFICATION FAILED for @{result.builder}'s {package.name}

Expected: {result.expected_hash[:16]}...
Got:      {result.actual_hash[:16]}...

⚠️ DO NOT USE THIS PACKAGE

#security #reproducibleBuilds
            """
        self.post(tweet)
```

### Mastodon Integration
```python
# lebowski/social/mastodon.py

class MastodonRing:
    def publish_build(self, package, manifest):
        """Post build to Mastodon"""
        toot = f"""
🔨 Built {package.name} with #Lebowski

Package: {package.filename}
SHA256: {manifest['output']['package_sha256']}
Manifest: {manifest_url}

Reproducible build - anyone can verify!

#ReproducibleBuilds #SoftwareSupplyChain #XSC
        """
        self.post(toot)
```

### GitHub Discussions Integration
```python
# lebowski/social/github.py

class GitHubRing:
    def create_verification_discussion(self, package, manifest):
        """Create GitHub discussion for verification"""
        title = f"Verify: {package.name} {package.version}"
        body = f"""
## Build Verification Request

**Package:** `{package.filename}`
**Builder:** {manifest['builder']['identity']}
**SHA256:** `{manifest['output']['package_sha256']}`

### Manifest
```json
{json.dumps(manifest, indent=2)}
```

### How to Verify
```bash
lebowski ring verify {manifest['builder']['identity']} {package.filename}
```

### Verifications
- [ ] Waiting for verifications...

Please comment with your verification results!
        """
        self.create_discussion(title, body)

    def update_verification(self, discussion_id, verifier, result):
        """Add verification to discussion"""
        if result.matches:
            comment = f"""
✅ **Verified by @{verifier}**

- Hash matches: `{result.hash}`
- Build time: {result.build_time}
- Bit-for-bit identical: YES

Signed verification: {result.signature_url}
            """
        else:
            comment = f"""
❌ **VERIFICATION FAILED** (@{verifier})

- Expected: `{result.expected_hash}`
- Got: `{result.actual_hash}`

**DO NOT USE THIS PACKAGE**
            """
        self.post_comment(discussion_id, comment)
```

## Ring Protocol

### Manifest Enhancement
```json
{
  "builder": {
    "identity": "alice@example.com",
    "gpg_key_fingerprint": "ABC123...",
    "build_timestamp": "2025-10-26T08:30:00Z",
    "signature": "..."
  },

  "verifications": [
    {
      "verifier": "bob@example.com",
      "timestamp": "2025-10-26T08:35:00Z",
      "hash_matched": true,
      "build_time_seconds": 180,
      "environment": {
        "hostname": "bob-laptop",
        "os": "Linux 6.11.0"
      },
      "signature": "...",
      "published_to": [
        "https://twitter.com/bob/status/123...",
        "https://github.com/discussions/456..."
      ]
    },
    {
      "verifier": "carol@company.com",
      "timestamp": "2025-10-26T08:40:00Z",
      "hash_matched": true,
      "build_time_seconds": 175,
      "signature": "..."
    }
  ],

  "consensus": {
    "total_verifications": 5,
    "successful": 5,
    "failed": 0,
    "trust_score": 100
  }
}
```

## Attack Resistance

### Attack: Fake Verification
```
Attacker posts: "✅ Verified - hash matches!"

But: Verification not signed with GPG key
     → Ring rejects verification
     → Attack fails
```

### Attack: Compromised Builder
```
alice@example.com is compromised
Attacker builds malicious package

But: Ring members rebuild
     → Hash doesn't match
     → 0/10 verifications succeed
     → Package rejected
     → Alice is alerted
```

### Attack: Sybil Attack (Fake Accounts)
```
Attacker creates fake verifiers:
  - fake1@example.com
  - fake2@example.com
  - fake3@example.com

But: Ring requires reputation
     → New accounts have 0 reputation
     → Verifications not counted
     → Attack fails
```

## Reputation System

### Earning Reputation
```python
def calculate_reputation(verifier):
    score = 0

    # Verifications that matched other verifiers
    score += verifier.successful_verifications * 10

    # Found real mismatches (caught attacks)
    score += verifier.caught_attacks * 100

    # Age of account
    score += min(verifier.account_age_days / 10, 50)

    # Endorsements from trusted members
    score += verifier.endorsements * 20

    return score

# Example:
# - New user: 0 points
# - 10 verifications: 100 points
# - Caught 1 attack: 200 points
# - Account 1 year old: 36.5 points
# - Total: 336.5 points → "TRUSTED" status
```

### Ring Policies
```yaml
ring:
  name: "high-security"

  policies:
    minimum_verifiers: 5
    minimum_reputation: 100

    require_from_each_group:
      - security-team: 1
      - build-team: 1
      - community: 3

    block_list:
      - compromised@old-domain.com
      - spammer@example.com
```

## CLI Commands

```bash
# Create/join ring
lebowski ring create my-team
lebowski ring join debian-xsc-community

# Publish build
lebowski ring publish bash_5.1_amd64.deb
lebowski ring publish --twitter --github bash_5.1_amd64.deb

# Verify build
lebowski ring verify alice@example.com bash_5.1_amd64.deb
lebowski ring verify --auto-publish bash_5.1_amd64.deb

# Check status
lebowski ring status bash_5.1_amd64.deb
lebowski ring list-verifications

# Manage reputation
lebowski ring reputation bob@example.com
lebowski ring endorse carol@company.com
lebowski ring report spammer@example.com
```

## Implementation Status

### Phase 1: Core (MVP)
- [ ] Manifest signing (GPG)
- [ ] Verification recording
- [ ] Ring configuration files
- [ ] CLI: publish, verify, status

### Phase 2: Social Integration
- [ ] Twitter API integration
- [ ] Mastodon API integration
- [ ] GitHub Discussions API

### Phase 3: Reputation & Trust
- [ ] Reputation scoring
- [ ] Ring policies
- [ ] Block lists / allow lists

### Phase 4: Web UI
- [ ] Public verification dashboard
- [ ] Ring member directory
- [ ] Package search & trust visualization

## Why This Changes Everything

### Old Model
```
1. Developer builds package
2. Publishes to repository
3. Users install

Trust: Based on who published it
Verification: None
```

### Build Ring Model
```
1. Developer builds package
2. Publishes with manifest
3. Ring verifies (10+ people rebuild)
4. All get same hash
5. Consensus reached
6. Users install

Trust: Based on mathematical proof
Verification: Distributed & transparent
```

## Example: Real-World Scenario

### Scenario: Critical Security Patch
```
Day 1, 09:00 - OpenSSH vulnerability discovered
Day 1, 10:00 - alice@security.org patches & builds openssh
Day 1, 10:05 - Posts to Security Ring:
  "🚨 Built openssh-9.9p1 with CVE-2025-1234 fix
   SHA256: abc123...
   URGENT - please verify!"

Day 1, 10:15 - bob@securityco verifies ✅ (matches)
Day 1, 10:20 - carol@infosec verifies ✅ (matches)
Day 1, 10:25 - dave@company verifies ✅ (matches)
Day 1, 10:30 - 5 more verify ✅ (all match)

Day 1, 10:35 - Consensus: 8/8 verifications passed
Day 1, 10:40 - Companies deploy to production

Result: Critical patch verified & deployed in 100 minutes
        Without central authority
        With mathematical proof of legitimacy
```

---

**This is the future of software supply chain security.**

From "trust me" → "verify yourself" → "the network verified"
