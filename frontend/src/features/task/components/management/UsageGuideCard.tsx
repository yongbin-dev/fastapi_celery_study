import React from 'react';

export const UsageGuideCard: React.FC = () => {
  return (
    <div className="bg-gradient-to-r from-yellow-50 to-amber-50 border-l-4 border-yellow-400 p-6 rounded-lg shadow-sm">
      <div className="flex items-start space-x-3">
        <svg className="h-6 w-6 text-yellow-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
        </svg>
        <div className="flex-1">
          <h4 className="font-semibold text-yellow-900 mb-3 text-lg">사용 방법</h4>
          <ol className="space-y-3">
            <li className="flex items-start space-x-3">
              <span className="flex items-center justify-center w-6 h-6 rounded-full bg-yellow-200 text-yellow-800 text-xs font-bold flex-shrink-0 mt-0.5">1</span>
              <p className="text-sm text-yellow-800">PDF 파일을 선택하고 <strong>"PDF 업로드 및 파이프라인 시작"</strong> 버튼을 클릭하세요.</p>
            </li>
            <li className="flex items-start space-x-3">
              <span className="flex items-center justify-center w-6 h-6 rounded-full bg-yellow-200 text-yellow-800 text-xs font-bold flex-shrink-0 mt-0.5">2</span>
              <p className="text-sm text-yellow-800">필요시 <strong>"파이프라인 취소"</strong> 버튼으로 실행을 중단할 수 있습니다.</p>
            </li>
          </ol>
          <div className="mt-4 pt-4 border-t border-yellow-200">
            <p className="text-xs text-yellow-700 flex items-center space-x-2">
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>각 섹션의 "API 호출 예시 보기"를 펼쳐서 curl 명령어로도 직접 API를 호출할 수 있습니다.</span>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
