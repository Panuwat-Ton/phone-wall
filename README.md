# phone-wall

View many Android phones on one PC screen at once, and control one phone or all of them together.
Built on [scrcpy](https://github.com/Genymobile/scrcpy) (not included — see step 2).
Panel UI language: English or Thai (`"language": "en"` / `"th"` in `config.json`).

- **View-only by default** — nothing you click reaches a phone until you switch that phone to *Control*.
- **Open all, or only some** — tick phones, press *Open selected*.
- **Group control** — click/drag in the dark pad to tap/swipe on every ticked phone at the same time
  (coordinates are scaled to each phone's screen). Back / Home / Recents / Wake / Power and app launch/quit buttons too.
- **Light on weak PCs** — low resolution (480/640/720), 10 fps, no audio, windows opened one by one.
- Optional: turn the phones' real screens off while you control them.

Only use it on phones you own or are allowed to manage.

## Setup (Windows, about 10 minutes)

### 1. Install Python
Python 3.9+ from python.org (tick *Add to PATH*). Tkinter is included.

### 2. Download scrcpy
Get `scrcpy-win64-*.zip` from <https://github.com/Genymobile/scrcpy/releases>, unzip it into a folder named
`scrcpy` next to `phone_wall.pyw`. It already contains `adb.exe`. (Or set `scrcpy_path` / `adb_path` in `config.json`.)

### 3. Prepare each phone (once)
1. Settings → About phone → tap **Build number** 7 times (turns on Developer options).
2. Developer options → turn on **USB debugging** and **Wireless debugging**.
3. Phone and PC must be on the **same Wi-Fi**.
4. Easiest first connection — with a USB cable:
   ```
   scrcpy\adb tcpip 5555
   ```
   Allow the "Allow USB debugging?" prompt on the phone, then unplug. The phone is now at `PHONE_IP:5555`
   (Settings → About → Status → IP address). Give each phone its own port if you like (`adb tcpip 6666`).
   The port is forgotten when the phone reboots — repeat this step then.
   Android 11+ alternative without a cable: Wireless debugging → *Pair device with pairing code*, then
   `scrcpy\adb pair IP:PAIRPORT` and `scrcpy\adb connect IP:PORT`.
5. Tip: reserve a fixed IP for each phone in your router so the address never changes.

### 4. Start the panel
Double-click `open_panel.bat` (or `pythonw phone_wall.pyw`). On first run it creates `config.json`.
Press **Add phone** (name + `ip:port`) for each phone, or edit `config.json`:

```json
{
  "language": "en",
  "devices": { "red": "192.168.1.101:5555", "blue": "192.168.1.102:5555" },
  "resolution": 480, "max_fps": 10, "bitrate_mbps": 1
}
```

Restart the panel after adding phones.

## Using it
| What you want | Do this |
|---|---|
| See all phones | *Select all* → *Open selected* (or *Open all*) |
| See only some | tick them → *Open selected* |
| Control one phone | press its **View only** button → it becomes **Control**; the window reopens controllable |
| Control many at once | tick them → click/drag on the dark pad, or use the keys / app buttons |
| Close | *Close selected* / *Close all* (the windows have no title bar) |
| A phone says "adb offline" | *Reconnect adb* |
| Sharper picture | Resolution 640 or 720 (applies the next time a window opens) |

Group control is coordinate-based: apps that look different on each phone may need a tap on a different spot.
Phones with a PIN lock screen cannot be unlocked by the swipe the app buttons use.

## Troubleshooting
- *scrcpy not found* → step 2. *adb not found* → use the adb inside the scrcpy folder.
- *adb offline* → phone asleep/rebooted/new IP. Reconnect, or repeat `adb tcpip` over USB.
- Windows are too big/small → the panel tiles windows across the top of the screen automatically
  (up to 3 rows); with many phones lower the resolution.
- Antivirus that scans HTTPS can break downloads inside Python; this tool downloads nothing itself.

## Licence
MIT — see `LICENSE`. scrcpy is Apache-2.0 and is not bundled.

---

# phone-wall (ภาษาไทย)

ดูจอมือถือ Android หลายเครื่องบนหน้าจอคอมเดียว และคุมทีละเครื่องหรือทุกเครื่องพร้อมกัน ใช้ scrcpy ข้างใน
(ไม่ได้แถมมาด้วย ดูขั้นที่ 2) ตั้งภาษาแผงได้ใน `config.json` (`"language": "th"`)

- **ค่าเริ่มต้นเป็นดูอย่างเดียว** จนกว่าจะกดสลับเครื่องนั้นเป็น "ควบคุม"
- เปิดทั้งหมด หรือเลือกเปิดบางเครื่อง (ติ๊ก → เปิดที่เลือก)
- Group control: คลิก/ลากในกรอบดำ = แตะ/ปัดบนทุกเครื่องที่ติ๊ก (ปรับตามขนาดจอแต่ละเครื่อง) มีปุ่ม Back/Home/Recents/Wake/Power และปุ่มเปิด/ปิดแอป
- เบาสำหรับคอมแรม 4 GB: ความละเอียดต่ำ 480/640/720, 10 เฟรม, ไม่มีเสียง, เปิดทีละเครื่อง
- ตัวเลือกดับจอจริงของมือถือตอนควบคุม

ใช้กับมือถือของตัวเองหรือที่ได้รับอนุญาตเท่านั้น

## ตั้งค่า (Windows ราว 10 นาที)
1. ลง **Python 3.9+** จาก python.org (ติ๊ก Add to PATH)
2. โหลด `scrcpy-win64-*.zip` จาก <https://github.com/Genymobile/scrcpy/releases> แตกไว้ในโฟลเดอร์ชื่อ `scrcpy` ข้างไฟล์ `phone_wall.pyw` (ในนั้นมี adb อยู่แล้ว)
3. ตั้งค่าแต่ละมือถือ (ทำครั้งเดียว)
   1. ตั้งค่า → เกี่ยวกับโทรศัพท์ → แตะ "หมายเลขรุ่น" 7 ครั้ง
   2. ตัวเลือกนักพัฒนา → เปิด **การแก้ปัญหา USB** และ **การแก้ปัญหาไร้สาย**
   3. มือถือกับคอมอยู่ **Wi-Fi เดียวกัน**
   4. ต่อสาย USB แล้วพิมพ์ `scrcpy\adb tcpip 5555` กด "อนุญาต" บนมือถือ แล้วถอดสาย มือถือจะต่อได้ที่ `IP:5555`
      (ดู IP ที่ ตั้งค่า → เกี่ยวกับ → สถานะ) พอร์ตจะหายเมื่อรีบูตเครื่อง ต้องทำซ้ำ
   5. แนะนำให้จอง IP ตายตัวให้แต่ละเครื่องที่เราเตอร์
4. ดับเบิลคลิก `open_panel.bat` ครั้งแรกจะสร้าง `config.json` ให้ กด **เพิ่มเครื่อง** ใส่ชื่อกับ `ip:port` ทีละเครื่อง (หรือแก้ไฟล์ตามตัวอย่างด้านบน) แล้วเปิดแผงใหม่

## วิธีใช้
| ต้องการ | ทำ |
|---|---|
| ดูทุกเครื่อง | เลือกทั้งหมด → เปิดที่เลือก |
| ดูบางเครื่อง | ติ๊กเครื่อง → เปิดที่เลือก |
| ควบคุมเครื่องเดียว | กดปุ่ม "ดูอย่างเดียว" ของเครื่องนั้น |
| ควบคุมหลายเครื่อง | ติ๊ก → คลิก/ลากในกรอบดำ หรือกดปุ่มคีย์/แอป |
| ปิด | ปิดที่เลือก / ปิดทั้งหมด (หน้าต่างไม่มีแถบหัว) |
| ขึ้น "adb ไม่ต่อ" | กด "ต่อ adb ใหม่" |
| ภาพคมขึ้น | เลือกความละเอียด 640/720 (มีผลตอนเปิดจอครั้งถัดไป) |

ข้อจำกัด: group control แตะตามตำแหน่ง ถ้าแอปบนแต่ละเครื่องหน้าตาไม่เหมือนกันอาจแตะไม่ตรงปุ่ม และเครื่องที่ล็อกด้วย PIN ปลดด้วยการปัดไม่ได้

## ใบอนุญาต
MIT (ดูไฟล์ `LICENSE`) scrcpy เป็น Apache-2.0 และไม่ได้รวมมาด้วย
