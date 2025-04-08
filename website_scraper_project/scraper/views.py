from django.http import JsonResponse
from .website_scraper import Website, summarize_text


def scrape_website(request):
    url = request.GET.get('url')

    if not url:
        return JsonResponse({'error': 'URL parameter is required'}, status=400)

    website = Website(url)

    if website.error:
        return JsonResponse({'error': website.error}, status=400)

    # Scrape the website and summarize its content
    summary = summarize_text(website.get_text())
    company_details = website.get_company_details()

    return JsonResponse({
        'title': website.get_title(),
        'summary': summary,
        'company_details': company_details
    })
