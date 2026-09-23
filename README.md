# Group Music Room Bot

Telegram group me `/play <song name>` bolo, bot ek **unique web room link** deta hai
jahan sab members ek saath, real-time synced music sun sakte hain. Playback control
(play/pause/skip/queue/volume) sab Telegram commands se hota hai.

## Kaise kaam karta hai

- Har Telegram group ka apna ek room hota hai — unique URL: `BASE_URL/room/<token>`
- Room ke andar sab connected users ka player WebSocket ke through automatically sync
  hota hai (same song, roughly same position)
- Music do jagah se aati hai:
  1. **User apni audio file bhej de** bot ko group me → automatically queue me add
  2. `/play <song name>` → Jamendo (royalty-free, legal music library) se search hoke queue me add

> ⚠️ Ye jaan-boojh kar YouTube/Spotify se audio download/stream nahi karta — wo unke
> Terms of Service todta hai. Isiliye sirf user-uploaded files aur Jamendo (legal,
> royalty-free) use kiya gaya hai.

## Commands

| Command | Kaam |
|---|---|
| `/play <song name>` | Jamendo se search karke queue me daalta hai |
| *(audio file bhejo)* | Wo file seedha queue me add ho jaati hai |
| `/pause` | Playback pause |
| `/resume` | Playback resume |
| `/skip` | Agla gaana |
| `/stop` | Queue clear, room reset |
| `/queue` | Poori queue dikhata hai |
| `/nowplaying` | Abhi kya baj raha hai |
| `/volume <0-100>` | Volume set karta hai |
| `/loop` | Queue loop on/off |
| `/remove <number>` | Queue se specific gaana hataata hai |

## Local setup

```bash
cd telegram-music-bot
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # fir .env me apni values daalo
```

### Env variables (`.env`)

- `BOT_TOKEN` — [@BotFather](https://t.me/BotFather) se `/newbot` karke lo
- `JAMENDO_CLIENT_ID` — [devportal.jamendo.com](https://devportal.jamendo.com/) par
  free account bana kar client ID generate karo
- `BASE_URL` — jahan ye app publicly host hogi (Railway URL), local testing ke liye
  `http://localhost:8000`
- `PORT` — default `8000`, Railway khud set kar deta hai

Run karne se pehle env vars load karo (ya `python-dotenv` add kar lo), phir:

```bash
python -m app.run
```

Bot polling shuru ho jayega aur web server bhi same process me chalega.

## Railway par deploy

1. Is folder ko GitHub repo me push karo
2. Railway par **New Project → Deploy from GitHub repo** select karo
3. Railway `Procfile` khud detect kar lega (`web: python -m app.run`)
4. **Variables** tab me ye set karo:
   - `BOT_TOKEN`
   - `JAMENDO_CLIENT_ID`
   - `BASE_URL` → Railway jo domain de (e.g. `https://xyz.up.railway.app`), wahi yahan daalo
   - `PORT` — Railway khud inject karta hai, chhod bhi sakte ho
5. Deploy hote hi bot live ho jayega. Group me add karo aur `/play` try karo.

## Important limitations (aage badhane layak cheezein)

- **In-memory storage**: Queue/room data RAM me store hota hai. Agar Railway app
  restart/redeploy ho, sab reset ho jayega. Persistence ke liye Postgres/Redis add
  kar sakte ho.
- **Uploaded files ka storage**: `uploads/` folder Railway ke ephemeral filesystem
  par hai — redeploy pe files delete ho sakti hain. Production ke liye S3/Cloudinary
  jaisa storage use karo.
- **Sync accuracy**: Position sync ±1.5 second tolerance ke saath hai, bilkul
  perfect real-time sync nahi (network latency ki wajah se) — chhote groups ke liye
  ye kaafi acha kaam karega.
- **"Unique domain per group"**: Har group ko ek hi base domain ke under alag
  unique **room link** milta hai (`/room/<token>`), literally alag DNS domain
  nahi — wo unnecessary complexity hai jo isi use-case ke liye zaroori nahi.
# Leaf-Music
# Leaf-Music
