# 📚 프로젝트 문서

React Feature-Based Architecture 프로젝트의 종합 문서입니다.

## 📖 문서 구성

### 🏗️ [아키텍처](./architecture/)
프로젝트의 전체적인 구조와 설계 철학을 설명합니다.

- [📋 아키텍처 개요](./architecture/README.md) - Feature-Based Architecture 패턴 소개

### 📋 [가이드](./guides/)
개발 시 참고할 수 있는 실무 가이드들입니다.

- [📁 폴더 구조 가이드](./guides/folder-structure.md) - 새로운 기능 추가 방법
- [📦 Import/Export 패턴](./guides/import-export-patterns.md) - 모듈 관리 방법
- [🎯 개발 가이드라인](./guides/development-guidelines.md) - 코딩 표준과 베스트 프랙티스

### 💡 [예시](./examples/)
실제 구현 예시와 코드 샘플들입니다.

- [🔧 기능 구현 예시](./examples/feature-example.md) - Todo 기능 구현 전체 과정

## 🚀 빠른 시작

### 1. 새로운 기능 만들기
```bash
# 1. 폴더 생성
mkdir -p src/features/my-feature/{components,hooks,pages,types}

# 2. 기본 파일 생성
touch src/features/my-feature/{index.ts,components/index.ts,hooks/index.ts,pages/index.ts,types/index.ts}
```

### 2. 기본 구조 설정
```typescript
// src/features/my-feature/index.ts
export * from './components';
export * from './hooks';
export * from './pages';
export * from './types';
```

### 3. 전역 Export에 추가
```typescript
// src/features/index.ts
export * from './my-feature';
```

자세한 내용은 [폴더 구조 가이드](./guides/folder-structure.md)를 참고하세요.

## 📋 체크리스트

### ✅ 새 기능 개발 전
- [ ] [아키텍처 문서](./architecture/README.md) 읽기
- [ ] [폴더 구조 가이드](./guides/folder-structure.md) 확인
- [ ] [개발 가이드라인](./guides/development-guidelines.md) 숙지

### ✅ 개발 중
- [ ] TypeScript 타입 정의
- [ ] 적절한 Export/Import 패턴 사용
- [ ] 컴포넌트 단위 분리
- [ ] 에러 처리 구현

### ✅ 개발 완료 후
- [ ] 코드 리뷰 체크리스트 확인
- [ ] 테스트 코드 작성
- [ ] 문서 업데이트

## 🔗 관련 링크

### 외부 문서
- [React 공식 문서](https://react.dev/)
- [TypeScript 공식 문서](https://www.typescriptlang.org/)
- [Tailwind CSS 문서](https://tailwindcss.com/)
- [React Query 문서](https://tanstack.com/query)

### 내부 리소스
- [프로젝트 README](../README.md)
- [환경 설정](./.env.example)
- [패키지 정보](../package.json)

## 📝 문서 기여

문서 개선이나 오류 발견 시:

1. 해당 문서 파일 수정
2. 명확하고 실용적인 내용으로 작성
3. 예시 코드 포함
4. 팀 내 리뷰 후 반영

---

💡 **팁**: 개발하면서 자주 참고하는 문서는 즐겨찾기에 추가해두세요!