# OFW Assistant - TODO List

## Priority: User Testing Feedback

- [ ] Get initial user feedback on v1.0
- [ ] Document any bugs or confusion points
- [ ] Identify most-used features

## UX Improvements - API Key Management

- [ ] Add API key URL link to initial prompt screen
- [ ] Add reload/refresh button after API key is saved (avoid manual page refresh)
- [ ] Disable password manager autofill on API key input fields

## Code Quality & Maintenance

- [ ] Improve AI memo prompt to handle variable content length (prevent verbose output for brief inputs)
- [x] Refactor app.py into modular pages (800+ lines → split into components)
  - [x] Extract upload page logic
  - [x] Extract dashboard page logic
  - [x] Extract memo builder page logic
  - [x] Extract sidebar components
- [ ] Add error logging system
- [ ] Add unit tests for core functionality

## \*\*Code Quality & Maintenance

- [ ] Fix Streamlit empty label warnings
  - [ ] Add label_visibility="collapsed" to all widgets with empty labels
  - [ ] Run grep to find all instances: `grep -rn 'st\.\w\+("")' app/`
  - [ ] Consider adding to linting/review checklist

## Features to Consider (Post-Feedback)

- [ ] Bulk file processing improvements
- [ ] Export memo templates customization
- [ ] Advanced search filters in dashboard
- [ ] Memo comparison/diff tool
- [ ] Case timeline visualization
- [ ] Direct email integration (.eml improvements)

## Known Issues

- [ ] Audio/video first-run requires terminal (models download)
- [ ] LangChain deprecation warnings in console
- [ ] Large file processing can timeout from desktop shortcut

## Documentation

- [ ] Create user guide/tutorial
- [ ] Document installation troubleshooting
- [ ] Add developer setup guide for future contributors

## Future Enhancements

- [ ] Multi-user support
- [ ] Cloud backup integration
- [ ] Mobile companion app concept
- [ ] Automated report scheduling

---

Last updated: 2024-10-05
