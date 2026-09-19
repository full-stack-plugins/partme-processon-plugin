## ADDED Requirements

### Requirement: ProcessOn skills use an immutable verified source
The plugin MUST vendor its managed ProcessOn skills from an immutable release tag and matching peeled commit SHA.

#### Scenario: Plugin distribution is validated
- **WHEN** online and offline vendor checks run
- **THEN** the lock, local snapshot, release tag, peeled SHA, and upstream skill content match
