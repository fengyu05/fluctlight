from serpapi import GoogleSearch
from fluctlight.settings import SERP_API_KEY
from fluctlight.search.data_model import SearchResult, SearchParameters


class SerpApiClient:
    def __init__(self, api_key: str = SERP_API_KEY):
        self.api_key = api_key
        # self.web_page_reader = SimpleWebPageReader()

    def search(self, request: SearchParameters) -> SearchResult:
        params = request.model_dump(by_alias=True)
        params["api_key"] = self.api_key
        search = GoogleSearch(params)
        search_result = SearchResult(**search.get_dict())
        # Fetch and inject content for each organic result
        # for result in search_result.organic_results:
        #     self.web_page_reader.load_data(urls=[result.link])

        return search_result

    def simple_search(self, query: str) -> SearchResult:
        request = SearchParameters(q=query)
        return self.search(request)


if __name__ == "__main__":
    request = SearchParameters(q="coffee")
    client = SerpApiClient()
    response = client.search(request)
    print(response)
