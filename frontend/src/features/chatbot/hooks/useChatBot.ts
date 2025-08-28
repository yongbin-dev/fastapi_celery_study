import { useState, useRef, useEffect } from 'react';
import type { Message } from '../types';

export const useChatBot = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      content: '안녕하세요! 무엇을 도와드릴까요?',
      sender: 'bot',
      timestamp: new Date(),
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const simulateBotResponse = (userMessage: string): string => {
    const responses = [
      '흥미로운 질문이네요! 더 자세히 설명해주세요.',
      '네, 이해했습니다. 다른 궁금한 것이 있나요?',
      '좋은 생각입니다! 어떻게 도움을 드릴까요?',
      '그렇군요. 더 구체적으로 알려주시면 도움을 드리겠습니다.',
      '감사합니다. 다른 질문이 있으시면 언제든 물어보세요.',
    ];
    
    if (userMessage.toLowerCase().includes('안녕')) {
      return '안녕하세요! 좋은 하루 되세요!';
    }
    if (userMessage.toLowerCase().includes('도움')) {
      return '물론입니다! 무엇을 도와드릴까요?';
    }
    if (userMessage.toLowerCase().includes('감사')) {
      return '천만에요! 언제든 말씀해주세요.';
    }
    
    return responses[Math.floor(Math.random() * responses.length)];
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputValue,
      sender: 'user',
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    const currentInput = inputValue;
    setInputValue('');
    setIsLoading(true);

    setTimeout(() => {
      const botResponse: Message = {
        id: (Date.now() + 1).toString(),
        content: simulateBotResponse(currentInput),
        sender: 'bot',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, botResponse]);
      setIsLoading(false);
    }, 1000);
  };

  return {
    messages,
    inputValue,
    setInputValue,
    isLoading,
    messagesEndRef,
    handleSendMessage,
  };
};