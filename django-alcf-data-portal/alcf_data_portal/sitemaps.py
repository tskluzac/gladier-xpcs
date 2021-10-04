from django.contrib import sitemaps
from django.urls import reverse
from globus_portal_framework.gclients import load_search_client


class MDFSitemap(sitemaps.Sitemap):
    priority = 0.5  # Default
    changefreq = 'always'
    index = "1a57bbe5-5272-477f-9d31-343b8258b7a5"

    def items(self):
        # Perform search for all datasets in MDF index
        client = load_search_client()
        query = {
            "q": "mdf.resource_type:dataset",
            "advanced": True,
            "limit": 10000
        }
        # Unwrap GMeta format, extract just source_id (subject) from each result
        source_ids = []
        for res in client.post_search(self.index, query).data["gmeta"]:
            for con in res["content"]:
                source_ids.append(con["mdf"]["source_id"])
        return source_ids

    def location(self, item):
        return reverse("detail", kwargs={"index": "mdf", "subject": item})
