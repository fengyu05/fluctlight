import unittest
from unittest.mock import patch, MagicMock
from fluctlight.search.client import SerpApiClient, SearchParameters, SearchResult


class TestSerpApiClient(unittest.TestCase):
    @patch("fluctlight.search.client.GoogleSearch")
    def test_search(self, mock_google_search):
        mock_search_instance = MagicMock()
        mock_search_instance.get_dict.return_value = {
            "search_metadata": {
                "id": "679fbeb4931dfa210a6dcaff",
                "status": "Success",
                "json_endpoint": "https://serpapi.com/searches/3a2af076dc153d9a/679fbeb4931dfa210a6dcaff.json",
                "created_at": "2025-02-02 18:51:32 UTC",
                "processed_at": "2025-02-02 18:51:32 UTC",
                "google_url": "https://www.google.com/search?q=deepseek&oq=deepseek&uule=w+CAIQICIaQXVzdGluLFRleGFzLFVuaXRlZCBTdGF0ZXM&hl=en&gl=us&num=2&sourceid=chrome&ie=UTF-8",
                "raw_html_file": "https://serpapi.com/searches/3a2af076dc153d9a/679fbeb4931dfa210a6dcaff.html",
                "total_time_taken": 1.01,
            },
            "search_parameters": {
                "engine": "google",
                "q": "deepseek",
                "location_requested": "Austin, Texas, United States",
                "location_used": "Austin,Texas,United States",
                "google_domain": "google.com",
                "hl": "en",
                "gl": "us",
                "num": "2",
                "device": "desktop",
            },
            "search_information": {
                "query_displayed": "deepseek",
                "total_results": 384000000,
                "time_taken_displayed": 0.28,
                "organic_results_state": "Results for exact spelling",
            },
            "knowledge_graph": {
                "title": "DeepSeek",
                "type": "IT company",
                "entity_type": "companies, company",
                "kgmid": "/g/11wxpfc4h2",
                "knowledge_graph_search_link": "https://www.google.com/search?kgmid=/g/11wxpfc4h2&hl=en-US&q=DeepSeek",
                "serpapi_knowledge_graph_search_link": "https://serpapi.com/search.json?device=desktop&engine=google&gl=us&google_domain=google.com&hl=en-US&kgmid=%2Fg%2F11wxpfc4h2&location=Austin%2C+Texas%2C+United+States&num=2&q=DeepSeek",
                "founded": "May 2023",
                "number_of_employees": "Under 200",
                "owner": "High-Flyer",
                "owner_links": [
                    {
                        "text": "High-Flyer",
                        "link": "https://www.google.com/search?num=2&sca_esv=22c69e882f91db0f&hl=en&gl=us&q=High-Flyer&stick=H4sIAAAAAAAAAONgVuLVT9c3NCwpL8jKzc2uXMTK5ZGZnqHrllOZWgQAXOk19x4AAAA&sa=X&ved=2ahUKEwiWkvSd1KWLAxVZ6ckDHTMVAecQmxMoAHoECCoQAg",
                    }
                ],
            },
            "organic_results": [
                {
                    "position": 1,
                    "title": "DeepSeek",
                    "link": "https://www.deepseek.com/",
                    "redirect_link": "https://www.google.com/url?sa=t&source=web&rct=j&opi=89978449&url=https://www.deepseek.com/&ved=2ahUKEwiWkvSd1KWLAxVZ6ckDHTMVAecQFnoECCAQAQ",
                    "displayed_link": "https://www.deepseek.com",
                    "favicon": "https://serpapi.com/searches/679fbeb4931dfa210a6dcaff/images/41daea9292c337d410ca471d554497a1e3baf80fe3db5807a61464e18f999f9d.png",
                    "snippet": "DeepSeek-R1 is now live and open source, rivaling OpenAI's Model o1. Available on web, app, and API. Click for details.",
                    "snippet_highlighted_words": [
                        "DeepSeek-R1 is now live and open source"
                    ],
                    "source": "DeepSeek",
                }
            ],
            "related_searches": [
                {
                    "block_position": 1,
                    "query": "DeepSeek Founder",
                    "link": "https://www.google.com/search?num=2&sca_esv=22c69e882f91db0f&hl=en&gl=us&q=DeepSeek+Founder&sa=X&ved=2ahUKEwiWkvSd1KWLAxVZ6ckDHTMVAecQ1QJ6BAgREAE",
                    "serpapi_link": "https://serpapi.com/search.json?device=desktop&engine=google&gl=us&google_domain=google.com&hl=en&location=Austin%2C+Texas%2C+United+States&num=2&q=DeepSeek+Founder",
                }
            ],
            "pagination": {
                "current": 1,
                "next": "https://www.google.com/search?q=deepseek&num=2&sca_esv=22c69e882f91db0f&hl=en&gl=us&ei=tb6fZ9bjHtnSp84Ps6qEuA4&start=2&sa=N&sstk=Af40H4X_dqNfjRJJK3QCFXUPXn8PqcjF_NQnaKMTIyA8OimZIuciHQxZ7vMrp8slHXA9Q_XVQHheRoUnoWFcGz7nKZGvqEWoYsubiA&ved=2ahUKEwiWkvSd1KWLAxVZ6ckDHTMVAecQ8NMDegQIBhAW",
                "other_pages": {
                    "2": "https://www.google.com/search?q=deepseek&num=2&sca_esv=22c69e882f91db0f&hl=en&gl=us&ei=tb6fZ9bjHtnSp84Ps6qEuA4&start=2&sa=N&sstk=Af40H4X_dqNfjRJJK3QCFXUPXn8PqcjF_NQnaKMTIyA8OimZIuciHQxZ7vMrp8slHXA9Q_XVQHheRoUnoWFcGz7nKZGvqEWoYsubiA&ved=2ahUKEwiWkvSd1KWLAxVZ6ckDHTMVAecQ8tMDegQIBhAE"
                },
            },
            "serpapi_pagination": {
                "current": 1,
                "next_link": "https://serpapi.com/search.json?device=desktop&engine=google&gl=us&google_domain=google.com&hl=en&location=Austin%2C+Texas%2C+United+States&num=2&q=deepseek&start=2",
                "next": "https://serpapi.com/search.json?device=desktop&engine=google&gl=us&google_domain=google.com&hl=en&location=Austin%2C+Texas%2C+United+States&num=2&q=deepseek&start=2",
                "other_pages": {
                    "2": "https://serpapi.com/search.json?device=desktop&engine=google&gl=us&google_domain=google.com&hl=en&location=Austin%2C+Texas%2C+United+States&num=2&q=deepseek&start=2"
                },
            },
        }
        mock_google_search.return_value = mock_search_instance

        client = SerpApiClient(api_key="test_api_key")
        request = SearchParameters(
            q="deepseek", location="Austin,Texas", api_key="test_api_key"
        )
        search_result: SearchResult = client.search(request)

        self.assertEqual(search_result.search_metadata.id, "679fbeb4931dfa210a6dcaff")
        self.assertEqual(search_result.search_parameters.q, "deepseek")
        self.assertEqual(search_result.knowledge_graph.title, "DeepSeek")
        self.assertEqual(search_result.organic_results[0].title, "DeepSeek")


if __name__ == "__main__":
    unittest.main()
