from django.http import HttpResponse

def robots_txt(request):
    lines = [
        "User-agent: *",
        "Disallow: /admin/",
        "Allow: /",
        "",
        "Sitemap: https://parikshonai.onrender.com/sitemap.xml"
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")

def sitemap_xml(request):
    urls = [
        "/",
        "/utilities/merge/",
        "/utilities/split/",
        "/utilities/protect/",
        "/utilities/unlock/",
        "/utilities/rotate/",
        "/utilities/remove-pages/",
        "/utilities/jpg-to-pdf/",
        "/utilities/pdf-to-jpg/",
        "/utilities/pdf-to-text/",
        "/utilities/watermark/",
        "/utilities/page-numbers/",
        "/utilities/compress/"
    ]
    
    xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    
    base_url = "https://parikshonai.onrender.com"
    
    for url in urls:
        xml.append('  <url>')
        xml.append(f'    <loc>{base_url}{url}</loc>')
        xml.append('    <changefreq>weekly</changefreq>')
        xml.append('    <priority>0.8</priority>')
        xml.append('  </url>')
        
    xml.append('</urlset>')
    
    return HttpResponse("\n".join(xml), content_type="application/xml")
