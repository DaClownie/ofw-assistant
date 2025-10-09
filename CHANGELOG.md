# Changelog

## [1.1.2] - 2025-10-07

### Added
- Ability to create installer even if version update is cancelled

### Changed
- Better metadata on saved memos so that user can better review which versions and which files are attached to them

## [1.1.1] - 2025-10-07

### Fixed
- Legacy code remnants causing potential issues in AI memo generation after refactoring for better memo creation

## [1.1.0] - 2025-10-05

### Added
- Enhanced ChatGPT AI memo building to make clear legal summaries
- Enhanced non-AI memo building to make a usable pass that will provide user with better idea of what ChatGPT will be working with

### Fixed
- Markdown carrying over into .docx memo creation

## [1.0.7] - 2025-10-05

### Fixed
- headless terminal preventing the processing from audio/video files

### Changed
- terminal functionality
- error suppression

## [1.0.6] - 2025-10-05

### Added
- whisper predownload to ensure proper functionality out of the box

## [1.0.5] - 2025-10-05

### Fixed
- copy errors on install due to invalid file locations

## [1.0.4] - 2025-10-03

### Fixed
- Copy of files being more selective during install to alleviate collisions with other cloud services

## [1.0.3] - 2025-10-03

### Added
- model predownloading to avoid the streamlit timeout causing i/o

### Fixed
- i/o errors on upload

### Removed
- debug logging to terminal

## [1.0.2] - 2025-10-03

### Added
- Debug logging to handle i/o errors

## [1.0.1] - 2025-10-03

### Added
- docx functionality
- eml functionality

### Fixed
- path issues for i/o (implement shutil instead of Path.rename)

