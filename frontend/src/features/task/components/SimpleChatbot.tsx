import React, { useRef, useState } from 'react';
import { useModels, useChatPredict } from '../hooks';

// 대화 메시지 타입
interface ChatMessage {
  id: string;
  type: 'user' | 'bot';
  content: string;
  timestamp: Date;
  model?: string; // 봇 메시지에만 사용
}

export const SimpleChatbot: React.FC = () => {
  const [prompt, setPrompt] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedModel, setSelectedModel] = useState<string>('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 모델 리스트 조회
  const { data: modelsData, isLoading: isModelsLoading, error: modelsError } = useModels();

  // 채팅 예측 API
  const { mutateAsync: chatPredict, isPending: isChatLoading } = useChatPredict();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  React.useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 사용자가 모델을 선택하도록 유도 (자동 선택하지 않음)
  // React.useEffect(() => {
  //   if (modelsData?.available_models && modelsData.available_models.length > 0 && !selectedModel) {
  //     setSelectedModel(modelsData.available_models[0]);
  //   }
  // }, [modelsData, selectedModel]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim() || !selectedModel) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: prompt,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    const currentPrompt = prompt;
    setPrompt('');
    setIsLoading(true);

    try {
      // 실제 API 호출
      const response = await chatPredict({
        prompt: currentPrompt,
        model: selectedModel,
        stream: false
      });

      const botMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'bot',
        content: response.response,
        timestamp: new Date(),
        model: selectedModel
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('채팅 API 오류:', error);
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'bot',
        content: '죄송합니다. 응답을 생성하는 중 오류가 발생했습니다. 다시 시도해주세요.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const clearChat = () => {
    setMessages([]);
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-sm">
      {/* 헤더 */}
      <div className="flex justify-between items-center p-4 border-b border-gray-200">
        <div className="flex items-center space-x-4">
          <h3 className="text-lg font-medium text-gray-900">챗봇 테스트</h3>

          {/* 모델 선택 */}
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-600">모델:</span>
            {isModelsLoading ? (
              <div className="text-sm text-gray-500">로딩 중...</div>
            ) : modelsError ? (
              <div className="text-sm text-red-500">오류 발생</div>
            ) : (
              <div className="flex items-center space-x-2">
                <select
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  className="text-sm border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="">모델을 선택하세요</option>
                  {modelsData?.available_models?.map((modelName: string) => (
                    <option
                      key={modelName}
                      value={modelName}
                    >
                      {modelName}
                    </option>
                  )) || []}
                </select>
                {selectedModel && (
                  <div className="text-xs text-blue-600 bg-blue-50 px-2 py-1 rounded">
                    선택됨: {selectedModel}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {messages.length > 0 && (
          <button
            onClick={clearChat}
            className="text-sm text-gray-500 hover:text-gray-700 transition-colors"
          >
            대화 초기화
          </button>
        )}
      </div>

      {/* 대화 영역 */}
      <div className="h-96 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full text-gray-500">
            <div className="text-center">
              <svg className="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
              <div>
                <p className="mb-2">챗봇과 대화를 시작해보세요!</p>
                {modelsData?.available_models && (
                  <p className="text-sm text-gray-400">
                    사용 가능한 모델: {modelsData.available_models.length}개
                  </p>
                )}
                {!selectedModel && (
                  <p className="text-sm text-orange-500 mt-2">
                    먼저 모델을 선택해주세요
                  </p>
                )}
              </div>
            </div>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                  message.type === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-900'
                }`}
              >
                {message.type === 'bot' && message.model && (
                  <div className="text-xs text-gray-600 mb-2 font-medium border-b border-gray-200 pb-1">
                    {message.model}
                  </div>
                )}
                <p className="whitespace-pre-wrap">{message.content}</p>
                <p className={`text-xs mt-1 ${
                  message.type === 'user' ? 'text-blue-200' : 'text-gray-500'
                }`}>
                  {message.timestamp.toLocaleTimeString()}
                </p>
              </div>
            </div>
          ))
        )}

        {(isLoading || isChatLoading) && (
          <div className="flex justify-start">
            <div className="bg-gray-100 text-gray-900 max-w-xs lg:max-w-md px-4 py-2 rounded-lg">
              <div className="flex items-center space-x-2">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
                <span className="text-sm text-gray-500">응답 생성 중...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* 입력 영역 */}
      <div className="border-t border-gray-200 p-4">
        <form onSubmit={handleSubmit} className="flex space-x-2">
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="메시지를 입력하세요..."
            className="flex-1 p-3 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            rows={2}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSubmit(e);
              }
            }}
          />
          <button
            type="submit"
            disabled={!prompt.trim() || isLoading || isChatLoading || !selectedModel}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors self-end"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </form>
        <p className="text-xs text-gray-500 mt-2">Enter로 전송, Shift+Enter로 줄바꿈</p>
      </div>
    </div>
  );
};