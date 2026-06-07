# TODO

## Render deployment fix (tamipee)
- [ ] Reorder `start.sh` to run `collectstatic` earlier and ensure it fails loudly if `STATIC_ROOT` is missing after collection.
- [ ] Simplify `render.yaml` to remove redundant `releaseCommand` steps that are already executed in `start.sh`.
- [x] Redeploy and verify logs: no WhiteNoise `No directory at ... staticfiles/` warning and service stays up.


