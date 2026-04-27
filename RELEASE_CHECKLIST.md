# Release Checklist

## Before release

- Update `APP_VERSION` in `watchdog.py` if needed.
- Test from source: `python watchdog.py`.
- Build EXE locally: run `BUILD.bat`.
- Verify `dist/VoltWatch.exe` launches and tray icon appears.
- Confirm `X` behavior and tray `Exit` behavior.
- Confirm startup register/unregister works from Settings.

## Publish on GitHub

- Push changes to `main`.
- Create a version tag such as `v3.1.0`.
- Push tag (`git push origin v3.1.0`).
- Wait for GitHub Actions workflow **Build Windows EXE** to finish.
- Download artifact `VoltWatch-windows`.
- Create a GitHub Release and attach `VoltWatch.exe`.

## Optional quality checks

- Run on a clean Windows user profile.
- Validate onboarding and profile defaults.
- Verify no false positive kills for your key apps.
