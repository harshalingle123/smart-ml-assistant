import os
import sys
import json
import re
import google.generativeai as genai
from huggingface_hub import HfApi, snapshot_download
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Tuple
from dotenv import load_dotenv

# Fix encoding issues on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# ==========================================
# 1. AUTHENTICATION & CONFIGURATION
# ==========================================

# Load environment variables from backend/.env
load_dotenv('backend/.env')

# [KAGGLE]
os.environ['KAGGLE_CONFIG_DIR'] = os.getcwd()

# Create kaggle.json for authentication
kaggle_config = {
    "username": os.getenv("KAGGLE_USERNAME"),
    "key": os.getenv("KAGGLE_KEY")
}
os.makedirs(os.path.expanduser('~/.kaggle'), exist_ok=True)
with open(os.path.expanduser('~/.kaggle/kaggle.json'), 'w') as f:
    json.dump(kaggle_config, f)
os.chmod(os.path.expanduser('~/.kaggle/kaggle.json'), 0o600)

from kaggle.api.kaggle_api_extended import KaggleApi

# [GEMINI & HUGGING FACE]
# ⚠️ USE ENVIRONMENT VARIABLES FOR SECURITY
GOOGLE_API_KEY = os.getenv("GOOGLE_GEMINI_API_KEY")  # Updated to match .env file
HF_TOKEN = os.getenv("HF_TOKEN")

if not GOOGLE_API_KEY:
    raise ValueError("Please set GOOGLE_API_KEY environment variable")
if not HF_TOKEN:
    raise ValueError("Please set HF_TOKEN environment variable")

genai.configure(api_key=GOOGLE_API_KEY)

# ==========================================
# 2. LOGIC PIPELINE
# ==========================================

def extract_spec(user_query: str) -> Dict:
    """Uses Gemini to fix typos and extract search keywords."""
    print(f"Analyzing query: '{user_query}'...")
    try:
        # FIXED: Use correct model name
        model = genai.GenerativeModel('gemini-2.0-flash-exp')

        prompt = f"""
        Act as a search query optimizer for a dataset recommendation engine.

        Task:
        1. Analyze the User Query: "{user_query}"
        2. Fix any spelling mistakes (e.g., "dibetes" -> "diabetes", "santiment" -> "sentiment", "analussi" -> "analysis").

        Return ONLY valid JSON with no markdown formatting:
        {{
            "fixed_query": "corrected query string",
            "keywords": ["keyword1", "keyword2", "keyword3"]
        }}
        """

        response = model.generate_content(prompt)
        text_resp = response.text.strip()

        # Remove markdown code blocks if present
        text_resp = text_resp.replace('```json', '').replace('```', '').strip()

        result = json.loads(text_resp)
        print(f"✓ Fixed query: '{result.get('fixed_query', user_query)}'")
        print(f"✓ Keywords: {result.get('keywords', [])}")
        return result

    except Exception as e:
        print(f"⚠ Gemini Extraction Warning: {e}")
        # Fallback to original query if LLM fails
        return {"fixed_query": user_query, "keywords": [user_query]}


def extract_urls_from_text(text: str) -> List[Tuple[str, str]]:
    """
    Extracts Kaggle and HuggingFace dataset URLs from text.
    Returns list of tuples: (source, dataset_id)
    """
    extracted = []
    seen = set()  # Track unique dataset IDs

    # Kaggle URL patterns - matches both with and without http://
    # Matches:
    # - https://www.kaggle.com/datasets/username/dataset-name
    # - https://kaggle.com/datasets/username/dataset-name
    # - www.kaggle.com/datasets/username/dataset-name
    # - kaggle.com/datasets/username/dataset-name
    kaggle_pattern = r'(?:https?://)?(?:www\.)?kaggle\.com/datasets/([a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+)'

    kaggle_matches = re.findall(kaggle_pattern, text, re.IGNORECASE)
    for match in kaggle_matches:
        # Clean up the match
        dataset_id = match.strip().rstrip('.,;:!?)')
        if dataset_id not in seen:
            seen.add(dataset_id)
            extracted.append(("Kaggle", dataset_id))

    # HuggingFace URL patterns - matches both with and without http://
    # Matches:
    # - https://huggingface.co/datasets/username/dataset-name
    # - huggingface.co/datasets/username/dataset-name
    hf_pattern = r'(?:https?://)?huggingface\.co/datasets/([a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+)'

    hf_matches = re.findall(hf_pattern, text, re.IGNORECASE)
    for match in hf_matches:
        # Clean up the match
        dataset_id = match.strip().rstrip('.,;:!?)')
        if dataset_id not in seen:
            seen.add(dataset_id)
            extracted.append(("HuggingFace", dataset_id))

    return extracted


