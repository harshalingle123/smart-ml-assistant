import re
from typing import List, Dict, Set


class URLExtractorService:
    def __init__(self):
        self.kaggle_patterns = [
            r'https?://(?:www\.)?kaggle\.com/datasets/([^/\s\)]+)/([^/\s\)]+)',
            r'https?://(?:www\.)?kaggle\.com/([^/\s\)]+)/([^/\s\)]+)(?!/datasets)',
        ]
        self.huggingface_pattern = r'https?://huggingface\.co/datasets/([^/\s\)]+/[^/\s\)]+)'

    def extract_dataset_urls(self, response_text: str) -> List[Dict]:
        if not response_text:
            return []

        extracted_datasets = []
        seen_ids: Set[str] = set()

        kaggle_urls = self._extract_kaggle_urls(response_text)
        for url_data in kaggle_urls:
            dataset_id = url_data['id']
            if dataset_id not in seen_ids:
                seen_ids.add(dataset_id)
                extracted_datasets.append(url_data)

        hf_urls = self._extract_huggingface_urls(response_text)
        for url_data in hf_urls:
            dataset_id = url_data['id']
            if dataset_id not in seen_ids:
                seen_ids.add(dataset_id)
                extracted_datasets.append(url_data)

        return extracted_datasets

    def _extract_kaggle_urls(self, text: str) -> List[Dict]:
        datasets = []
        for pattern in self.kaggle_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                if 'datasets' in pattern:
                    username = match.group(1)
                    dataset_name = match.group(2)
                else:
                    username = match.group(1)
                    dataset_name = match.group(2)
                    if username == 'datasets':
                        continue

                dataset_id = self._clean_url_fragment(f"{username}/{dataset_name}")
                full_url = match.group(0)
                full_url = self._clean_url_fragment(full_url)

                datasets.append({
                    'id': dataset_id,
                    'title': dataset_name,
                    'source': 'Kaggle',
                    'url': full_url,
                    'downloads': 0
                })

        return datasets

    def _extract_huggingface_urls(self, text: str) -> List[Dict]:
        datasets = []
        matches = re.finditer(self.huggingface_pattern, text, re.IGNORECASE)

        for match in matches:
            dataset_path = match.group(1)
            dataset_id = self._clean_url_fragment(dataset_path)

            if '/' in dataset_id:
                dataset_name = dataset_id.split('/')[-1]
            else:
                dataset_name = dataset_id

            full_url = match.group(0)
            full_url = self._clean_url_fragment(full_url)

            datasets.append({
                'id': dataset_id,
                'title': dataset_name,
                'source': 'HuggingFace',
                'url': full_url,
                'downloads': 0
            })

        return datasets

    def _clean_url_fragment(self, url: str) -> str:
        url = url.rstrip('.,;:!?)')
        url = url.split('?')[0]
        url = url.split('#')[0]
        return url


url_extractor_service = URLExtractorService()
