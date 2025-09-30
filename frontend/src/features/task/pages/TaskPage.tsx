import React, { useEffect, useState } from 'react';
import {
  TaskHistoryTab,
  TaskManagementTab,
  TaskModelsTab
} from '../components';

type TabType = 'management' | 'history' | 'model' | 'etc';

export const TaskPage: React.FC = () => {
  // URL 쿼리 파라미터에서 탭 상태를 가져오는 함수
  const getTabFromUrl = (): TabType => {
    const urlParams = new URLSearchParams(window.location.search);
    const tab = urlParams.get('tab');
    const validTabs: TabType[] = ['management', 'history', 'model', 'etc'];
    return (tab && validTabs.includes(tab as TabType)) ? tab as TabType : 'management';
  };

  const [activeTab, setActiveTab] = useState<TabType>(getTabFromUrl);

  // URL 쿼리 파라미터 업데이트 함수
  const updateUrlTab = (tabId: TabType) => {
    const url = new URL(window.location.href);
    url.searchParams.set('tab', tabId);
    window.history.pushState({}, '', url.toString());
  };

  // 탭 변경 시 URL 업데이트
  const handleTabChange = (tabId: TabType) => {
    setActiveTab(tabId);
    updateUrlTab(tabId);
  };

  // 브라우저 뒤로가기/앞으로가기 처리
  useEffect(() => {
    const handlePopState = () => {
      setActiveTab(getTabFromUrl());
    };

    window.addEventListener('popstate', handlePopState);
    return () => {
      window.removeEventListener('popstate', handlePopState);
    };
  }, []);

  const tabs = [
    { id: 'management' as const, label: '태스크 관리' },
    { id: 'history' as const, label: '태스크 이력' },
    { id: 'model' as const, label: '모델 테스트' },
    { id: 'etc' as const, label: '기타 테스트' }
  ];

  const renderTabContent = () => {
    switch (activeTab) {
      case 'management':
        return <TaskManagementTab />
      case 'history':
        return <TaskHistoryTab />;
      case 'model':
        return <TaskModelsTab />;
      case 'etc':
        return <></>
      // return <TaskApiTab />;
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
              onClick={() => handleTabChange(tab.id)}
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