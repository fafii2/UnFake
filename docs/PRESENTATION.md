# Presenting UnFake with Facebook and real news

Use the `extension` folder in this working copy. The earlier November 19 copy does
not include the new upload, live status, retry, and polling changes.

## Before class

1. Run `Start-UnFake.cmd` from the project folder. Keep its window open. This computer's
   Python environment has been repaired; another computer needs `Setup-UnFake.ps1` first.
2. In Chrome, open `chrome://extensions`. If UnFake already points to this folder,
   click its reload button. Otherwise load this project's `extension` folder as an
   unpacked extension with Developer mode enabled. Pin UnFake to the toolbar.
3. Open Facebook or a normal news webpage. Refresh it after updating the extension.
4. Open UnFake and choose **Check live connections**. Wait for **Live search and
   evaluation verified**. This makes small real provider requests and caches their
   result for five minutes. Merely seeing “backend online” does not verify the APIs.
5. Keep the internet connection on. If the service check reports credentials, quota,
   or provider errors, fix that connection before presenting.

## Checking a post

For copied text, paste **one factual assertion** into UnFake and choose **Verify Text
Claim**. Alternatively highlight the claim on Facebook, right-click, and choose
**Verify Text with UnFake**. Close the popup to read the result on the page.

For an image, choose **Crop text from this page**, then drag around the headline or
claim. Stay on that tab while the screenshot is captured. You can also choose a
saved PNG, JPEG, or WebP under 5 MB and 20 megapixels. OCR is local; review its text,
remove buttons/comments/usernames, correct numbers, and retain dates before verifying.
The image itself is not sent to the backend or model.

The result includes linked evidence and an explanation. Open a source to show the
professor how it supports or contradicts the selected statement. A live check can
take around a minute when providers are busy; the extension keeps polling while it
finishes. Temporary Gemini server errors get one retry.

## Choosing a claim fairly

The current search source list focuses on Philippine news, government sources,
and fact-checkers. A random post can be too new, outside those sources, ambiguous,
or an opinion. **Insufficient evidence** is a valid result; it does not mean false.
The app does not establish whether a whole Facebook account, post, photograph, or
video is authentic. Image input extracts text for claim checking.

Include the event date and place. If you copy an entire post containing several
claims, check its assertions separately. Do not remove wording that changes meaning.
OCR confidence measures text recognition; it is not a truth percentage.

## Validation and remaining checks

On November 22, 2026, both live connection checks passed. All **148 backend tests**
and **11 extension tests** passed. Three actual API checks also passed through the
asynchronous verification path, with five web sources returned for each:

| Input | Actual verdict | Backend processing |
|---|---|---|
| Philippine population was 112,729,484 on July 1, 2024 | Supported | 26.6 seconds |
| Same date, changed number of 12,729,484 | Contradicted | 16.6 seconds |
| Deliberately fictional Lunavela underwater airport assertion | Insufficient evidence | 19.0 seconds |

The population report can be read on the
[Presidential Communications Office website](https://pco.gov.ph/news_releases/pbbm-declares-112-7m-philippine-population-count-as-official/).
Initial calls encountered Gemini HTTP 503 errors, which motivated the retry and
longer asynchronous path. These measured cases do not guarantee provider uptime or
establish accuracy across arbitrary news.

The updated browser flow still needs a local Facebook rehearsal: browser control
could not verify the active Chrome URL, and the isolated headless browser launch
failed in this managed environment. No claim is made that the updated Facebook UI
or uploaded-image OCR has passed a full browser run here.

Automated checks:

```powershell
cd backend
& ..\.venv\Scripts\python.exe -m pytest tests -q
& ..\.venv\Scripts\python.exe -m scripts.check_providers
& ..\.venv\Scripts\python.exe -m scripts.live_smoke --live
cd ..
node --test tests/extension.test.cjs
```

The last two provider commands consume real API quota. `live_smoke` checks a published
population figure, an altered number, and a deliberately fictional assertion; it
writes actual responses to ignored `test-results/live-api.json`. These are connection
and regression checks, not research accuracy results.

Keep `backend/.env` private. API credentials belong only on the backend, not in the
extension, screenshots, public repository, or presentation slides.
