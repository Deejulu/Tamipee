# TODO

- [x] Inspect current static/CSS loading setup (templates, settings, start.sh)
- [x] Fix broken `start.sh` (remove merge-conflict markers) to make `collectstatic` + verification deterministic
- [ ] Redeploy to Render
- [ ] Verify CSS loads on hosted site (check browser Network tab for `/static/.../main*.css`)
- [ ] If still failing, inspect Render logs for `collectstatic` output and WhiteNoise/STATICFILES_STORAGE behavior

