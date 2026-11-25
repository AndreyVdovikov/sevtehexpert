#!/usr/bin/env python3
"""Сборка блога sevtehexpert.ru из data/blog.json.

Запуск из корня репозитория:  python3 tools/build_blog.py
Создаёт blog/index.html, blog/<slug>/index.html, blog.css и обновляет sitemap.xml.
Формат статьи в blog.json: id, pub (ГГГГ-ММ-ДД), slug, title, og (картинка-обложка),
cat (build | auto), blocks — список [тип, текст], где тип: p, h2, h3, li, blockquote, img, cap.
"""
import html
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://sevtehexpert.ru"
TG_TOKEN = "9014388871:AAGUAE92YmzeiHbgUIeOsInXpqimsHd2isU"
TG_CHAT = "670836035"
MONTHS = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля",
          "августа", "сентября", "октября", "ноября", "декабря"]
CATS = {"build": "Строительная экспертиза", "auto": "Автоэкспертиза"}

e = lambda s: html.escape(str(s), quote=True)


def ru_date(iso):
    y, m, d = iso.split("-")
    return f"{int(d)} {MONTHS[int(m) - 1]} {y}"


def excerpt(art, n=170):
    for k, v in art["blocks"]:
        if k == "p" and len(v) > 60:
            v = re.sub(r"\s+", " ", v)
            return v if len(v) <= n else v[:n].rsplit(" ", 1)[0] + "…"
    return art["title"]


def cover(art):
    for k, v in art["blocks"]:
        if k == "img":
            return v
    return art["og"]


def img_tag(src, alt, cls="", eager=False):
    load = 'fetchpriority="high"' if eager else 'loading="lazy"'
    return (f'<img src="{e(src)}" alt="{e(alt)}" {load} decoding="async" '
            f'referrerpolicy="no-referrer"{f" class=\"{cls}\"" if cls else ""}>')


def body_html(art):
    out, in_list, first_img = [], False, True
    blocks = art["blocks"]
    for i, (k, v) in enumerate(blocks):
        if k != "li" and in_list:
            out.append("</ul>")
            in_list = False
        if k == "img":
            cap = blocks[i + 1][1] if i + 1 < len(blocks) and blocks[i + 1][0] == "cap" else art["title"]
            out.append(f"<figure>{img_tag(v, cap, eager=first_img)}"
                       + (f"<figcaption>{e(cap)}</figcaption>" if cap != art["title"] else "")
                       + "</figure>")
            first_img = False
        elif k == "cap":
            continue
        elif k == "li":
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{e(v)}</li>")
        elif k in ("h2", "h3", "p", "blockquote"):
            out.append(f"<{k}>{e(v)}</{k}>")
    if in_list:
        out.append("</ul>")
    return "\n".join(out)


HEAD = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{url}">
<link rel="icon" href="/logo.png">
<meta property="og:type" content="{ogtype}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{ogimg}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/blog.css">
{extra}
</head>
<body>
<header><div class="wrap nav">
  <a class="brand" href="/"><img src="/logo.png" alt="Эмблема Севтехэксперт" width="46" height="46"><span><b>СЕВТЕХЭКСПЕРТ</b><small>Независимая экспертиза</small></span></a>
  <nav class="links"><a href="/#services">Услуги</a><a href="/#prices">Цены</a><a href="/blog/">Блог</a><a href="/#contact">Контакты</a></nav>
  <a class="btn sm" href="tel:+79782152598">+7 978 215-25-98</a>
</div></header>
"""

FOOT = """
<footer><div class="wrap fbot">
  <span>© 2026 ООО «Севтехэксперт» · Севастополь, проспект Нахимова, 15</span>
  <span><a href="/">Главная</a> · <a href="/blog/">Блог</a> · <a href="https://dzen.ru/sevtehexp" target="_blank" rel="noopener">Мы на Дзене</a></span>
</div></footer>
</body>
</html>
"""

FORM = """
<aside class="cta" id="lead">
  <div>
    <h2>Нужна экспертиза?</h2>
    <p>Оставьте телефон: эксперт перезвонит, разберёт вашу ситуацию и назовёт стоимость. Можно сразу написать в <a href="https://wa.me/79782152598" target="_blank" rel="noopener">WhatsApp</a> или <a href="https://t.me/VdovikovZen" target="_blank" rel="noopener">Telegram</a>.</p>
  </div>
  <form id="f" novalidate>
    <input name="website" tabindex="-1" autocomplete="off" aria-hidden="true" class="hp">
    <input name="name" placeholder="Ваше имя" autocomplete="name">
    <input name="phone" type="tel" placeholder="+7 (___) ___-__-__" autocomplete="tel" required>
    <button class="btn" type="submit">Получить консультацию</button>
    <p class="fine">Нажимая кнопку, вы соглашаетесь с политикой обработки персональных данных</p>
    <div class="msg" hidden></div>
  </form>
