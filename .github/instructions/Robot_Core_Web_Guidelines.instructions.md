---
description: Vue + TypeScript 기반 프로젝트에서 일관된 구조와 유지보수성을 유지하기 위한 코딩 지침. Copilot이 코드 생성, 수정, 리뷰 시 반드시 따라야 함.
applyTo: "**/*.vue, **/*.ts, **/*.css, **/*.html"
---

# Project Context

이 프로젝트는 Vue (Composition API) + TypeScript 기반의 웹 애플리케이션이다.  
코드는 유지보수성과 확장성을 최우선으로 고려하여 작성되어야 한다.

---

# Core Principles

## 1. 역할 분리 (Separation of Concerns)

각 기술 스택은 명확한 역할을 가진다:

- **Vue (Composition API)**: 상태 관리, 로직 처리
- **TypeScript**: 타입 정의 및 데이터 구조 명확화
- **HTML (Template)**: 구조 표현 (UI 구조만 담당)
- **CSS**: 스타일링 (레이아웃 및 디자인)

### ❗ 절대 규칙
- template에 비즈니스 로직 작성 금지
- script에 스타일 관련 코드 작성 금지
- CSS에서 로직 제어 금지

---

## 2. 코드 수정 후 정리 (Critical Rule)

코드를 수정하거나 리팩토링한 경우:

- 더 이상 사용하지 않는 변수, 함수, import는 반드시 제거할 것
- 중복 코드가 발생하면 반드시 하나로 통합할 것
- 이전 로직과 충돌하는 코드가 남지 않도록 할 것

### ❗ 금지 사항
- "혹시 필요할 수도 있음" 이유로 코드 남겨두기 금지
- 사용되지 않는 state, props 유지 금지

---

## 3. TypeScript 사용 규칙

- 모든 데이터는 명시적인 타입을 가져야 한다
- `any` 사용 금지 (불가피한 경우 이유 명시)
- interface 또는 type을 적극 활용할 것

### 예시

```ts
interface User {
  id: number
  name: string
}