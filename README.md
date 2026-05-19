<<<<<<< HEAD
# Robot Core Web

Vue 3 + TypeScript + Vite 기반 개발 템플릿입니다.

설치 및 실행:

```bash
npm install
npm run dev
```

타입 검사:

```bash
npm run type-check
```

레이아웃 사용법:

- 레이아웃 컴포넌트는 `src/components/Layout.vue` 입니다. 이제 키워드로 `header`, `middle`, `footer`, `menu`, `main`을 사용해 비율을 제어합니다.
- 예: `src/App.vue`에서 `layout.header`, `layout.middle`, `layout.footer`, `layout.menu`, `layout.main`을 `Layout`에 전달합니다.

기본 값 (샘플): header=1, middle=8, footer=1, menu=3, main=7

추가: `main` 내부를 상/하로 나누는 비율은 `contentTop`/`contentBottom`으로 제어할 수 있습니다. 기본값은 `contentTop=6`, `contentBottom=4`입니다.

중요: 설정 키는 프로젝트 전반에서 camelCase(`contentTop`, `contentBottom`)를 사용하도록 통일했습니다. `main_top`/`main_bottom` 같은 snake_case는 더 이상 권장되지 않으며 지원되지 않습니다. 기존 설정을 변경하려면 `src/config/layout.ts`의 키를 camelCase로 바꿔주세요.

TypeScript 기반 설정 및 composable:

- 기본 값과 타입은 `src/config/layout.ts`에 정의되어 있습니다 (`defaultLayout`, `LayoutRatios`).
- 런타임에서 값을 변경하려면 `src/composables/useLayout.ts`의 `useLayout()`을 사용하세요. 예: `const { layout, setLayout } = useLayout()`.

=======
# Robot_Core_Web
순찰로봇 코어 개발을 위한 테스트 웹 페이지
>>>>>>> 2aa3ce791fe54d61f6ded041ac39b3699e3d5728
