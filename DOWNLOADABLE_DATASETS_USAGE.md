# Downloadable Datasets Feature - Usage Guide

## For End Users

### How to Download Datasets from Chat

1. **Start a conversation in Agent Mode** (toggle should be ON)

2. **Ask for dataset recommendations:**
   ```
   "I need a diabetes prediction dataset"
   "Find me sentiment analysis datasets"
   "Show me image classification datasets"
   ```

3. **View Download Options:**
   - After the AI responds, you'll see a "Download Options" section
   - Each dataset card shows:
     - Dataset title and ID
     - Source (Kaggle or HuggingFace)
     - Download count
     - Relevance score (how well it matches your query)

4. **Download a Dataset:**
   - Click the "Download Dataset" button
   - Wait for the download to complete (status will show "Downloading...")
   - Success: You'll see a green message with the local file path
   - Error: You'll see a red message explaining what went wrong

5. **View Dataset Online:**
   - Click the 🔗 (external link) button to open the dataset page
   - Opens in a new tab on Kaggle or HuggingFace

### Example Queries

**Good queries that trigger downloadable datasets:**
- "I need a dataset for house price prediction"
- "Find me customer churn datasets"
- "Show me NLP datasets for sentiment analysis"
- "I want to build an image classifier, suggest datasets"
- "Find fraud detection datasets"

**What you'll see:**
```
📦 Download Options                        5 datasets
┌────────────────────────────────────────────────────┐
│ Pima Indians Diabetes Database                     │
│ uciml/pima-indians-diabetes                        │
│ 🔵 Kaggle    📊 Downloads: 15,234   ⭐ 95%        │
│ [Download Dataset] [🔗]                            │
└────────────────────────────────────────────────────┘
```

### Download Status Messages

**While Downloading:**
```
[⏳ Downloading...]
```

**Success:**
```
✅ Downloaded successfully
📁 E:\Startup\smart-ml-assistant\downloads\diabetes-dataset
```

**Error:**
```
❌ Download failed
Failed to download dataset: Kaggle API not configured
```

## For Developers

### Using the DownloadableDatasetCard Component

#### Basic Usage

```tsx
import { DownloadableDatasetCard } from "@/components/DownloadableDatasetCard";

function MyComponent() {
  return (
    <DownloadableDatasetCard
      id="uciml/pima-indians-diabetes"
      title="Pima Indians Diabetes Database"
      source="Kaggle"
      url="https://www.kaggle.com/datasets/uciml/pima-indians-diabetes"
      downloads={15234}
      relevance_score={0.95}
    />
  );
}
```

#### Props Reference

```typescript
interface DownloadableDatasetCardProps {
  // Required Props
  id: string;           // Dataset identifier (Kaggle ref or HF name)
  title: string;        // Display name for the dataset
  source: "Kaggle" | "HuggingFace";  // Data source platform
  url: string;          // External URL to view the dataset

  // Optional Props
  downloads?: number;   // Number of times downloaded (for display only)
  relevance_score?: number;  // Relevance to user query (0-1 scale)
}
```

#### Advanced Example with Grid Layout

```tsx
import { DownloadableDatasetCard } from "@/components/DownloadableDatasetCard";

function DatasetGrid({ datasets }: { datasets: DownloadableDataset[] }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
      {datasets.map((dataset, idx) => (
        <DownloadableDatasetCard
          key={`${dataset.source}-${dataset.id}-${idx}`}
          id={dataset.id}
          title={dataset.title}
          source={dataset.source}
          url={dataset.url}
          downloads={dataset.downloads}
          relevance_score={dataset.relevance_score}
        />
      ))}
    </div>
  );
}
```

### Backend Integration

#### Message Response Format

When your AI agent returns a message, include the `downloadable_datasets` field:

```python
# In your message response
response_dict = {
    "role": "assistant",
    "content": "Here are the top diabetes datasets I found...",
    "downloadable_datasets": [
        {
            "id": "uciml/pima-indians-diabetes",
            "title": "Pima Indians Diabetes Database",
            "source": "Kaggle",
            "url": "https://www.kaggle.com/datasets/uciml/pima-indians-diabetes",
            "downloads": 15234,
            "relevance_score": 0.95
        },
        {
            "id": "scikit-learn/diabetes",
            "title": "Diabetes Dataset",
            "source": "HuggingFace",
            "url": "https://huggingface.co/datasets/scikit-learn/diabetes",
            "downloads": 8421,
            "relevance_score": 0.88
        }
    ]
}
```

#### API Endpoint for Downloads

The frontend expects this endpoint:

```
POST /api/datasets/download-dataset

Request Body:
{
  "dataset_id": "uciml/pima-indians-diabetes",
  "source": "Kaggle"
}

Response (Success):
{
  "success": true,
  "dataset_id": "uciml/pima-indians-diabetes",
  "source": "Kaggle",
  "message": "Dataset downloaded successfully",
  "file_path": "E:/Startup/smart-ml-assistant/downloads/pima-indians-diabetes"
}

Response (Error):
{
  "success": false,
  "dataset_id": "uciml/pima-indians-diabetes",
  "source": "Kaggle",
  "message": "Kaggle API is not configured",
  "file_path": null
}
```