def process_urls(text: str) -> List[Dict]:
    """
    Processes text with URLs and returns dataset information.
    """
    urls = extract_urls_from_text(text)

    if not urls:
        print("⚠ No valid Kaggle or HuggingFace dataset URLs found in the text.")
        return []

    print(f"✓ Found {len(urls)} dataset URL(s):")

    datasets = []
    for source, dataset_id in urls:
        if source == "Kaggle":
            url = f"https://www.kaggle.com/datasets/{dataset_id}"
            print(f"  - [Kaggle] {dataset_id}")
        else:  # HuggingFace
            url = f"https://huggingface.co/datasets/{dataset_id}"
            print(f"  - [HuggingFace] {dataset_id}")

        datasets.append({
            "id": dataset_id,
            "title": dataset_id.split('/')[-1],
            "description": f"Dataset from {source}",
            "source": source,
            "url": url,
            "downloads": "N/A"
        })

    return datasets


def search_apis(keywords: List[str]) -> List[Dict]:
    """Searches Kaggle and Hugging Face."""
    candidates = []
    search_term = " ".join(keywords)
    print(f"\nSearching for: '{search_term}'...")

    # --- 1. Kaggle Search ---
    try:
        k_api = KaggleApi()
        k_api.authenticate()

        k_datasets = k_api.dataset_list(search=search_term, sort_by='votes', page=1)

        for d in k_datasets[:15]:
            candidates.append({
                "id": d.ref,
                "title": d.title,
                "description": getattr(d, 'description', '') or d.title,
                "source": "Kaggle",
                "url": f"https://www.kaggle.com/datasets/{d.ref}",
                "downloads": getattr(d, 'downloadCount', 0)
            })
        print(f"✓ Found {len(candidates)} from Kaggle.")

    except Exception as e:
        print(f"✗ Kaggle Search Failed: {e}")

    # --- 2. Hugging Face Search ---
    try:
        hf_api = HfApi(token=HF_TOKEN)
        hf_datasets = hf_api.list_datasets(
            search=search_term,
            limit=15,
            sort="downloads",
            direction=-1
        )

        hf_count = 0
        for d in hf_datasets:
            candidates.append({
                "id": d.id,
                "title": d.id.split('/')[-1],
                "description": getattr(d, 'description', '') or d.id,
                "source": "HuggingFace",
                "url": f"https://huggingface.co/datasets/{d.id}",
                "downloads": getattr(d, 'downloads', 0)
            })
            hf_count += 1
        print(f"✓ Found {hf_count} from Hugging Face.")

    except Exception as e:
        print(f"✗ HF Search Failed: {e}")

    return candidates


def rank_candidates(query: str, candidates: List[Dict]) -> List[Dict]:
    """Ranks datasets using Gemini Embeddings."""
    if not candidates:
        return []

    print("\nRanking candidates using embeddings...")
    try:
        # 1. Embed Query
        query_emb = genai.embed_content(
            model="models/text-embedding-004",
            content=query,
            task_type="retrieval_query"
        )['embedding']

        # 2. Embed Candidates
        texts = [f"{c['title']}: {str(c['description'])[:500]}" for c in candidates]

        batch_emb = genai.embed_content(
            model="models/text-embedding-004",
            content=texts,
            task_type="retrieval_document"
        )['embedding']

        # 3. Compute Similarity
        scores = cosine_similarity([query_emb], batch_emb)[0]

        for idx, score in enumerate(scores):
            candidates[idx]['score'] = float(score)

        # Sort descending
        return sorted(candidates, key=lambda x: x['score'], reverse=True)

    except Exception as e:
        print(f"⚠ Ranking failed: {e}")
        print("Returning unranked results...")
        return candidates


def download_kaggle_dataset(dataset_id: str, download_path: str = "./downloads"):
    """Downloads a Kaggle dataset."""
    try:
        print(f"\n📥 Downloading Kaggle dataset: {dataset_id}")
        k_api = KaggleApi()
        k_api.authenticate()

        # Create download directory if it doesn't exist
        os.makedirs(download_path, exist_ok=True)

        # Download dataset
        k_api.dataset_download_files(dataset_id, path=download_path, unzip=True)
        print(f"✓ Successfully downloaded to: {download_path}/{dataset_id.split('/')[-1]}")
        return True

    except Exception as e:
        print(f"✗ Failed to download Kaggle dataset: {e}")
        return False


def download_huggingface_dataset(dataset_id: str, download_path: str = "./downloads"):
    """Downloads a Hugging Face dataset."""
    try:
        print(f"\n📥 Downloading HuggingFace dataset: {dataset_id}")

        # Create download directory if it doesn't exist
        dataset_folder = os.path.join(download_path, dataset_id.replace('/', '_'))
        os.makedirs(dataset_folder, exist_ok=True)

        # Download dataset using snapshot_download
        snapshot_download(
            repo_id=dataset_id,
            repo_type="dataset",
            local_dir=dataset_folder,
            token=HF_TOKEN
        )
        print(f"✓ Successfully downloaded to: {dataset_folder}")
        return True

    except Exception as e:
        print(f"✗ Failed to download HuggingFace dataset: {e}")
        return False


