# Lebowski Roadmap

## Phased Approach

### Phase 1: Opinion Definitions (MVP)

**Goal:** Make it trivially easy to build Debian packages with different opinions

**What we provide:**
- Opinion definitions (diffs, formulas, scripts)
- Tool to apply opinions and build locally
- Repository of community opinions

**What users do:**
- Download opinion definition
- Run lebowski build tool
- Tool fetches Debian source, applies opinion, builds package
- Install the resulting .deb

**Benefits of this approach:**
- Simple to start
- No build infrastructure needed
- No repository hosting needed
- Users build what they need, when they need it
- Community can contribute opinions immediately

**Example:**

```bash
# Install lebowski tool
apt install lebowski  # or download binary

# Build nginx with HTTP/3 opinion
lebowski build nginx --opinion http3

# Tool does:
# 1. Fetch nginx source from Debian
# 2. Fetch http3.yaml opinion from opinions repo
# 3. Apply modifications
# 4. Build package
# 5. Output: nginx-http3_1.24.0-1~opinion1_amd64.deb

# Install it
sudo dpkg -i nginx-http3_1.24.0-1~opinion1_amd64.deb
```

### Phase 2: Pre-built Popular Opinions

**Goal:** Provide pre-built packages for popular opinions

**What we add:**
- Build infrastructure (CI/CD)
- APT repository hosting
- Package signing
- Automated builds of popular opinions

**What users do:**
- Add Lebowski APT repository
- `apt install nginx-http3` - just works, no building

**Benefits:**
- Instant installation
- No local compilation
- Curated popular opinions
- Automatic updates

**Criteria for pre-built opinions:**
- Popular (high usage)
- Stable (well-tested)
- Maintained (active maintainer)

### Phase 3: Community Build Network

**Goal:** Distributed building and hosting

**What we add:**
- Allow community members to host build servers
- Trust/verification system
- Distributed package hosting

**This is future - Phase 1 is the focus**

## Phase 1 Deliverables

### 1. Opinion Definition Format

YAML-based format for defining package modifications:

```yaml
package: nginx
opinion_name: http3
version: "1.0"
description: nginx with HTTP/3 support

modifications:
  patches:
    - http3-support.patch
  configure_flags:
    add: ["--with-http_v3_module"]
  build_deps:
    add: ["libquiche-dev"]
```

### 2. Lebowski Build Tool

CLI tool that:
- Fetches Debian source packages
- Downloads opinion definitions
- Applies modifications
- Builds packages
- Makes it as easy as: `lebowski build nginx --opinion http3`

### 3. Opinion Repository

Git repository containing:
- `/opinions/<package>/<opinion-name>.yaml`
- `/patches/<package>/<patch-files>`
- `/scripts/<helper-scripts>`
- Documentation

### 4. Initial Opinions

Start with popular packages and common opinions:

**nginx:**
- minimal - stripped down
- http3 - with QUIC support
- full - all modules

**python3:**
- optimized - with LTO, PGO
- minimal - without rarely-used modules

**gcc:**
- native - optimized for builder's CPU

**ffmpeg:**
- full - all codecs
- minimal - basic codecs only

### 5. Documentation

- User guide: how to use lebowski
- Opinion author guide: how to create opinions
- Best practices
- FAQ

## Success Metrics

### Phase 1 Success Looks Like:

1. **Easy for users:** Building a custom package takes one command
2. **Easy for contributors:** Adding a new opinion is just a YAML file + PR
3. **Active community:** 10+ opinion contributors, 50+ opinions
4. **Popular packages covered:** Top 20 commonly-customized packages have opinions
5. **Adoption:** 1000+ users building with opinions

### Timeline Estimate

**Phase 1 MVP:**
- Month 1: Core build tool + opinion format
- Month 2: Initial opinions for 5 packages
- Month 3: Documentation + community launch

**Phase 2:**
- After Phase 1 has proven community adoption
- 6 months after Phase 1 launch

## Current Status

- [x] Project concept
- [x] Philosophy and motivation documented
- [x] Architecture designed
- [ ] Opinion format specification
- [ ] Build tool implementation
- [ ] Opinion repository setup
- [ ] Initial opinions created
- [ ] User documentation
- [ ] Alpha release

## Next Immediate Steps

1. Finalize opinion YAML schema
2. Research Debian source package building (tools, process)
3. Prototype build tool
4. Create 3 sample opinions to test the workflow
5. Iterate on format based on real-world usage
