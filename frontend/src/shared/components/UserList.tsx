import React, { useState } from 'react';
import { useUsers, useCreateUser, useDeleteUser } from '@/hooks/user';
import type { User } from '@/types';

const UserList: React.FC = () => {
  const [newUserName, setNewUserName] = useState('');
  const [newUserEmail, setNewUserEmail] = useState('');

  // 데이터 조회
  const { data: users, isLoading, error } = useUsers();

  // 사용자 생성
  const createUser = useCreateUser();

  // 사용자 삭제
  const deleteUser = useDeleteUser();

  const handleCreateUser = async () => {
    if (!newUserName || !newUserEmail) return;

    try {
      await createUser.mutateAsync({
        name: newUserName,
        email: newUserEmail,
      });
      setNewUserName('');
      setNewUserEmail('');
    } catch (error) {
      console.error('사용자 생성 실패:', error);
    }
  };

  const handleDeleteUser = async (userId: string) => {
    if (!confirm('정말로 삭제하시겠습니까?')) return;

    try {
      await deleteUser.mutateAsync();
      console.log(`사용자 ${userId} 삭제 완료`);
    } catch (error) {
      console.error('사용자 삭제 실패:', error);
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-md">
        <p className="text-red-600">데이터를 불러오는데 실패했습니다.</p>
      </div>
    );
  }

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-6">사용자 관리</h2>

      {/* 새 사용자 추가 */}
      <div className="bg-white p-4 rounded-lg shadow mb-6">
        <h3 className="text-lg font-semibold mb-4">새 사용자 추가</h3>
        <div className="flex space-x-4">
          <input
            type="text"
            placeholder="이름"
            value={newUserName}
            onChange={(e) => setNewUserName(e.target.value)}
            className="flex-1 border border-gray-300 rounded px-3 py-2"
          />
          <input
            type="email"
            placeholder="이메일"
            value={newUserEmail}
            onChange={(e) => setNewUserEmail(e.target.value)}
            className="flex-1 border border-gray-300 rounded px-3 py-2"
          />
          <button
            onClick={handleCreateUser}
            disabled={createUser.isPending}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {createUser.isPending ? '생성 중...' : '추가'}
          </button>
        </div>
      </div>

      {/* 사용자 목록 */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b">
          <h3 className="text-lg font-semibold">사용자 목록</h3>
        </div>
        <div className="divide-y">
          {users?.map((user: User) => (
            <div key={user.id} className="px-6 py-4 flex justify-between items-center">
              <div>
                <h4 className="font-medium">{user.name}</h4>
                <p className="text-gray-600 text-sm">{user.email}</p>
              </div>
              <button
                onClick={() => handleDeleteUser(user.id)}
                disabled={deleteUser.isPending}
                className="text-red-600 hover:text-red-700 px-3 py-1 rounded text-sm disabled:opacity-50"
              >
                삭제
              </button>
            </div>
          ))}
        </div>
        {users?.length === 0 && (
          <div className="px-6 py-8 text-center text-gray-500">
            사용자가 없습니다.
          </div>
        )}
      </div>
    </div>
  );
};

export default UserList;