def confirm_and_download(top_datasets: List[Dict]):
    """Allows user to select and download datasets."""
    print("\n" + "="*60)
    print("📦 DOWNLOAD OPTIONS")
    print("="*60)
    print("\nWould you like to download any of these datasets?")
    print("Enter the numbers separated by commas (e.g., 1,3,5) or 'all' for all datasets")
    print("Enter 'n' or 'no' to skip downloading")

    user_input = input("\nYour selection: ").strip().lower()

    if user_input in ['n', 'no', '']:
        print("\n✓ Skipping downloads. Exiting.")
        return

    # Parse selection
    if user_input == 'all':
        selected_indices = list(range(len(top_datasets)))
    else:
        try:
            selected_indices = [int(x.strip()) - 1 for x in user_input.split(',')]
            # Validate indices
            selected_indices = [i for i in selected_indices if 0 <= i < len(top_datasets)]
        except ValueError:
            print("✗ Invalid input. Skipping downloads.")
            return

    if not selected_indices:
        print("✗ No valid selections. Exiting.")
        return

    # Confirm download path
    download_path = input("\nEnter download directory path (press Enter for './downloads'): ").strip()
    if not download_path:
        download_path = "./downloads"

    print(f"\n📂 Download location: {download_path}")
    print("="*60)

    # Download selected datasets
    success_count = 0
    fail_count = 0

    for idx in selected_indices:
        dataset = top_datasets[idx]
        print(f"\n[{idx + 1}] Processing: {dataset['title']} ({dataset['source']})")

        if dataset['source'] == 'Kaggle':
            if download_kaggle_dataset(dataset['id'], download_path):
                success_count += 1
            else:
                fail_count += 1

        elif dataset['source'] == 'HuggingFace':
            if download_huggingface_dataset(dataset['id'], download_path):
                success_count += 1
            else:
                fail_count += 1

    # Summary
    print("\n" + "="*60)
    print("📊 DOWNLOAD SUMMARY")
    print("="*60)
    print(f"✓ Successfully downloaded: {success_count}")
    print(f"✗ Failed: {fail_count}")
    print(f"📂 Location: {os.path.abspath(download_path)}")
    print("="*60)


def main():
    print("="*60)
    print("🤖 SMART ML DATASET SEARCH & DOWNLOAD")
    print("="*60)
    print("\nChoose mode:")
    print("1. Search datasets by keywords")
    print("2. Extract and download from URLs")

    mode = input("\nEnter mode (1 or 2): ").strip()

    if mode == "2":
        # URL Extraction Mode
        print("\n" + "="*60)
        print("📋 URL EXTRACTION MODE")
        print("="*60)
        print("\nPaste text containing Kaggle or HuggingFace dataset URLs.")
        print("Supported formats:")
        print("  - https://www.kaggle.com/datasets/username/dataset-name")
        print("  - https://huggingface.co/datasets/username/dataset-name")
        print("\nEnter your text (type 'END' on a new line when done):")

        lines = []
        while True:
            line = input()
            if line.strip().upper() == "END":
                break
            lines.append(line)

        text = "\n".join(lines)

        if not text.strip():
            print("Empty input. Exiting.")
            return

        # Extract URLs and process
        datasets = process_urls(text)

        if not datasets:
            print("\n❌ No valid dataset URLs found. Exiting.")
            return

        # Display found datasets
        print("\n" + "="*60)
        print("📦 EXTRACTED DATASETS")
        print("="*60)

        for i, d in enumerate(datasets, 1):
            print(f"\n{i}. [{d['source']}] {d['title']}")
            print(f"   ID: {d['id']}")
            print(f"   URL: {d['url']}")

        print("\n" + "="*60)

        # Download confirmation
        confirm_and_download(datasets)

    else:
        # Search Mode (default)
        print("\n" + "="*60)
        print("🔍 SEARCH MODE")
        print("="*60)

        user_query = input("\nEnter your dataset requirement: ")
        if not user_query.strip():
            print("Empty query. Exiting.")
            return

        # 1. Spec Extraction (Fixes Typos -> Keywords)
        spec = extract_spec(user_query)

        # 2. Search APIs
        keywords = spec.get('keywords', [user_query])
        candidates = search_apis(keywords)

        if not candidates:
            print("\n❌ No datasets found. Try different keywords.")
            return

        # 3. Semantic Ranking
        query_for_ranking = spec.get('fixed_query', user_query)
        top_datasets = rank_candidates(query_for_ranking, candidates)

        # 4. Display Results
        print("\n" + "="*60)
        print("🏆 TOP 5 RECOMMENDED DATASETS")
        print("="*60)

        for i, d in enumerate(top_datasets[:5], 1):
            score_display = f"{d.get('score', 0):.4f}" if 'score' in d else "N/A"
            print(f"\n{i}. [{d['source']}] {d['title']}")
            print(f"   Relevance Score: {score_display}")
            print(f"   Downloads: {d.get('downloads', 'N/A')}")
            print(f"   URL: {d['url']}")

        print("\n" + "="*60)

        # 5. Download Confirmation
        confirm_and_download(top_datasets[:5])


if __name__ == "__main__":
    main()
