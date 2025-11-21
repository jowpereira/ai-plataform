---
applyTo: "**/*.ts,**/*.tsx"
---

# TypeScript Coding Standards

Instruções específicas para arquivos TypeScript no AI Platform.

## 🎯 Type Safety

### Tipos Explícitos
- **SEMPRE** defina tipos para parâmetros de função
- **SEMPRE** defina tipos de retorno para funções
- **EVITE** usar `any` - prefira `unknown` se necessário
- Use `strictNullChecks` e `noImplicitAny`

```typescript
// ✅ Bom
function processUser(user: User, options: ProcessOptions): Promise<Result> {
  // ...
}

// ❌ Evitar
function processUser(user, options) {
  // ...
}
```

### Interfaces vs Types
- Use `interface` para objetos e contratos públicos
- Use `type` para unions, intersections e tipos computados
- Prefira `interface` quando possível (melhor para extensão)

```typescript
// ✅ Bom
interface User {
  id: string;
  name: string;
  email: string;
}

type Status = 'pending' | 'approved' | 'rejected';
type Result<T> = Success<T> | Error;

// ❌ Evitar misturar sem razão
type User = {
  id: string;
  // ... quando interface seria melhor
};
```

## 🔧 Padrões de Código

### Async/Await
- **SEMPRE** use async/await ao invés de Promises.then()
- **SEMPRE** trate erros com try/catch
- **EVITE** callback hell

```typescript
// ✅ Bom
async function fetchUserData(userId: string): Promise<UserData> {
  try {
    const user = await userService.getUser(userId);
    const posts = await postService.getUserPosts(userId);
    return { user, posts };
  } catch (error) {
    logger.error('Failed to fetch user data', { userId, error });
    throw new UserDataError('Unable to fetch user data', { cause: error });
  }
}

// ❌ Evitar
function fetchUserData(userId: string): Promise<UserData> {
  return userService.getUser(userId)
    .then(user => postService.getUserPosts(userId)
      .then(posts => ({ user, posts })))
    .catch(error => {
      logger.error('Failed', error);
      throw error;
    });
}
```

### Destructuring
- Use destructuring para objetos e arrays
- Use rest operator para coletar propriedades restantes
- Evite destructuring profundo (max 2 níveis)

```typescript
// ✅ Bom
const { id, name, email } = user;
const [first, second, ...rest] = items;
const { user: { id, name } } = response; // OK - 2 níveis

// ❌ Evitar
const id = user.id;
const name = user.name;
const { data: { user: { profile: { name } } } } = response; // Muito profundo
```

### Optional Chaining e Nullish Coalescing
- Use `?.` para acessar propriedades opcionais
- Use `??` para valores padrão (não `||`)

```typescript
// ✅ Bom
const userName = user?.profile?.name ?? 'Anonymous';
const count = options?.limit ?? 10;

// ❌ Evitar
const userName = user && user.profile && user.profile.name || 'Anonymous';
const count = options.limit || 10; // Problema se limit = 0
```

## 🏗️ Arquitetura

### Imports
- Use imports absolutos quando possível
- Agrupe imports: externos, internos, tipos
- Ordene alfabeticamente dentro de cada grupo

```typescript
// ✅ Bom
import { Router } from 'express';
import { z } from 'zod';

import { UserService } from '@/services/user-service';
import { logger } from '@/utils/logger';

import type { User, UserCreateDTO } from '@/types/user';
```

### Exports
- Use named exports, evite default exports
- Exporte tipos e interfaces relevantes
- Um arquivo = uma responsabilidade principal

```typescript
// ✅ Bom - user-service.ts
export class UserService {
  // ...
}

export type { User, UserCreateDTO };

// ❌ Evitar
export default class UserService {
  // ...
}
```

### Error Handling
- Crie classes de erro customizadas
- Use Error.cause para encadear erros
- Inclua contexto útil nos erros

```typescript
// ✅ Bom
export class UserNotFoundError extends Error {
  constructor(
    message: string,
    public readonly userId: string,
    options?: ErrorOptions
  ) {
    super(message, options);
    this.name = 'UserNotFoundError';
  }
}

async function getUser(userId: string): Promise<User> {
  try {
    return await db.users.findById(userId);
  } catch (error) {
    throw new UserNotFoundError(
      `User with ID ${userId} not found`,
      userId,
      { cause: error }
    );
  }
}
```

## 📝 Documentação

### JSDoc
- Documente todas as funções e métodos públicos
- Inclua exemplos quando apropriado
- Use tags apropriadas: @param, @returns, @throws, @example

```typescript
/**
 * Retrieves user data by ID with optional relations.
 *
 * @param userId - The unique identifier of the user
 * @param options - Optional fetch options
 * @param options.includeProfile - Whether to include user profile
 * @param options.includePosts - Whether to include user posts
 * @returns Promise resolving to the user with requested relations
 * @throws {UserNotFoundError} When user doesn't exist
 * @throws {DatabaseError} When database query fails
 *
 * @example
 * ```typescript
 * const user = await getUserById('123', { includeProfile: true });
 * console.log(user.profile.bio);
 * ```
 */
async function getUserById(
  userId: string,
  options?: {
    includeProfile?: boolean;
    includePosts?: boolean;
  }
): Promise<User> {
  // Implementation
}
```

## 🎨 Estilo

### Formatação
- Use Prettier com configuração do projeto
- 2 espaços para indentação
- Ponto-e-vírgula sempre
- Single quotes para strings
- Trailing commas em multi-linha

### Organização de Código
```typescript
// Ordem dentro de uma classe:
class UserService {
  // 1. Propriedades estáticas
  private static instance: UserService;

  // 2. Propriedades de instância
  private readonly db: Database;
  private cache: Cache;

  // 3. Constructor
  constructor(db: Database, cache: Cache) {
    this.db = db;
    this.cache = cache;
  }

  // 4. Métodos estáticos
  static getInstance(): UserService {
    // ...
  }

  // 5. Métodos públicos
  async getUser(id: string): Promise<User> {
    // ...
  }

  // 6. Métodos privados
  private validateUser(user: User): boolean {
    // ...
  }
}
```

## ⚡ Performance

### Evite Operações Custosas
- Não use loops em operações de array quando desnecessário
- Cache resultados de operações pesadas
- Use lazy loading quando apropriado

```typescript
// ✅ Bom
const userIds = users.map(u => u.id);
const activeUsers = users.filter(u => u.isActive);

// ❌ Evitar
const userIds: string[] = [];
for (const user of users) {
  userIds.push(user.id);
}
```

### Memoization
- Use useMemo e useCallback apropriadamente (React)
- Implemente cache para operações repetitivas

---

**Nota**: Estas instruções complementam as instruções gerais do repositório.
