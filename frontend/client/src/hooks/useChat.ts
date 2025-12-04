import { useState, useCallback } from 'react';
import { Message, MessageMetadata } from '@/types/chat'; // We'll need to define these types
import { createChat, sendMessage, sendMessageToAgent, updateChat } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';

export function useChat() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [chatId, setChatId] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const { toast } = useToast();

    const addMessage = useCallback((message: Message) => {
        setMessages((prev) => [...prev, message]);
    }, []);

    const handleSendMessage = async (content: string, useAgent: boolean, file?: File) => {
        let currentChatId = chatId;

        // Create chat if needed
        if (!currentChatId) {
            try {
                const chatTitle = generateChatTitle(content);
                const chat = await createChat({ title: chatTitle });
                currentChatId = chat._id;
                setChatId(currentChatId);
                window.history.pushState({}, '', `/?chat=${currentChatId}`);
            } catch (error) {
                console.error("Failed to create chat:", error);
                toast({
                    variant: "destructive",
                    title: "Error",
                    description: "Failed to create chat. Please try again.",
                });
                return;
            }
        }

        // Optimistic update
        const userMessage: Message = {
            role: "user",
            content: file ? `Uploaded: ${file.name}\n${content}` : content,
            timestamp: new Date(),
        };
        addMessage(userMessage);
        setIsLoading(true);

        try {
            const response = useAgent
                ? await sendMessageToAgent({ chat_id: currentChatId, content: userMessage.content })
                : await sendMessage({ chat_id: currentChatId, content: userMessage.content });

            const assistantMessage: Message = {
                role: "assistant",
                content: response.content,
                queryType: response.query_type,
                timestamp: new Date(response.timestamp),
                metadata: {
                    ...response.metadata,
                    kaggle_datasets: response.kaggle_datasets || response.metadata?.kaggle_datasets,
                    huggingface_datasets: response.huggingface_datasets || response.metadata?.huggingface_datasets,
                    huggingface_models: response.huggingface_models || response.metadata?.huggingface_models
                },
            };

            // Update title if needed
            if (messages.length <= 1 && (response.kaggle_datasets?.length || response.metadata?.kaggle_datasets?.length)) {
                const enhancedTitle = generateChatTitle(content);
                updateChat(currentChatId, { title: enhancedTitle }).catch(console.error);
            }

            addMessage(assistantMessage);
        } catch (error: any) {
            console.error("Failed to send message:", error);
            toast({
                variant: "destructive",
                title: "Error",
                description: error.message || "Failed to send message",
            });
            setMessages((prev) => prev.filter((msg) => msg !== userMessage));
        } finally {
            setIsLoading(false);
        }
    };

    return {
        messages,
        setMessages,
        chatId,
        setChatId,
        isLoading,
        setIsLoading,
        handleSendMessage,
        addMessage
    };
}

// Helper (moved from component)
const generateChatTitle = (query: string): string => {
    const lowerQuery = query.toLowerCase();
    if (lowerQuery.includes('sentiment')) return 'Sentiment Analysis';
    if (lowerQuery.includes('house') && lowerQuery.includes('price')) return 'House Price Prediction';
    // ... (rest of the logic)
    const words = query.split(' ').filter(w => w.length > 3).slice(0, 3);
    return words.length > 0 ? words.join(' ') : 'New Chat';
};
