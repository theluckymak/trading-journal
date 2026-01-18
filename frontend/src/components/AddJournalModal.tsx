import { useState } from 'react';
import { useRouter } from 'next/router';
import { X, Save } from 'lucide-react';

interface AddJournalModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export default function AddJournalModal({ isOpen, onClose, onSuccess }: AddJournalModalProps) {
  const router = useRouter();
  const [formData, setFormData] = useState({
    title: '',
    content: '',
    entry_date: new Date().toISOString().split('T')[0],
    mood: 'neutral',
    tags: '',
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const resetForm = () => {
    setFormData({
      title: '',
      content: '',
      entry_date: new Date().toISOString().split('T')[0],
      mood: 'neutral',
      tags: '',
    });
    setError('');
    setSuccess(false);
  };

  const handleClose = () => {
    resetForm();
    onClose();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');
    setSuccess(false);

    try {
      let accessToken = localStorage.getItem('accessToken');
      
      if (!accessToken) {
        setError('Not authenticated. Please log in again.');
        return;
      }

      let response = await fetch('http://localhost:8000/api/journal/entries', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`,
        },
        body: JSON.stringify(formData),
      });

      // If 401, try to refresh token and retry
      if (response.status === 401) {
        const refreshToken = localStorage.getItem('refreshToken');
        
        if (refreshToken) {
          try {
            const refreshResponse = await fetch('http://localhost:8000/api/auth/refresh', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({ refresh_token: refreshToken }),
            });

            if (refreshResponse.ok) {
              const refreshData = await refreshResponse.json();
              const newAccessToken = refreshData.access_token;
              localStorage.setItem('accessToken', newAccessToken);

              response = await fetch('http://localhost:8000/api/journal/entries', {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                  'Authorization': `Bearer ${newAccessToken}`,
                },
                body: JSON.stringify(formData),
              });
            } else {
              setError('Session expired. Please log in again.');
              setTimeout(() => router.push('/login'), 2000);
              return;
            }
          } catch (refreshError) {
            setError('Session expired. Please log in again.');
            setTimeout(() => router.push('/login'), 2000);
            return;
          }
        } else {
          setError('Session expired. Please log in again.');
          setTimeout(() => router.push('/login'), 2000);
          return;
        }
      }

      if (!response.ok) {
        const errorData = await response.json();
        const detail = errorData.detail;
        if (Array.isArray(detail)) {
          const errorMessages = detail.map((e: any) => `${e.loc?.join(' → ') || 'Field'}: ${e.msg}`).join(', ');
          setError(errorMessages);
        } else if (typeof detail === 'string') {
          setError(detail);
        } else {
          setError(`Failed to create journal entry: ${response.status}`);
        }
        return;
      }

      setSuccess(true);
      setTimeout(() => {
        handleClose();
        if (onSuccess) onSuccess();
      }, 1500);
    } catch (error) {
      console.error('Failed to create entry:', error);
      setError('Failed to create journal entry. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white dark:bg-gray-800 border-b dark:border-gray-700 px-6 py-4 flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">New Journal Entry</h2>
            <p className="text-sm text-gray-600 dark:text-gray-400">Document your trading thoughts and lessons</p>
          </div>
          <button
            onClick={handleClose}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition"
          >
            <X className="h-5 w-5 text-gray-600 dark:text-gray-400" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6">
          {success && (
            <div className="mb-6 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 text-green-700 dark:text-green-400 px-4 py-3 rounded-lg flex items-center">
              <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              Journal entry created successfully!
            </div>
          )}
          {error && (
            <div className="mb-6 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 px-4 py-3 rounded-lg">
              {error}
            </div>
          )}

          <div className="space-y-6">
            {/* Title */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Title *
              </label>
              <input
                type="text"
                required
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                className="w-full px-4 py-2 border dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
                placeholder="Today's Trading Session"
              />
            </div>

            {/* Date and Mood */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Entry Date *
                </label>
                <input
                  type="date"
                  required
                  value={formData.entry_date}
                  onChange={(e) => setFormData({ ...formData, entry_date: e.target.value })}
                  className="w-full px-4 py-2 border dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Mood
                </label>
                <select
                  value={formData.mood}
                  onChange={(e) => setFormData({ ...formData, mood: e.target.value })}
                  className="w-full px-4 py-2 border dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
                >
                  <option value="excellent">😄 Excellent</option>
                  <option value="good">🙂 Good</option>
                  <option value="neutral">😐 Neutral</option>
                  <option value="bad">😟 Bad</option>
                  <option value="terrible">😢 Terrible</option>
                </select>
              </div>
            </div>

            {/* Content */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Content *
              </label>
              <textarea
                required
                rows={12}
                value={formData.content}
                onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                className="w-full px-4 py-2 border dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
                placeholder="Describe your trading session, what went well, what you learned, and any insights..."
              />
            </div>

            {/* Tags */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Tags
              </label>
              <input
                type="text"
                value={formData.tags}
                onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
                className="w-full px-4 py-2 border dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
                placeholder="strategy, lesson, mistake, win (comma separated)"
              />
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                Separate multiple tags with commas
              </p>
            </div>

            {/* Actions */}
            <div className="flex gap-4 pt-6">
              <button
                type="submit"
                disabled={submitting}
                className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
              >
                <Save className="h-5 w-5" />
                {submitting ? 'Saving...' : 'Save Entry'}
              </button>
              <button
                type="button"
                onClick={handleClose}
                className="flex-1 px-6 py-3 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition"
              >
                Cancel
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