### Customization

#### Changing Colors

Edit the `getSourceColor()` function in `DownloadableDatasetCard.tsx`:

```tsx
const getSourceColor = () => {
  return source === "Kaggle"
    ? "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300"
    : "bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-300";
};
```

#### Adding New Sources

1. Update the `source` type:
```tsx
source: "Kaggle" | "HuggingFace" | "UCI" | "Custom"
```

2. Add source color mapping:
```tsx
const getSourceColor = () => {
  switch(source) {
    case "Kaggle": return "bg-blue-100 text-blue-700 ...";
    case "HuggingFace": return "bg-orange-100 text-orange-700 ...";
    case "UCI": return "bg-green-100 text-green-700 ...";
    default: return "bg-gray-100 text-gray-700 ...";
  }
};
```

3. Update backend download service to support new source

### Styling Customization

The component uses Tailwind CSS. Common customizations:

#### Card Border
```tsx
// Default
<Card className="p-4 hover:shadow-md transition-shadow border-l-4 border-l-primary/20">

// Custom color
<Card className="p-4 hover:shadow-md transition-shadow border-l-4 border-l-green-500">
```

#### Button Variants
```tsx
// Default
<Button size="sm" variant="default">Download Dataset</Button>

// Outline style
<Button size="sm" variant="outline">Download Dataset</Button>

// Different sizes
<Button size="xs">Download</Button>
<Button size="lg">Download Dataset</Button>
```

### Error Handling

#### Common Errors and Solutions

**"Kaggle API is not configured"**
- Solution: Set up Kaggle API credentials in backend `.env`
- Required: `KAGGLE_USERNAME` and `KAGGLE_KEY`

**"HuggingFace API is not configured"**
- Solution: Set `HF_TOKEN` in backend `.env`
- Get token from: https://huggingface.co/settings/tokens

**"Failed to download dataset: Dataset not found"**
- Solution: Verify dataset ID is correct
- Check if dataset still exists on source platform

**"Network error during download"**
- Solution: Check internet connection
- Verify backend can reach Kaggle/HuggingFace APIs

### Performance Optimization

The component is already optimized with:

1. **React.memo()** - Prevents unnecessary re-renders
2. **Local state** - Avoids prop drilling
3. **Efficient API calls** - Only downloads on user action
4. **Optimistic updates** - Immediate UI feedback

### Accessibility

The component is fully accessible:

- ✅ **Keyboard Navigation:** All interactive elements are keyboard accessible
- ✅ **Screen Readers:** ARIA labels and live regions
- ✅ **Color Contrast:** WCAG AA compliant
- ✅ **Focus Management:** Clear focus indicators
- ✅ **Semantic HTML:** Proper heading hierarchy

### Testing

#### Unit Test Example (Jest + React Testing Library)

```tsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { DownloadableDatasetCard } from './DownloadableDatasetCard';

describe('DownloadableDatasetCard', () => {
  it('renders dataset information', () => {
    render(
      <DownloadableDatasetCard
        id="test/dataset"
        title="Test Dataset"
        source="Kaggle"
        url="https://kaggle.com/test"
        downloads={1234}
        relevance_score={0.95}
      />
    );

    expect(screen.getByText('Test Dataset')).toBeInTheDocument();
    expect(screen.getByText('test/dataset')).toBeInTheDocument();
    expect(screen.getByText('Kaggle')).toBeInTheDocument();
  });

  it('downloads dataset on button click', async () => {
    const user = userEvent.setup();

    render(
      <DownloadableDatasetCard
        id="test/dataset"
        title="Test Dataset"
        source="Kaggle"
        url="https://kaggle.com/test"
      />
    );

    const downloadButton = screen.getByRole('button', { name: /download/i });
    await user.click(downloadButton);

    await waitFor(() => {
      expect(screen.getByText(/downloading/i)).toBeInTheDocument();
    });
  });
});
```

## Troubleshooting

### Component Not Rendering

1. Check if `downloadable_datasets` exists in message metadata
2. Verify the array is not empty
3. Check browser console for errors
4. Ensure all required props are provided

### Download Button Not Working

1. Verify API endpoint is accessible
2. Check authentication token is valid
3. Ensure backend services (Kaggle/HuggingFace) are configured
4. Check network tab for API request errors

### Styling Issues

1. Verify Tailwind CSS is properly configured
2. Check if dark mode classes are working
3. Ensure shadcn/ui components are installed
4. Clear browser cache and rebuild

## FAQ

**Q: Can I download multiple datasets at once?**
A: Currently, each dataset must be downloaded individually. Batch download is a potential future enhancement.

**Q: Where are datasets downloaded to?**
A: By default, datasets are downloaded to `E:\Startup\smart-ml-assistant\downloads\`. This can be configured in backend settings.

**Q: What formats are supported?**
A: The component supports any format that Kaggle and HuggingFace provide (CSV, JSON, Parquet, etc.)

**Q: Can I cancel a download in progress?**
A: Currently, there's no cancel functionality. This could be added as a future enhancement.

**Q: How do I add a new data source?**
A: See the "Adding New Sources" section under Customization.

---

**Last Updated:** December 3, 2025
