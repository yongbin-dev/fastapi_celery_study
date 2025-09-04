import React, { useState } from 'react';
import {
  TaskApiTab,
  TaskHistoryTab,
  TaskManagementTab,
  TaskModelsTab
} from '../components';

export const TaskPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'management' | 'history' | 'model' | 'etc'>('management');

  const tabs = [
    { id: 'management' as const, label: '태스크 관리' },
    { id: 'history' as const, label: '태스크 이력' },
    { id: 'model' as const, label: '모델 테스트' },
    { id: 'etc' as const, label: '기타 테스트' }
  ];

  const renderTabContent = () => {
    switch (activeTab) {
      case 'management':
        return (
          <TaskManagementTab />
        );

      case 'history':
        return <TaskHistoryTab />;

      case 'model':
        return <TaskModelsTab />;


      case 'etc':
        return <TaskApiTab />;

      default:
        return null;
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">태스크 관리</h1>

      {/* 탭 네비게이션 */}
      <div className="border-b border-gray-200 mb-8">
        <nav className="flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors ${activeTab === tab.id
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* 탭 컨텐츠 */}
      {renderTabContent()}
    </div>
  );
};