</aside>
<script>
{
const f=document.getElementById('f');
f.addEventListener('submit',async ev=>{ev.preventDefault();
 const ph=f.phone.value;if(ph.replace(/\\D/g,'').length<10){f.phone.classList.add('err');setTimeout(()=>f.phone.classList.remove('err'),2500);return}
 if(f.website.value)return;
 const b=f.querySelector('button');b.disabled=true;
 const text=['📩 Заявка с сайта Севтехэксперт (блог)','Телефон: '+ph,f.name.value&&'Имя: '+f.name.value,'Статья: '+document.title,'Страница: '+location.pathname].filter(Boolean).join('\\n');
 let ok=true;try{await fetch('https://api.telegram.org/bot__TOKEN__/sendMessage',{method:'POST',mode:'no-cors',body:new URLSearchParams({chat_id:'__CHAT__',text})})}catch(e){ok=false}
 const m=f.querySelector('.msg');m.hidden=false;m.textContent=ok?'Спасибо! Заявка отправлена, эксперт скоро свяжется с вами.':'Не получилось отправить. Позвоните или напишите в WhatsApp: +7 978 215-25-98';
 b.disabled=false;if(ok)f.reset()});
}
</script>
""".replace("__TOKEN__", TG_TOKEN).replace("__CHAT__", TG_CHAT)


def card(a):
    return (f'<article class="card"><a href="/blog/{a["slug"]}/">'
            f'<div class="ph">{img_tag(cover(a), a["title"])}</div>'
            f'<div class="cb"><span class="meta">{CATS[a["cat"]]} · {ru_date(a["pub"])}</span>'
            f'<h3>{e(a["title"])}</h3><p>{e(excerpt(a, 140))}</p></div></a></article>')


def build():
    arts = json.load(open(os.path.join(ROOT, "data", "blog.json"), encoding="utf-8"))
    arts.sort(key=lambda a: a["pub"], reverse=True)
    os.makedirs(os.path.join(ROOT, "blog"), exist_ok=True)

    # список статей
    url = f"{SITE}/blog/"
    filt = '<div class="tabs" role="tablist"><button aria-selected="true" data-c="all">Все статьи</button>' + "".join(
        f'<button aria-selected="false" data-c="{k}">{v}</button>' for k, v in CATS.items()) + "</div>"
    cards = "\n".join(f'<div data-cat="{a["cat"]}">{card(a)}</div>' for a in arts)
    page = HEAD.format(title="Блог о строительной экспертизе и автоэкспертизе — Севтехэксперт",
                       desc="Статьи эксперта: что делать после залива, как проходит строительная экспертиза, чем досудебная экспертиза отличается от судебной, как страховые занижают ущерб после ДТП.",
                       url=url, ogtype="website", ogimg=f"{SITE}/logo.png", extra="")
    page += f"""<main>
<section class="hero"><div class="wrap">
  <nav class="crumbs"><a href="/">Главная</a> / Блог</nav>
  <h1>Блог эксперта</h1>
  <p class="lead">Разбираем заливы, некачественный ремонт, приёмку квартир и споры со страховыми после ДТП. Пишем по своей практике в Севастополе, Крыму и Краснодарском крае.</p>
</div></section>
<section class="band"><div class="wrap">
{filt}
<div class="grid" id="grid">
{cards}
</div>
</div></section>
</main>
<script>
{{const bs=[...document.querySelectorAll('.tabs button')];bs.forEach(b=>b.addEventListener('click',()=>{{bs.forEach(x=>x.setAttribute('aria-selected',x===b));document.querySelectorAll('#grid>div').forEach(d=>d.hidden=b.dataset.c!=='all'&&d.dataset.cat!==b.dataset.c)}}))}}
</script>
{FOOT}"""
    open(os.path.join(ROOT, "blog", "index.html"), "w", encoding="utf-8").write(page)

    # страницы статей
    for i, a in enumerate(arts):
        url = f"{SITE}/blog/{a['slug']}/"
        desc = excerpt(a)
        ld = {"@context": "https://schema.org", "@type": "Article", "headline": a["title"][:110],
              "datePublished": a["pub"], "image": [cover(a)], "inLanguage": "ru",
              "author": {"@type": "Organization", "name": "ООО «Севтехэксперт»", "url": SITE},
              "publisher": {"@type": "Organization", "name": "ООО «Севтехэксперт»",
                            "logo": {"@type": "ImageObject", "url": f"{SITE}/logo.png"}},
              "mainEntityOfPage": url}
        extra = '<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False).replace("</", "<\\/") + "</script>"
        related = [x for x in arts if x["cat"] == a["cat"] and x["slug"] != a["slug"]][:3]
        page = HEAD.format(title=e(a["title"]) + " — Севтехэксперт", desc=e(desc), url=url,
                           ogtype="article", ogimg=e(cover(a)), extra=extra)
        page += f"""<main>
<article class="post"><div class="wrap narrow">
  <nav class="crumbs"><a href="/">Главная</a> / <a href="/blog/">Блог</a> / {CATS[a['cat']]}</nav>
  <h1>{e(a['title'])}</h1>
  <p class="meta">{CATS[a['cat']]} · <time datetime="{a['pub']}">{ru_date(a['pub'])}</time></p>
  <div class="content">
{body_html(a)}
  </div>
{FORM}
</div></article>
<section class="band ice"><div class="wrap">
  <h2>Читайте также</h2>
  <div class="grid">{''.join(card(x) for x in related)}</div>
  <p style="margin-top:24px"><a class="btn line" href="/blog/">Все статьи блога</a></p>
</div></section>
</main>
{FOOT}"""
        d = os.path.join(ROOT, "blog", a["slug"])
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(page)

    # sitemap
    urls = [(f"{SITE}/", "1.0", None), (f"{SITE}/blog/", "0.8", None)] + \
           [(f"{SITE}/blog/{a['slug']}/", "0.7", a["pub"]) for a in arts]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u, p, lm in urls:
        sm.append(f"  <url><loc>{u}</loc>" + (f"<lastmod>{lm}</lastmod>" if lm else "") + f"<priority>{p}</priority></url>")
    sm.append("</urlset>")
    open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8").write("\n".join(sm) + "\n")
    print(f"Готово: {len(arts)} статей")


if __name__ == "__main__":
    build()
