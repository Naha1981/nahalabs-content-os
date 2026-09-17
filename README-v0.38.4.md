# NahaLabs Reactivate v0.38.4

Windows Playwright runtime hotfix.

The app uses Playwright for live Maps/social browser workers. On Windows, these workers require a subprocess-capable Proactor event loop. v0.38.4 installs that loop inside synchronous worker threads before Playwright starts.

Full regression suite: 84 passed in the build environment.

Windows live verification still requires the user machine to have Playwright's Chromium browser installed with:

```powershell
playwright install chromium
```
