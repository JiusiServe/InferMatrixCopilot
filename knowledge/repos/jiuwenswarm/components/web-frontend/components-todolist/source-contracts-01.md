---
title: "components-todolist 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# components-todolist 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/TodoList/TodoItem.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a66dfb5d6088b1bd9f3fad8629cd221ba18bdb790ce1bdfe65d49c841545b300 -->
**`jiuwenswarm/channels/web/frontend/src/components/TodoList/TodoItem.tsx`**

- 源码声明的类型、组件或调用边界：`TodoItemProps`, `TodoItem`, `getStatusIcon`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { TodoItem as TodoItemType } from '../../types';`；`import clsx from 'clsx';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/TodoList/TodoItem.tsx#L1-L78)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/TodoList/index.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1398a32b57b7bdd9d03e9b9a3cc3384b73718b152dac367a32841d30505aad56 -->
**`jiuwenswarm/channels/web/frontend/src/components/TodoList/index.tsx`**

- 源码声明的类型、组件或调用边界：`TodoList`, `activeSessionId`, `todos`, `inProgress`, `pending`, `completed`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useTranslation } from 'react-i18next';`；`import { useChatStore, useTodoStore } from '../../stores';`；`import { TodoItem } from './TodoItem';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/TodoList/index.tsx#L1-L87)。
<!-- /kb:file -->
