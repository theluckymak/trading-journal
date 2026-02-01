import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/router';
import Layout from '@/components/Layout';
import ChatBox from '@/components/ChatBox';
import { apiClient } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';

interface ChatMessage {
  id: number;
  user_id: number;
  user_name: string;
  message: string;
  is_admin: boolean;
  created_at: string;
}

export default function ContactPage() {
  const router = useRouter();
  const { user } = useAuth();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchMessages = useCallback(async () => {
    try {
      const data = await apiClient.getChatMessages();
      setMessages(data);
    } catch (error: any) {
      console.error('Failed to fetch messages:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!user) {
      router.push('/login');
      return;
    }

    fetchMessages();

    // Poll for new messages every 5 seconds
    const interval = setInterval(fetchMessages, 5000);

    return () => clearInterval(interval);
  }, [user, router, fetchMessages]);

  const handleSendMessage = async (message: string) => {
    try {
      await apiClient.sendChatMessage(message);
      // Refresh messages immediately after sending
      await fetchMessages();
    } catch (error: any) {
      console.error('Failed to send message:', error);
      alert('Failed to send message. Please try again.');
      throw error;
    }
  };

  const handleDeleteMessage = async (messageId: number) => {
    try {
      await apiClient.deleteChatMessage(messageId);
      // Refresh messages after deletion
      await fetchMessages();
    } catch (error: any) {
      console.error('Failed to delete message:', error);
      alert('Failed to delete message. Please try again.');
      throw error;
    }
  };

  if (!user) {
    return null;
  }

  return (
    <Layout>
      <div className="min-h-screen p-6 lg:p-8">
        <div className="max-w-6xl mx-auto">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-white mb-2">
            Contact Support
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Have questions or need help? Chat with our support team. Your conversation is private - only you and support can see your messages.
          </p>
        </div>

        <div className="h-[500px]">
          <ChatBox
            currentUserId={user.id}
            isAdmin={user.role === 'ADMIN'}
            onSendMessage={handleSendMessage}
            onDeleteMessage={handleDeleteMessage}
            messages={messages}
            loading={loading}
          />
        </div>

        <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
          <p className="text-sm text-blue-800 dark:text-blue-200">
            <strong>Privacy:</strong> This is a private conversation. Only you and support staff can see your messages.
            Support responses will be marked with "Support" badge and appear in real-time.
          </p>
        </div>
        </div>
      </div>
    </Layout>
  );
}
