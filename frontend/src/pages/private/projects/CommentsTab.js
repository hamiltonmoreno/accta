import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { toast } from 'sonner';
import { MessageSquare, Send, Trash2 } from 'lucide-react';
import { projectsAPI } from '../../../utils/api';
import { useAuth } from '../../../contexts/AuthContext';
import { EmptyState } from '../../../components/EmptyState';
import { UserAvatar } from '../../../components/UserAvatar';

export const CommentsTab = ({ project, comments, onReload }) => {
  const { user } = useAuth();
  const [text, setText] = useState('');

  const sendMutation = useMutation({
    mutationFn: (content) => projectsAPI.addComment(project.id, content),
    onSuccess: () => {
      setText('');
      onReload();
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro'),
  });

  const deleteMutation = useMutation({
    mutationFn: (commentId) => projectsAPI.deleteComment(project.id, commentId),
    onSuccess: onReload,
    onError: () => toast.error('Erro'),
  });

  const sending = sendMutation.isPending;

  const handleSend = () => {
    if (!text.trim()) return;
    sendMutation.mutate(text);
  };

  return (
    <div className="space-y-4">
      {/* Input */}
      <div className="bg-white border border-gray-200/80 rounded-xl p-3.5 flex items-start gap-3">
        <UserAvatar size="xs" name={user?.name} photoUrl={user?.photo_url} />
        <div className="flex-1">
          <textarea rows={2} value={text} onChange={(e) => setText(e.target.value)}
            placeholder="Partilhe uma ideia ou comentario..."
            className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none resize-none"
            data-testid="comment-input" />
          <div className="flex justify-end mt-2">
            <button onClick={handleSend} disabled={sending || !text.trim()}
              className="btn-primary text-xs px-4 py-2 flex items-center gap-1.5 disabled:opacity-40" data-testid="send-comment-btn">
              <Send className="w-3.5 h-3.5" /> {sending ? '...' : 'Enviar'}
            </button>
          </div>
        </div>
      </div>

      {/* List */}
      {comments.length === 0 ? (
        <EmptyState icon={MessageSquare} title="Nenhum comentario ainda" className="p-6 sm:p-8" testId="no-comments" />
      ) : (
        <div className="space-y-2">
          {comments.map((c) => (
            <div key={c.id} className="bg-white border border-gray-200/80 rounded-xl p-4" data-testid={`comment-${c.id}`}>
              <div className="flex items-center gap-2 mb-1.5">
                <UserAvatar
                  size="xs"
                  className="w-7 h-7"
                  name={c.user_name}
                  photoUrl={c.user_photo_url}
                  fallbackClassName="bg-grafite"
                />
                <span className="font-semibold text-sm text-grafite">{c.user_name}</span>
                <span className="text-xs text-[#6B7280] ml-auto">
                  {c.created_at ? new Date(c.created_at).toLocaleDateString('pt') : ''}
                </span>
                {(c.user_id === user?.id || user?.role === 'admin') && (
                  <button onClick={() => deleteMutation.mutate(c.id)} className="p-1 text-gray-400 hover:text-[#B91C1C]" aria-label="Apagar comentário">
                    <Trash2 className="w-3 h-3" aria-hidden="true" />
                  </button>
                )}
              </div>
              <p className="text-sm text-gray-600 leading-relaxed">{c.content}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
