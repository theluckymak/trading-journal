import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import Layout from '@/components/Layout';
import { useAuth } from '@/contexts/AuthContext';
import { apiClient } from '@/lib/api';
import {
  Plus,
  Search,
  BookOpen,
  Calendar,
  Edit,
  Trash2,
  Eye,
} from 'lucide-react';

interface JournalEntry {
  id: number;
  title: string;
  content: string;
  entry_date: string;
  mood: string | null;
  tags: string | null;
  created_at: string;
  updated_at: string;
}

export default function JournalPage() {
  const router = useRouter();
  const { user } = useAuth();
  const [entries, setEntries] = useState<JournalEntry[]>([]);
  const [filteredEntries, setFilteredEntries] = useState<JournalEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedMood, setSelectedMood] = useState<string>('all');

  useEffect(() => {
    if (!user) {
      router.push('/login');
      return;
    }
    loadEntries();
  }, [user]);

  useEffect(() => {
    filterEntries();
  }, [entries, searchTerm, selectedMood]);

  const loadEntries = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getJournalEntries();
      setEntries(data);
    } catch (error) {
      console.error('Failed to load journal entries:', error);
    } finally {
      setLoading(false);
    }
  };

  const filterEntries = () => {
    let filtered = [...entries];

    if (searchTerm) {
      filtered = filtered.filter(
        (entry) =>
          entry.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
          entry.content.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    if (selectedMood !== 'all') {
      filtered = filtered.filter((entry) => entry.mood === selectedMood);
    }

    filtered.sort((a, b) => new Date(b.entry_date).getTime() - new Date(a.entry_date).getTime());

    setFilteredEntries(filtered);
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this journal entry?')) return;

    try {
      await apiClient.deleteJournalEntry(id);
      setEntries(entries.filter((e) => e.id !== id));
    } catch (error) {
      console.error('Failed to delete entry:', error);
      alert('Failed to delete entry');
    }
  };

  const getMoodEmoji = (mood: string | null) => {
    const moods: Record<string, string> = {
      excellent: '😄',
      good: '🙂',
      neutral: '😐',
      bad: '😟',
      terrible: '😢',
    };
    return mood ? moods[mood] || '📝' : '📝';
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'long',
      day: 'numeric',
      year: 'numeric',
    });
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <BookOpen className="h-12 w-12 text-blue-600 mx-auto animate-pulse" />
            <p className="mt-4 text-gray-600 dark:text-gray-400">Loading journal entries...</p>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="p-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">Journal</h1>
          <p className="text-gray-600 dark:text-gray-400">
            Document your trading journey and insights
          </p>
        </div>

        {/* Controls */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-6">
          <div className="flex flex-wrap gap-4">
            {/* Search */}
            <div className="flex-1 min-w-[200px]">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search entries..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            {/* Mood Filter */}
            <select
              value={selectedMood}
              onChange={(e) => setSelectedMood(e.target.value)}
              className="px-4 py-2 border dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Moods</option>
              <option value="excellent">😄 Excellent</option>
              <option value="good">🙂 Good</option>
              <option value="neutral">😐 Neutral</option>
              <option value="bad">😟 Bad</option>
              <option value="terrible">😢 Terrible</option>
            </select>

            {/* New Entry Button */}
            <button
              onClick={() => router.push('/journal/new')}
              className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
            >
              <Plus className="h-5 w-5" />
              New Entry
            </button>
          </div>
        </div>

        {/* Entries Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredEntries.length === 0 ? (
            <div className="col-span-full text-center py-12">
              <BookOpen className="h-16 w-16 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600 dark:text-gray-400 text-lg">
                {entries.length === 0
                  ? 'No journal entries yet. Start documenting your trading journey!'
                  : 'No entries match your search.'}
              </p>
              {entries.length === 0 && (
                <button
                  onClick={() => router.push('/journal/new')}
                  className="mt-4 inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
                >
                  <Plus className="h-5 w-5" />
                  Create First Entry
                </button>
              )}
            </div>
          ) : (
            filteredEntries.map((entry) => (
              <div
                key={entry.id}
                className="bg-white dark:bg-gray-800 rounded-lg shadow hover:shadow-lg transition p-6 cursor-pointer"
                onClick={() => router.push(`/journal/${entry.id}`)}
              >
                {/* Header */}
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <span className="text-2xl">{getMoodEmoji(entry.mood)}</span>
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white line-clamp-1">
                        {entry.title}
                      </h3>
                      <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400 mt-1">
                        <Calendar className="h-4 w-4" />
                        {formatDate(entry.entry_date)}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Content Preview */}
                <p className="text-gray-600 dark:text-gray-400 text-sm line-clamp-3 mb-4">
                  {entry.content}
                </p>

                {/* Tags */}
                {entry.tags && (
                  <div className="flex flex-wrap gap-2 mb-4">
                    {entry.tags.split(',').map((tag, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-300 text-xs rounded-full"
                      >
                        {tag.trim()}
                      </span>
                    ))}
                  </div>
                )}

                {/* Actions */}
                <div className="flex items-center gap-2 pt-4 border-t dark:border-gray-700">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      router.push(`/journal/${entry.id}`);
                    }}
                    className="flex items-center gap-1 px-3 py-1.5 text-sm text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition"
                  >
                    <Eye className="h-4 w-4" />
                    View
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      router.push(`/journal/edit/${entry.id}`);
                    }}
                    className="flex items-center gap-1 px-3 py-1.5 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg transition"
                  >
                    <Edit className="h-4 w-4" />
                    Edit
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(entry.id);
                    }}
                    className="flex items-center gap-1 px-3 py-1.5 text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition ml-auto"
                  >
                    <Trash2 className="h-4 w-4" />
                    Delete
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </Layout>
  );
}
