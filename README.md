# prayer-times 🕌

[العربية](#العربية) | [English](#english)

---

<div dir="rtl">

## العربية

أداة بسيطة بلغة Python تعرض **مواقيت الصلاة لأي مدينة** باستخدام واجهة [aladhan.com](https://aladhan.com/prayer-times-api) المجانية (بدون مفتاح API)، مع صفحة ويب تعمل على GitHub Pages.

### المميزات

- أمر في الطرفية يطبع مواقيت اليوم بالعربي: الفجر، الشروق، الظهر، العصر، المغرب، العشاء.
- يوضّح **الصلاة القادمة والوقت المتبقي** لها حسب التوقيت المحلي للمدينة.
- يقبل أسماء المدن بالعربي (مثل صنعاء، عدن، القاهرة، مكة) أو بالإنجليزي (مثل London).
- صفحة ويب `index.html` بالعربي مع عدّاد تنازلي للصلاة القادمة.
- بدون أي مكتبات خارجية — مكتبة Python القياسية فقط.

### التثبيت

</div>

```bash
git clone https://github.com/ywsfalhajby08-star/prayer-times.git
cd prayer-times
pip install .
```

<div dir="rtl">

### الاستخدام

</div>

```bash
prayer-times صنعاء
```

<div dir="rtl">

مثال على المخرجات:

</div>

```
مواقيت الصلاة في صنعاء
01-11-2026 | 20 جُمادى الأولى 1448 هـ
----------------------------
الفجر    04:30
الشروق   05:50
الظهر    11:55
العصر    15:15  ◀ القادمة
المغرب   18:00
العشاء   19:15
----------------------------
الصلاة القادمة: العصر — بعد 1 ساعة و 10 دقيقة
```

<div dir="rtl">

خيارات إضافية:

- `-m` أو `--method`: رقم طريقة الحساب في aladhan.com (مثلاً `4` = أم القرى، `5` = الهيئة المصرية).
- يمكن أيضاً التشغيل بـ `python -m prayer_times صنعاء`.

### صفحة الويب (GitHub Pages)

الملف `index.html` في جذر المستودع صفحة مستقلة. لتفعيلها: من إعدادات المستودع ← **Pages** ← اختر الفرع `main` والمجلد `/ (root)`. ستكون الصفحة على:
`https://ywsfalhajby08-star.github.io/prayer-times/`

### الاختبارات

</div>

```bash
pip install -e ".[test]"
pytest
```

<div dir="rtl">

### الرخصة

MIT — انظر ملف [LICENSE](LICENSE).

</div>

---

## English

A small Python tool that shows **prayer times for any city** using the free [aladhan.com](https://aladhan.com/prayer-times-api) API (no API key needed), plus an Arabic web page that runs on GitHub Pages.

### Features

- CLI that prints today's times in Arabic: Fajr, Sunrise, Dhuhr, Asr, Maghrib, Isha.
- Shows the **next prayer and the time remaining**, using the city's local time zone.
- Accepts Arabic city names (صنعاء, عدن, القاهرة, …) or English ones (London, Cairo, …).
- `index.html`: an Arabic web page with a live countdown to the next prayer.
- No third-party dependencies — Python standard library only.

### Install

```bash
git clone https://github.com/ywsfalhajby08-star/prayer-times.git
cd prayer-times
pip install .
```

### Usage

```bash
prayer-times صنعاء
```

```bash
prayer-times London --method 3
```

- `-m/--method`: aladhan.com calculation method (e.g. `4` = Umm al-Qura, `3` = Muslim World League).
- Also runnable as `python -m prayer_times <city>`.

### Web page (GitHub Pages)

`index.html` at the repo root is a standalone page. Enable it under **Settings → Pages**, source branch `main`, folder `/ (root)`. It will be served at
`https://ywsfalhajby08-star.github.io/prayer-times/`.

### Tests

```bash
pip install -e ".[test]"
pytest
```

### License

MIT — see [LICENSE](LICENSE).
