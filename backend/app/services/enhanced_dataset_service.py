import os
import json
import logging
from typing import List, Dict, Optional, Any
import asyncio
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import google.generativeai as genai
from app.core.config import settings
from app.services.kaggle_service import kaggle_service
from app.services.huggingface_service import huggingface_service

logger = logging.getLogger(__name__)

class EnhancedDatasetService:
    """
    Enhanced dataset search service that uses Gemini for:
    1. Query correction and keyword extraction
    2. Semantic ranking using embeddings
    3. Generating proper download URLs
    """
    
    def __init__(self):
        self.gemini_configured = bool(settings.GOOGLE_GEMINI_API_KEY)
        if self.gemini_configured:
            genai.configure(api_key=settings.GOOGLE_GEMINI_API_KEY)
            logger.info("Enhanced Dataset Service initialized with Gemini")
        else:
            logger.warning("Gemini API key not configured - using fallback search")
    
    async def extract_spec(self, user_query: str) -> Dict[str, Any]:
        """
        Uses Gemini to fix typos and extract search keywords.
        Returns: {"fixed_query": str, "keywords": List[str]}
        """
        if not self.gemini_configured:
            return {"fixed_query": user_query, "keywords": [user_query]}
        
        logger.info(f"Analyzing query: '{user_query}'")
        
        try:
            def _run_gemini():
                model = genai.GenerativeModel('gemini-2.0-flash-exp')
                
                prompt = f"""
                Act as a search query optimizer for a dataset recommendation engine.
                
                Task:
                1. Analyze the User Query: "{user_query}"
                2. Fix any spelling mistakes (e.g., "dibetes" -> "diabetes", "santiment" -> "sentiment").
                
                Return ONLY valid JSON with no markdown formatting:
                {{
                    "fixed_query": "corrected query string",
                    "keywords": ["keyword1", "keyword2", "keyword3"]
                }}
                """
                
                response = model.generate_content(prompt)
                text_resp = response.text.strip()
                text_resp = text_resp.replace('```json', '').replace('```', '').strip()
                return json.loads(text_resp)
            
            # Run in thread to avoid blocking
            result = await asyncio.to_thread(_run_gemini)
            logger.info(f"✓ Fixed query: '{result.get('fixed_query', user_query)}'")
            logger.info(f"✓ Keywords: {result.get('keywords', [])}")
            return result
            
        except Exception as e:
            logger.warning(f"Gemini extraction failed: {e}, using original query")
            return {"fixed_query": user_query, "keywords": [user_query]}
    
    async def search_datasets(self, keywords: List[str], limit: int = 15) -> List[Dict[str, Any]]:
        """
        Searches both Kaggle and HuggingFace for datasets.
        Returns list of candidates with metadata and download URLs.
        """
        candidates = []
        search_term = " ".join(keywords)
        logger.info(f"Searching for: '{search_term}'")
        
        # Search Kaggle
        try:
            if kaggle_service.is_configured:
                kaggle_datasets = kaggle_service.search_datasets(search_term, page_size=limit)
                for d in kaggle_datasets:
                    # Kaggle ref already contains 'datasets/' prefix (e.g., 'datasets/username/dataset-name')
                    dataset_ref = d.get("ref")
                    candidates.append({
                        "id": dataset_ref,
                        "title": d.get("title"),
                        "description": d.get("description", d.get("title")),
                        "source": "Kaggle",
                        "url": f"https://www.kaggle.com/{dataset_ref}",  # ref already has 'datasets/' prefix
                        "download_url": f"kaggle://{dataset_ref}",  # Custom protocol with full ref
                        "downloads": d.get("downloadCount", 0),
                        "votes": d.get("voteCount", 0),
                        "size": d.get("totalBytes", 0)
                    })
                logger.info(f"✓ Found {len(candidates)} from Kaggle")
        except Exception as e:
            logger.error(f"✗ Kaggle search failed: {e}")
        
        # Search HuggingFace
        try:
            hf_datasets = await huggingface_service.search_datasets(
                query=search_term,
                limit=limit,
                use_cache=False
            )
            for d in hf_datasets:
                candidates.append({
                    "id": d.get("id"),
                    "title": d.get("title", d.get("name")),
                    "description": d.get("description", d.get("id")),
                    "source": "HuggingFace",
                    "url": d.get("url", f"https://huggingface.co/datasets/{d.get('id')}"),
                    "download_url": f"hf://datasets/{d.get('id')}",  # Custom protocol
                    "downloads": d.get("downloads", 0),
                    "likes": d.get("likes", 0)
                })
            logger.info(f"✓ Found {len(hf_datasets)} from HuggingFace")
        except Exception as e:
            logger.error(f"✗ HuggingFace search failed: {e}")
        
        return candidates
    
    async def rank_candidates(
        self,
        query: str,
        candidates: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Ranks datasets using Gemini embeddings for semantic similarity.
        """
        if not candidates or not self.gemini_configured:
            return candidates
        
        logger.info(f"Ranking {len(candidates)} candidates using embeddings...")
        
        try:
            def _compute_embeddings():
                # Embed query
                query_emb = genai.embed_content(
                    model="models/text-embedding-004",
                    content=query,
                    task_type="retrieval_query"
                )['embedding']
                
                # Embed candidates
                texts = [
                    f"{c['title']}: {str(c.get('description', ''))[:500]}"
                    for c in candidates
                ]
                
                batch_emb = genai.embed_content(
                    model="models/text-embedding-004",
                    content=texts,
                    task_type="retrieval_document"
                )['embedding']
                
                # Compute similarity
                scores = cosine_similarity([query_emb], batch_emb)[0]
                return scores
            
            # Run in thread
            scores = await asyncio.to_thread(_compute_embeddings)
            
            # Add scores to candidates
            for idx, score in enumerate(scores):
                candidates[idx]['relevance_score'] = float(score)
            
            # Sort by relevance
            ranked = sorted(candidates, key=lambda x: x.get('relevance_score', 0), reverse=True)
            logger.info(f"✓ Ranked {len(ranked)} candidates")
            return ranked
            
        except Exception as e:
            logger.warning(f"Ranking failed: {e}, returning unranked results")
            return candidates
    
    async def get_download_url(self, dataset_id: str, source: str) -> str:
        """
        Generates the proper download URL for a dataset.
        """
        if source == "Kaggle":
            # dataset_id already contains 'datasets/' prefix
            return f"https://www.kaggle.com/{dataset_id}"
        elif source == "HuggingFace":
            return f"https://huggingface.co/datasets/{dataset_id}"
        else:
            return ""
    
    async def search_and_rank(
        self,
        user_query: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Complete pipeline: extract keywords, search, and rank datasets.
        """
        # 1. Extract keywords and fix typos
        spec = await self.extract_spec(user_query)
        
        # 2. Search datasets
        keywords = spec.get('keywords', [user_query])
        candidates = await self.search_datasets(keywords, limit=15)
        
        if not candidates:
            logger.warning("No datasets found")
            return []
        
        # 3. Rank by semantic similarity
        query_for_ranking = spec.get('fixed_query', user_query)
        ranked = await self.rank_candidates(query_for_ranking, candidates)
        
        # Return top results
        return ranked[:limit]


# Global instance
enhanced_dataset_service = EnhancedDatasetService()
