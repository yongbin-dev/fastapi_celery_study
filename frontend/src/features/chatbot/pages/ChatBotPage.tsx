import React from 'react';
import { ChatMessage, ChatInput, TypingIndicator } from '../components';
import { useChatBot } from '../hooks/useChatBot';
import { useModels } from '../hooks';

const ChatBotPage: React.FC = () => {

  const { data } = useModels();

  const {
    messages,
    inputValue,
    setInputValue,
    isLoading,
    messagesEndRef,
    handleSendMessage,
  } = useChatBot();

  return (
    <div className="h-full bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto h-full">
        <div className="bg-white rounded-lg shadow-lg overflow-hidden h-full flex flex-col">
          <div className="bg-blue-600 text-white p-4">
            <h1 className="text-xl font-bold">ChatBot 테스트</h1>
            <p className="text-blue-100 text-sm">간단한 챗봇과 대화해보세요</p>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))}

            {isLoading && <TypingIndicator />}

            <div ref={messagesEndRef} />
          </div>

          <ChatInput
            value={inputValue}
            onChange={setInputValue}
            onSend={handleSendMessage}
            isLoading={isLoading}
          />
        </div>
      </div>
    </div>
  );
};

export default ChatBotPage;