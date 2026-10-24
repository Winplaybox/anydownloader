import os
import yaml
from datetime import datetime

ROOT_DIR = r"C:\Users\sagar\Desktop\Project\anydownloader"
PLATFORMS_FILE = os.path.join(ROOT_DIR, "backend", "platforms.yaml")
if not os.path.exists(PLATFORMS_FILE):
    PLATFORMS_FILE = os.path.join(ROOT_DIR, "platforms.yaml")

SITEMAP_FILE = os.path.join(ROOT_DIR, "sitemap.xml")
BASE_URL = "https://ovd.winplaybox.in"

def load_platforms():
    if not os.path.exists(PLATFORMS_FILE):
        return []
    with open(PLATFORMS_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("platforms", [])
    return []

def generate_sitemap(platforms):
    today = datetime.now().strftime("%Y-%m-%d")
    
    urls = [
        {"loc": f"{BASE_URL}/", "priority": "1.0", "changefreq": "daily"},
        {"loc": f"{BASE_URL}/blog", "priority": "0.8", "changefreq": "weekly"},
        {"loc": f"{BASE_URL}/updates", "priority": "0.8", "changefreq": "weekly"},
    ]

    seen_slugs = set(["", "blog", "updates"])

    for p in platforms:
        seo = p.get("seo", {})
        slug = seo.get("slug")
        if slug and slug not in seen_slugs:
            urls.append({"loc": f"{BASE_URL}/{slug}", "priority": "0.9", "changefreq": "daily"})
            seen_slugs.add(slug)

        # Content-type subroutes
        p_id = p.get("id")
        content_types = p.get("contentTypes", [])
        for ct in content_types:
            if ct in ("video", "short", "reel", "post", "slideshow", "carousel", "thumbnails", "image"):
                sub_slug = f"{p_id}-{ct}-downloader"
                if ct == "short":
                    sub_slug = f"{p_id}-shorts-downloader"
                elif ct == "reel":
                    sub_slug = f"{p_id}-reels-downloader"
                elif ct == "thumbnails":
                    sub_slug = f"{p_id}-thumbnail-downloader"
                elif ct == "image":
                    sub_slug = f"{p_id}-image-downloader"

                if sub_slug not in seen_slugs:
                    urls.append({"loc": f"{BASE_URL}/{sub_slug}", "priority": "0.9", "changefreq": "daily"})
                    seen_slugs.add(sub_slug)

    # Static legal routes
    for legal in ["privacy", "terms", "dmca", "contact"]:
        if legal not in seen_slugs:
            urls.append({"loc": f"{BASE_URL}/{legal}", "priority": "0.6", "changefreq": "monthly"})
            seen_slugs.add(legal)

    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    ]
    for u in urls:
        xml_lines.append("  <url>")
        xml_lines.append(f"    <loc>{u['loc']}</loc>")
        xml_lines.append(f"    <lastmod>{today}</lastmod>")
        xml_lines.append(f"    <changefreq>{u['changefreq']}</changefreq>")
        xml_lines.append(f"    <priority>{u['priority']}</priority>")
        xml_lines.append("  </url>")
    xml_lines.append("</urlset>")
    xml_content = "\n".join(xml_lines) + "\n"

    with open(SITEMAP_FILE, "w", encoding="utf-8") as f:
        f.write(xml_content)

    # Also copy script to scripts/generate_seo_pages.py
    script_target = os.path.join(ROOT_DIR, "scripts", "generate_seo_pages.py")
    with open(__file__, "r", encoding="utf-8") as f_src:
        with open(script_target, "w", encoding="utf-8") as f_dst:
            f_dst.write(f_src.read())

    print(f"Generated {len(urls)} sitemap entries from platforms.yaml into sitemap.xml")

if __name__ == "__main__":
    platforms = load_platforms()
    generate_sitemap(platforms)
