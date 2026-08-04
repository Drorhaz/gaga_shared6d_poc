# Path sanitization for Git freeze

Absolute local filesystem prefixes were rewritten to relative forms for privacy:
- `/…/gaga_jcvpca` → `../gaga_jcvpca`
- `/…/gaga_shared6d_poc` → `.`

Scientific identifiers, SHA-256 checksums, dates, and analysis outputs were not altered.
Raw OptiTrack recordings were never copied into this project and are not committed.
