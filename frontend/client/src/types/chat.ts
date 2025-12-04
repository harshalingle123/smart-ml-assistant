export interface KaggleDataset {
    ref: string;
    title: string;
    size: number;
    last_updated: string;
    download_count: number;
    vote_count: number;
    usability_rating: number;
}

export interface DownloadableDataset {
    id: string;
    title: string;
    source: "Kaggle" | "HuggingFace";
    url: string;
    downloads?: number;
    relevance_score?: number;
}

export interface MessageMetadata {
    kaggle_datasets?: KaggleDataset[];
    huggingface_datasets?: any[];
    huggingface_models?: any[];
    downloadable_datasets?: DownloadableDataset[];
    search_query?: string;
    model_id?: string;
    best_model?: string;
    metrics?: any;
}

export interface Message {
    role: "user" | "assistant";
    content: string;
    queryType?: "simple" | "data_based" | "dataset_search";
    timestamp: Date;
    charts?: any[];
    metadata?: MessageMetadata;
}
