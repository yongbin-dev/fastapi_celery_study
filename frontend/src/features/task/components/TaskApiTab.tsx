import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/shared/utils/api';

interface UserCreateRequest {
  email: string;
  username: string;
  full_name?: string;
  bio?: string;
  is_active: boolean;
  is_superuser: boolean;
}

interface UserCreateResponse {
  message: string;
  user_id?: string;
  user?: any;
}

interface User {
  id: string;
  email: string;
  username: string;
  full_name?: string;
  bio?: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
}

interface UsersListResponse {
  users: User[];
  total: number;
}

interface ApiResponse {
  success: boolean;
  data?: UserCreateResponse;
  error?: string;
  timestamp: string;
}

export const TaskApiTab: React.FC = () => {
  const queryClient = useQueryClient();
  const [formData, setFormData] = useState<UserCreateRequest>({
    email: '',
    username: '',
    full_name: '',
    bio: '',
    is_active: true,
    is_superuser: false,
  });

  const [response, setResponse] = useState<ApiResponse | null>(null);

  // 사용자 목록 조회
  const {
    data: usersData,
    isLoading: usersLoading,
    error: usersError,
    refetch: refetchUsers
  } = useQuery({
    queryKey: ['users'],
    queryFn: async (): Promise<UsersListResponse> => {
      const result = await api.get<UsersListResponse>('/api/v1/users');
      return result.data;
    },
    refetchInterval: 10000, // 10초마다 자동 새로고침
  });

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? (e.target as HTMLInputElement).checked : value
    }));
  };

  const createUserMutation = useMutation({
    mutationFn: async (data: UserCreateRequest): Promise<UserCreateResponse> => {
      const result = await api.post<UserCreateResponse>('/api/v1/users', data);
      return result.data;
    },
    onSuccess: (data) => {
      console.log('사용자 생성 성공:', data);
      setResponse({
        success: true,
        data,
        timestamp: new Date().toISOString(),
      });
      // 사용자 목록 새로고침
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
    onError: (error: any) => {
      console.error('사용자 생성 실패:', error);
      setResponse({
        success: false,
        error: error.response?.data?.message,
        timestamp: new Date().toISOString(),
      });
    },
  });

  const createUser = () => {
    createUserMutation.mutate(formData);
  };

  const clearForm = () => {
    setFormData({
      email: '',
      username: '',
      full_name: '',
      bio: '',
      is_active: true,
      is_superuser: false,
    });
    setResponse(null);
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* 폼 영역 */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">사용자 생성 API 테스트</h2>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                이메일 *
              </label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="user@example.com"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                사용자명 *
              </label>
              <input
                type="text"
                name="username"
                value={formData.username}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="username"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                전체 이름
              </label>
              <input
                type="text"
                name="full_name"
                value={formData.full_name}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="홍길동"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                소개
              </label>
              <textarea
                name="bio"
                value={formData.bio}
                onChange={handleInputChange}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="자기소개를 입력하세요"
              />
            </div>

            <div className="flex gap-4">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  name="is_active"
                  checked={formData.is_active}
                  onChange={handleInputChange}
                  className="mr-2"
                />
                <span className="text-sm text-gray-700">활성 사용자</span>
              </label>

              <label className="flex items-center">
                <input
                  type="checkbox"
                  name="is_superuser"
                  checked={formData.is_superuser}
                  onChange={handleInputChange}
                  className="mr-2"
                />
                <span className="text-sm text-gray-700">관리자 권한</span>
              </label>
            </div>

            <div className="flex gap-3 pt-4">
              <button
                onClick={createUser}
                disabled={createUserMutation.isPending || !formData.email || !formData.username}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                {createUserMutation.isPending ? '생성 중...' : '사용자 생성'}
              </button>

              <button
                onClick={clearForm}
                className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
              >
                폼 초기화
              </button>
            </div>
          </div>
        </div>

        {/* 결과 영역 */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">API 응답</h2>

          {response ? (
            <div className="space-y-4">
              <div className={`p-3 rounded-md ${response.success
                ? 'bg-green-100 border border-green-300'
                : 'bg-red-100 border border-red-300'
                }`}>
                <div className="flex items-center mb-2">
                  <span className={`font-medium ${response.success ? 'text-green-800' : 'text-red-800'
                    }`}>
                    {response.success ? '✅ 성공' : '❌ 실패'}
                  </span>
                  <span className="ml-auto text-sm text-gray-500">
                    {new Date(response.timestamp).toLocaleString()}
                  </span>
                </div>
              </div>

              {response.success && response.data && (
                <div>
                  <h3 className="font-medium text-gray-700 mb-2">응답 데이터:</h3>
                  <pre className="bg-gray-100 p-3 rounded-md text-sm overflow-x-auto">
                    {JSON.stringify(response.data, null, 2)}
                  </pre>
                </div>
              )}

              {!response.success && response.error && (
                <div>
                  <h3 className="font-medium text-red-700 mb-2">오류 메시지:</h3>
                  <div className="bg-red-50 p-3 rounded-md text-sm text-red-800">
                    {response.error}
                  </div>
                </div>
              )}

              <div>
                <h3 className="font-medium text-gray-700 mb-2">요청 데이터:</h3>
                <pre className="bg-gray-100 p-3 rounded-md text-sm overflow-x-auto">
                  {JSON.stringify(formData, null, 2)}
                </pre>
              </div>
            </div>
          ) : (
            <div className="text-gray-500 text-center py-8">
              API를 호출하면 결과가 여기에 표시됩니다
            </div>
          )}
        </div>

        {/* 사용자 목록 영역 */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold">사용자 목록</h2>
            <button
              onClick={() => refetchUsers()}
              disabled={usersLoading}
              className="px-3 py-1 bg-blue-500 text-white text-sm rounded-md hover:bg-blue-600 disabled:bg-gray-400"
            >
              {usersLoading ? '로딩...' : '새로고침'}
            </button>
          </div>

          {usersError ? (
            <div className="text-red-500 text-center py-8">
              사용자 목록을 불러오는데 실패했습니다
            </div>
          ) : usersLoading ? (
            <div className="text-gray-500 text-center py-8">
              사용자 목록을 불러오는 중...
            </div>
          ) : usersData?.users && usersData.users.length > 0 ? (
            <div className="space-y-3 max-h-96 overflow-y-auto">
              <div className="text-sm text-gray-600 mb-2">
                총 {usersData.total}명의 사용자
              </div>
              {usersData.users.map((user) => (
                <div
                  key={user.id}
                  className="border border-gray-200 rounded-lg p-3 hover:bg-gray-50"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h3 className="font-medium text-gray-900">
                          {user.full_name || user.username}
                        </h3>
                        <div className="flex gap-1">
                          {user.is_active ? (
                            <span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded">
                              활성
                            </span>
                          ) : (
                            <span className="px-2 py-1 text-xs bg-gray-100 text-gray-800 rounded">
                              비활성
                            </span>
                          )}
                          {user.is_superuser && (
                            <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">
                              관리자
                            </span>
                          )}
                        </div>
                      </div>
                      <p className="text-sm text-gray-600 mt-1">
                        @{user.username}
                      </p>
                      <p className="text-sm text-gray-600">
                        {user.email}
                      </p>
                      {user.bio && (
                        <p className="text-sm text-gray-500 mt-1 line-clamp-2">
                          {user.bio}
                        </p>
                      )}
                      <p className="text-xs text-gray-400 mt-2">
                        가입일: {new Date(user.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-gray-500 text-center py-8">
              등록된 사용자가 없습니다
            </div>
          )}
        </div>
      </div>
    </div>
  );
};