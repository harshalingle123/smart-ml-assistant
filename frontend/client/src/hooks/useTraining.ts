import { useState } from 'react';
import { useToast } from '@/hooks/use-toast';
import { getApiUrl } from '@/lib/env';

export function useTraining() {
    const [isTraining, setIsTraining] = useState(false);
    const { toast } = useToast();

    const startTraining = async (datasetId: string, chatId: string, onMessage: (msg: any) => void) => {
        try {
            setIsTraining(true);
            const token = localStorage.getItem("token");
            if (!token) {
                toast({ title: "Authentication Required", description: "Please log in", variant: "destructive" });
                setIsTraining(false);
                return;
            }

            const response = await fetch(
                `${getApiUrl()}/api/automl/train/${datasetId}?chat_id=${chatId}`,
                {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Accept': 'text/event-stream',
                    },
                }
            );

            if (!response.ok) throw new Error(`Training failed: ${response.status}`);

            const reader = response.body?.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            if (!reader) throw new Error("No response body");

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n\n');
                buffer = lines.pop() || '';

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            onMessage(data);

                            if (data.type === 'complete' || data.type === 'error') {
                                setIsTraining(false);
                                if (data.type === 'complete') {
                                    toast({ title: "Training Complete!", description: `Model: ${data.best_model}` });
                                } else {
                                    toast({ title: "Training Failed", description: data.message, variant: "destructive" });
                                }
                                return;
                            }
                        } catch (e) {
                            console.error("SSE Parse Error", e);
                        }
                    }
                }
            }
            setIsTraining(false);
        } catch (error: any) {
            console.error("Training Error:", error);
            setIsTraining(false);
            toast({ title: "Connection Error", description: error.message, variant: "destructive" });
        }
    };

    return { isTraining, startTraining };
}
