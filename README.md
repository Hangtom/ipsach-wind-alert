# Ipsach Wind Alert

This GitHub Actions project checks the **Wind-10min-Max** value at WSA-Ipsach
every five minutes. It sends an iPhone notification when the wind reaches
**20 knots** between **09:00 and 20:00 Swiss time**.

It sends only one notification per windy period. A new notification becomes
possible only after the value has fallen below **15 knots**.

## 1. Install the iPhone notification app

1. Install **ntfy** from the iPhone App Store.
2. Open ntfy and tap `+` to subscribe to a topic.
3. Choose a long, private topic name, for example
   `ipsach-wind-leo-7f3x9p`. Anyone who knows a topic name can receive or send
   messages on that public ntfy topic, so do not use only `Ipsach-wind`.
4. Allow notifications when iOS asks.

## 2. Put this project on GitHub

1. Sign in at https://github.com and create a **public** repository named
   `ipsach-wind-alert`. Public repositories get free standard GitHub Actions
   minutes; your private ntfy topic remains protected in a GitHub secret.
2. Unzip this download.
3. On the new repository page, choose **uploading an existing file**.
4. Upload everything inside the `ipsach-wind-alert` folder. Make sure the
   hidden `.github` folder is included. On macOS, press `Command + Shift + .`
   in Finder if hidden files are not visible.
5. Commit the uploaded files.

## 3. Add your private ntfy topic

1. In the GitHub repository, open **Settings → Secrets and variables → Actions**.
2. Choose **New repository secret**.
3. Name it exactly `NTFY_TOPIC`.
4. Set its value to the same private topic name used in the iPhone app.

## 4. Enable and test it

1. Open the repository's **Actions** tab and enable workflows if asked.
2. Select **Check Ipsach wind**.
3. Choose **Run workflow → Run workflow**.
4. Open the running job. A successful check ends with a green checkmark.

The workflow then runs automatically. GitHub's scheduler can occasionally run
a few minutes late. The script itself uses `Europe/Zurich`, so summer/winter
clock changes are handled automatically.

## Send a test notification immediately

The normal workflow sends only if the live wind is at least 20 kn. To test the
iPhone connection independently, open this address in Safari, replacing the
final part with your topic:

`https://ntfy.sh/YOUR-PRIVATE-TOPIC/publish?message=Test`

## Change the limits later

In `.github/workflows/wind-check.yml`, add values under `env` if desired:

```yaml
env:
  NTFY_TOPIC: ${{ secrets.NTFY_TOPIC }}
  ALERT_THRESHOLD: "20"
  RESET_THRESHOLD: "15"
```

The active hours are defined near the top of `wind_alert.py`.

## Run it on a Mac

From Terminal, inside the unzipped folder:

```bash
export NTFY_TOPIC="your-private-topic"
python3 wind_alert.py
```

Run the automated tests with:

```bash
python3 -m unittest discover -s tests -v
```
