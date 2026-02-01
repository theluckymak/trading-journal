import { useState, useEffect, useRef } from 'react';
import { Send, Trash2 } from 'lucide-react';

interface ChatMessage {
  id: number;
  user_id: number;
  user_name: string;
  message: string;
  is_admin: boolean;
  created_at: string;
}

interface ChatBoxProps {
  currentUserId: number;
  isAdmin: boolean;
  onSendMessage: (message: string) => Promise<void>;
  onDeleteMessage: (messageId: number) => Promise<void>;
  messages: ChatMessage[];
  loading: boolean;
}

export default function ChatBox({
  currentUserId,
  isAdmin,
  onSendMessage,
  onDeleteMessage,
  messages,
  loading,
}: ChatBoxProps) {
  const [newMessage, setNewMessage] = useState('');
  const [sending, setSending] = useState(false);
  const [mounted, setMounted] = useState(false);

  // Handle mounting for hydration safety
  useEffect(() => {
    setMounted(true);
  }, []);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMessage.trim() || sending) return;

    setSending(true);
    try {
      await onSendMessage(newMessage);
      setNewMessage('');
    } catch (error) {
      console.error('Failed to send message:', error);
    } finally {
      setSending(false);
    }
  };

  const handleDelete = async (messageId: number) => {
    if (!confirm('Are you sure you want to delete this message?')) return;

    try {
      await onDeleteMessage(messageId);
    } catch (error) {
      console.error('Failed to delete message:', error);
    }
  };

  const formatTime = (dateString: string) => {
    // Ensure proper UTC parsing - append 'Z' if not present
    const isoString = dateString.endsWith('Z') ? dateString : `${dateString}Z`;
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffSecs = Math.floor(diffMs / 1000);
    const diffMins = Math.floor(diffSecs / 60);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffSecs < 10) return 'Just now';
    if (diffSecs < 60) return `${diffSecs}s ago`;
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;

    return date.toLocaleDateString();
  };

  return (
    <div className="flex flex-col h-full bg-white dark:bg-gray-800 rounded-lg shadow-md">
      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {loading || !mounted ? (
          <div className="flex items-center justify-center h-full">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          </div>
        ) : messages.length === 0 ? (
          <div className="flex items-center justify-center h-full text-gray-500 dark:text-gray-400">
            No messages yet. Start the conversation!
          </div>
        ) : (
          messages.map((msg) => {
            const isOwn = msg.user_id === currentUserId;
            const canDelete = isAdmin || isOwn;

            return (
              <div
                key={msg.id}
                className={`flex ${isOwn ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[70%] rounded-lg p-3 ${
                    msg.is_admin
                      ? 'bg-green-100 dark:bg-green-900 text-green-900 dark:text-green-100'
                      : isOwn
                      ? 'bg-blue-100 dark:bg-blue-900 text-blue-900 dark:text-blue-100'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-gray-100'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-semibold text-sm">
                          {msg.is_admin ? `Support (${msg.user_name})` : msg.user_name}
                        </span>
                        <span className="text-xs opacity-70">
                          {formatTime(msg.created_at)}
                        </span>
                      </div>
                      <p className="text-sm whitespace-pre-wrap break-words">
                        {msg.message}
                      </p>
                    </div>
                    {canDelete && (
                      <button
                        onClick={() => handleDelete(msg.id)}
                        className="flex-shrink-0 p-1 hover:bg-red-200 dark:hover:bg-red-800 rounded transition-colors"
                        title="Delete message"
                      >
                        <Trash2 className="h-4 w-4 text-red-600 dark:text-red-400" />
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Message Input */}
      <form onSubmit={handleSend} className="border-t border-gray-200 dark:border-gray-700 p-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            placeholder="Type your message..."
            className="input flex-1"
            disabled={sending}
            maxLength={5000}
          />
          <button
            type="submit"
            disabled={!newMessage.trim() || sending}
            className="btn btn-primary flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send className="h-4 w-4" />
            Send
          </button>
        </div>
      </form>
    </div>
  );
}
